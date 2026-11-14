import math

import torch
import torch.nn.functional as F
from torch import nn


class SparseAutoencoder(nn.Module):
    """L1 sparse autoencoder with a tied pre-encoder/post-decoder bias and unit-norm decoder columns.

    Matches the `sparse_autoencoder` 1.10 library used by M-CBM, so its hyperparameters carry over.
    Each hidden unit is an "SAE neuron": a candidate concept with an activation and a decoder direction.
    """

    def __init__(self, input_dim, n_neurons):
        super().__init__()
        self.input_dim = input_dim
        self.n_neurons = n_neurons
        self.tied_bias = nn.Parameter(torch.zeros(input_dim))
        self.encoder = nn.Linear(input_dim, n_neurons)
        self.decoder_weight = nn.Parameter(torch.empty(input_dim, n_neurons))
        self.reset_parameters()
        self.decoder_weight.register_hook(self._remove_parallel_gradient)

    def reset_parameters(self):
        nn.init.kaiming_uniform_(self.encoder.weight, nonlinearity="relu")
        bound = 1 / math.sqrt(self.input_dim)
        nn.init.uniform_(self.encoder.bias, -bound, bound)
        nn.init.normal_(self.decoder_weight)
        self.normalize_decoder()

    @torch.no_grad()
    def normalize_decoder(self):
        """Must be called after every optimizer step: Adam's momentum moves columns off the unit sphere."""
        F.normalize(self.decoder_weight, dim=0, out=self.decoder_weight)

    def _remove_parallel_gradient(self, grad):
        unit = self.decoder_weight / self.decoder_weight.norm(dim=0, keepdim=True)
        return grad - unit * (grad * unit).sum(dim=0, keepdim=True)

    def encode(self, x):
        return F.relu(self.encoder(x - self.tied_bias))

    def decode(self, activations):
        return activations @ self.decoder_weight.T + self.tied_bias

    def forward(self, x):
        activations = self.encode(x)
        return activations, self.decode(activations)

    def decoder_direction(self, neuron):
        return self.decoder_weight[:, neuron]


def sae_loss(x, activations, reconstructed, l1_coefficient):
    reconstruction = (reconstructed - x).pow(2).mean(dim=-1).mean()
    l1_penalty = l1_coefficient * activations.abs().sum(dim=-1).mean()
    return {
        "total_loss": reconstruction + l1_penalty,
        "reconstruction_loss": reconstruction,
        "l1_penalty": l1_penalty,
        "avg_l0": (activations > 0).float().sum(dim=-1).mean(),
    }


def save_sae(path, sae, extra=None):
    torch.save({"state_dict": sae.state_dict(), "input_dim": sae.input_dim, "n_neurons": sae.n_neurons, **(extra or {})}, path)


def load_sae(path, device="cpu"):
    state = torch.load(path, map_location="cpu")
    sae = SparseAutoencoder(state["input_dim"], state["n_neurons"])
    sae.load_state_dict(state["state_dict"])
    return sae.to(device).eval()

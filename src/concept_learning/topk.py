import math
import textwrap
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn.functional as F

from concept_learning.data import CUBDataset, cub_root, display_transform, eval_transform
from concept_learning.models import load_backbone
from concept_learning.sae import load_sae
from concept_learning.utils import OUTPUTS, load_json, resolve_device

IMAGES_PER_ROW = 5


def run_backbone(run_dir):
    """Backbone name from a `<prefix>_<backbone>_<YYYYmmdd>_<HHMMSS>` run directory."""
    return Path(run_dir).name.rsplit("_", 2)[0].split("_", 1)[1]


def latest_run(kind, backbone=None):
    runs = sorted(
        (p for p in (OUTPUTS / kind).iterdir() if p.is_dir() and (backbone is None or run_backbone(p) == backbone)),
        key=lambda p: p.stat().st_mtime,
    )
    if not runs:
        raise FileNotFoundError(f"No runs in {OUTPUTS / kind}" + (f" for backbone {backbone}" if backbone else ""))
    return runs[-1]


class NeuronExplorer:
    """Top-K training images and concept heatmaps for the neurons of a trained SAE."""

    def __init__(self, sae_dir, device=None):
        self.sae_dir = Path(sae_dir)
        self.device = resolve_device(device)
        self.metrics = load_json(self.sae_dir / "metrics.json")
        activation_dir = Path(load_json(self.sae_dir / "run_info.json")["activation_dir"])
        self.activation_info = load_json(activation_dir / "run_info.json")

        self.sae = load_sae(self.sae_dir / "sae.pt", self.device)
        self.backbone = load_backbone(self.activation_info["backbone"], self.activation_info["checkpoint"], self.device)
        self.kept_indices = torch.load(self.sae_dir / "kept_indices.pt").tolist()
        self.neuron_counts = torch.load(self.sae_dir / "neuron_active_counts.pt")

        train = torch.load(activation_dir / "activations_train.pt")
        self.labels = train["labels"]
        self.image_names = train["image_names"]
        with torch.no_grad():
            self.activations = self.sae.encode(train["features"].to(self.device)).cpu()

        self.dataset = CUBDataset(cub_root(), train=True)
        self.class_names = self.dataset.class_names
        self._preprocess = eval_transform()
        self._display = display_transform()

    @property
    def n_images(self):
        return len(self.image_names)

    def neurons_by_frequency(self):
        return sorted(self.kept_indices, key=lambda neuron: -int(self.neuron_counts[neuron]))

    def top_images(self, neuron, k):
        values, indices = self.activations[:, neuron].topk(k)
        positive = values > 0
        return indices[positive].tolist(), values[positive].tolist()

    @torch.no_grad()
    def concept_maps(self, images, neuron):
        """Per-location projection of the backbone's last feature map onto the SAE neuron's decoder direction."""
        batch = torch.stack([self._preprocess(image) for image in images]).to(self.device)
        fmaps = self.backbone.feature_map(batch)
        direction = self.sae.decoder_direction(neuron).reshape(1, -1, 1, 1)
        return F.relu((fmaps * direction).sum(dim=1)).cpu()

    def heatmap_overlays(self, images, neuron):
        maps = self.concept_maps(images, neuron)
        threshold = 0.5 * maps.amax(dim=(1, 2)).mean()
        overlays = []
        for image, concept_map in zip(images, maps):
            shown = np.asarray(self._display(image), dtype=np.float32) / 255
            resized = F.interpolate(concept_map[None, None], size=shown.shape[:2], mode="bilinear")[0, 0].numpy()
            mask = np.where(resized >= threshold.item(), 1.0, 0.2)[..., None]
            overlays.append(0.3 * shown + 0.7 * shown * mask)
        return overlays

    def class_counts(self, neuron, top_n):
        indices, _ = self.top_images(neuron, top_n)
        return Counter(self.class_names[int(self.labels[i])] for i in indices)

    def plot_neuron(self, neuron, k=10, hist_top=50, hist_classes=10, heatmap=True):
        indices, values = self.top_images(neuron, k)
        if not indices:
            raise ValueError(f"SAE neuron {neuron} never fires on the training split.")
        images = [self.dataset.load_image_by_name(self.image_names[i]) for i in indices]
        shown = self.heatmap_overlays(images, neuron) if heatmap else [self._display(image) for image in images]

        image_rows = math.ceil(len(images) / IMAGES_PER_ROW)
        fig = plt.figure(figsize=(3 * IMAGES_PER_ROW, 3.4 * image_rows + 3))
        grid = fig.add_gridspec(image_rows + 1, IMAGES_PER_ROW, height_ratios=[3.4] * image_rows + [2.6])
        for position, (image, index, value) in enumerate(zip(shown, indices, values)):
            axis = fig.add_subplot(grid[position // IMAGES_PER_ROW, position % IMAGES_PER_ROW])
            axis.imshow(image)
            axis.set_title(f"{textwrap.fill(self.class_names[int(self.labels[index])], 22)}\nact = {value:.3f}", fontsize=9)
            axis.axis("off")

        counts = self.class_counts(neuron, hist_top).most_common(hist_classes)
        hist_axis = fig.add_subplot(grid[image_rows, :])
        hist_axis.barh([name for name, _ in reversed(counts)], [count for _, count in reversed(counts)])
        n_top = min(hist_top, int(self.neuron_counts[neuron]))
        hist_axis.set_title(f"Most common classes among the top {n_top} activating images", fontsize=10)
        hist_axis.set_xlabel("Images")

        fires = int(self.neuron_counts[neuron])
        fig.suptitle(f"SAE neuron {neuron}: fires on {fires} / {self.n_images} training images ({fires / self.n_images:.1%})", fontsize=13)
        fig.tight_layout()
        return fig

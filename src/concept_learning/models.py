from pathlib import Path

import torch
from torch import nn
from torchvision import models

BACKBONES = ("resnet18_cub", "resnet18_cub_pytorchcv")


class Backbone(nn.Module):
    """A classifier split into a spatial feature extractor and a linear head on its average-pooled output."""

    def __init__(self, feature_map, head):
        super().__init__()
        self.feature_map = feature_map
        self.head = head

    def embed(self, x):
        return self.feature_map(x).mean(dim=(2, 3))

    def forward(self, x):
        return self.head(self.embed(x))


def wrap_torchvision_resnet(resnet):
    feature_map = nn.Sequential(
        resnet.conv1, resnet.bn1, resnet.relu, resnet.maxpool,
        resnet.layer1, resnet.layer2, resnet.layer3, resnet.layer4,
    )
    return Backbone(feature_map, resnet.fc)


def resnet18_backbone(num_classes, imagenet_init):
    weights = models.ResNet18_Weights.IMAGENET1K_V1 if imagenet_init else None
    resnet = models.resnet18(weights=weights)
    resnet.fc = nn.Linear(resnet.fc.in_features, num_classes)
    return wrap_torchvision_resnet(resnet)


def pytorchcv_backbone():
    from pytorchcv.model_provider import get_model

    model = get_model("resnet18_cub", pretrained=True)
    feature_map = nn.Sequential(*[m for name, m in model.features.named_children() if name != "final_pool"])
    return Backbone(feature_map, model.output)


def save_classifier(path, backbone, num_classes, extra=None):
    torch.save({"state_dict": backbone.state_dict(), "num_classes": num_classes, **(extra or {})}, path)


def load_backbone(name, checkpoint=None, device="cpu"):
    if name == "resnet18_cub":
        if checkpoint is None:
            raise ValueError("Backbone 'resnet18_cub' needs a checkpoint from train_classifier.")
        state = torch.load(Path(checkpoint), map_location="cpu")
        backbone = resnet18_backbone(state["num_classes"], imagenet_init=False)
        backbone.load_state_dict(state["state_dict"])
    elif name == "resnet18_cub_pytorchcv":
        backbone = pytorchcv_backbone()
    else:
        raise ValueError(f"Unknown backbone {name!r}, expected one of {BACKBONES}.")
    return backbone.to(device).eval()

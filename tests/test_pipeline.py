import json

import matplotlib

matplotlib.use("Agg")
import numpy as np
import pytest
import torch
from PIL import Image
from torchvision import models

from concept_learning import data
from concept_learning.models import wrap_torchvision_resnet
from concept_learning.sae import SparseAutoencoder, sae_loss
from concept_learning.scripts import extract_activations, train_classifier, train_sae
from concept_learning.topk import NeuronExplorer

N_CLASSES = 4
TRAIN_PER_CLASS = 6
TEST_PER_CLASS = 2


@pytest.fixture
def fake_cub(tmp_path, monkeypatch):
    root = tmp_path / "datasets" / "CUB_200_2011"
    rng = np.random.default_rng(0)
    images, labels, split, classes = [], [], [], []
    img_id = 1
    for class_id in range(1, N_CLASSES + 1):
        class_dir = f"{class_id:03d}.Bird_{class_id}"
        classes.append(f"{class_id} {class_dir}")
        (root / "images" / class_dir).mkdir(parents=True)
        for i in range(TRAIN_PER_CLASS + TEST_PER_CLASS):
            name = f"{class_dir}/img_{i}.jpg"
            pixels = rng.integers(0, 255, (48, 64, 3), dtype=np.uint8)
            Image.fromarray(pixels).save(root / "images" / name)
            images.append(f"{img_id} {name}")
            labels.append(f"{img_id} {class_id}")
            split.append(f"{img_id} {int(i < TRAIN_PER_CLASS)}")
            img_id += 1
    for filename, lines in [("images.txt", images), ("image_class_labels.txt", labels), ("train_test_split.txt", split), ("classes.txt", classes)]:
        (root / filename).write_text("\n".join(lines) + "\n")
    monkeypatch.setattr(data, "DATASET_FOLDER", root.parent)
    return root


def test_backbone_split_matches_torchvision_forward():
    resnet = models.resnet18(weights=None, num_classes=N_CLASSES).eval()
    backbone = wrap_torchvision_resnet(resnet).eval()
    x = torch.randn(2, 3, 224, 224)
    with torch.no_grad():
        torch.testing.assert_close(backbone(x), resnet(x))


def test_sae_keeps_decoder_columns_unit_norm():
    torch.manual_seed(0)
    sae = SparseAutoencoder(16, 32)
    optimizer = torch.optim.Adam(sae.parameters(), lr=1e-2)
    x = torch.randn(64, 16)
    for _ in range(5):
        loss = sae_loss(x, *sae(x), l1_coefficient=1e-3)["total_loss"]
        optimizer.zero_grad()
        loss.backward()
        unit = sae.decoder_weight / sae.decoder_weight.norm(dim=0, keepdim=True)
        assert (sae.decoder_weight.grad * unit).sum(dim=0).abs().max() < 1e-5
        optimizer.step()
        sae.normalize_decoder()
    torch.testing.assert_close(sae.decoder_weight.norm(dim=0), torch.ones(32))


def test_pipeline_end_to_end(fake_cub, tmp_path):
    config = json.loads((data.PROJECT_ROOT / "configs" / "cub.json").read_text())
    config.update(
        val_split=0.25,
        num_workers=0,
        clf_imagenet_init=False,
        clf_epochs=1,
        clf_batch_size=8,
        sae_epochs=3,
        sae_patience=2,
        sae_min_active_images=1,
    )
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config))
    common = ["--config", str(config_path), "--device", "cpu"]

    train_classifier.main([*common, "--output-dir", str(tmp_path / "clf")])
    extract_activations.main([*common, "--checkpoint", str(tmp_path / "clf" / "model.pt"), "--output-dir", str(tmp_path / "act"), "--batch-size", "8"])
    train_sae.main([*common, "--activation-dir", str(tmp_path / "act"), "--output-dir", str(tmp_path / "sae")])

    train = torch.load(tmp_path / "act" / "activations_train.pt")
    assert train["features"].shape == (N_CLASSES * TRAIN_PER_CLASS * 3 // 4, 512)
    assert len(train["image_names"]) == len(train["labels"])

    explorer = NeuronExplorer(tmp_path / "sae", device="cpu")
    neuron = explorer.neurons_by_frequency()[0]
    fig = explorer.plot_neuron(neuron, k=4, hist_top=8)
    assert len(fig.axes) == 5

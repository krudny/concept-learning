from collections import Counter
from pathlib import Path

import torch

from concept_learning.sae import load_sae
from concept_learning.utils import load_json

DETECTOR_SHARE = 0.8
DIFFUSE_CLASSES = 8


def neuron_purity(activations, labels, neuron, k):
    """Most common class among the neuron's top-k activating images, its share of them, and how many classes appear."""
    values, indices = activations[:, neuron].topk(k)
    counts = Counter(labels[indices[values > 0]].tolist())
    top_class, top_count = counts.most_common(1)[0]
    return {"neuron": neuron, "top_class": top_class, "share": top_count / counts.total(), "n_classes": len(counts)}


def within_class_variance_share(features, labels):
    """Fraction of the embeddings' variance left within classes. Near 0 means each class has collapsed onto its mean."""
    within = sum((features[labels == c] - features[labels == c].mean(0)).pow(2).sum() for c in labels.unique())
    return (within / (features - features.mean(0)).pow(2).sum()).item()


def class_purity(sae_dir, k=10, wide_k=50):
    """How class-specific the kept neurons of an SAE run are, on the training split it was trained on.

    A neuron is a class detector if one class makes up at least DETECTOR_SHARE of its top-k images,
    and diffuse if its top-k images span at least DIFFUSE_CLASSES classes.
    """
    sae_dir = Path(sae_dir)
    run_info = load_json(sae_dir / "run_info.json")
    activation_dir = Path(run_info["activation_dir"])
    train = torch.load(activation_dir / "activations_train.pt")
    features, labels = train["features"].float(), train["labels"]
    kept = torch.load(sae_dir / "kept_indices.pt").tolist()
    with torch.no_grad():
        activations = load_sae(sae_dir / "sae.pt").encode(features)

    neurons = [neuron_purity(activations, labels, neuron, k) for neuron in kept]
    wide_shares = [neuron_purity(activations, labels, neuron, wide_k)["share"] for neuron in kept]
    detectors = [row for row in neurons if row["share"] >= DETECTOR_SHARE]
    summary = {
        "backbone": load_json(activation_dir / "run_info.json")["backbone"],
        "l1_coefficient": run_info["config"]["sae_l1_coefficient"],
        "train_avg_l0": load_json(sae_dir / "metrics.json")["train_avg_l0"],
        "kept_neurons": len(kept),
        "class_detectors": len(detectors) / len(kept),
        "classes_with_detector": len({row["top_class"] for row in detectors}),
        "diffuse_neurons": sum(row["n_classes"] >= DIFFUSE_CLASSES for row in neurons) / len(kept),
        f"mean_top{k}_share": sum(row["share"] for row in neurons) / len(kept),
        f"mean_top{wide_k}_share": sum(wide_shares) / len(kept),
        "within_class_variance": within_class_variance_share(features, labels),
    }
    return summary, neurons

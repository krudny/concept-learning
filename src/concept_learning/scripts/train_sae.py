import argparse
import copy
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn.functional as F

from concept_learning.models import load_backbone
from concept_learning.sae import SparseAutoencoder, sae_loss, save_sae
from concept_learning.utils import load_config, load_json, new_run_dir, resolve_device, save_json, set_seed

MAX_POST_SELECTION_CURVE_POINTS = 100


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Train an SAE on saved backbone activations.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--activation-dir", required=True)
    parser.add_argument("--output-dir")
    parser.add_argument("--device")
    return parser.parse_args(argv)


def load_split(activation_dir, split):
    data = torch.load(Path(activation_dir) / f"activations_{split}.pt")
    return data["features"].float(), data["labels"].long()


def run_epoch(sae, features, batch_size, l1_coefficient, optimizer=None, generator=None):
    train = optimizer is not None
    sae.train(train)
    order = torch.randperm(len(features), generator=generator).to(features.device) if train else None
    totals = {"reconstruction_loss": 0.0, "l1_penalty": 0.0, "total_loss": 0.0, "avg_l0": 0.0}

    with torch.set_grad_enabled(train):
        for start in range(0, len(features), batch_size):
            batch = features[order[start:start + batch_size]] if train else features[start:start + batch_size]
            losses = sae_loss(batch, *sae(batch), l1_coefficient)
            if train:
                optimizer.zero_grad()
                losses["total_loss"].backward()
                optimizer.step()
                sae.normalize_decoder()
            for key in totals:
                totals[key] += losses[key].item() * len(batch)

    return {key: value / len(features) for key, value in totals.items()}


@torch.no_grad()
def neuron_active_counts(sae, features):
    return (sae.encode(features) > 0).sum(dim=0).cpu()


@torch.no_grad()
def recovered_metrics(sae, head, features, labels, kept_mask):
    """Fraction of the classifier's CE loss / accuracy recovered when it sees SAE reconstructions instead of embeddings.

    0 means as bad as zero-ablating the embedding, 1 means as good as the original embedding.
    """
    def ce_and_accuracy(inputs):
        logits = head(inputs)
        return F.cross_entropy(logits, labels).item(), (logits.argmax(1) == labels).float().mean().item()

    original_loss, original_acc = ce_and_accuracy(features)
    zero_loss, zero_acc = ce_and_accuracy(torch.zeros_like(features))
    recon_loss, recon_acc = ce_and_accuracy(sae.decode(sae.encode(features) * kept_mask.to(features.device)))
    recovered_loss = (zero_loss - recon_loss) / (zero_loss - original_loss + 1e-8)
    recovered_acc = (recon_acc - zero_acc) / (original_acc - zero_acc + 1e-8)
    return recovered_loss, recovered_acc


def run_pruning(sae, head, train_counts, val_features, val_labels, tolerance, min_active_images):
    """Drop rarely-firing SAE neurons at the highest activation-count threshold that keeps the recovered CE loss within tolerance."""
    total_neurons = train_counts.numel()
    baseline_loss, baseline_acc = recovered_metrics(sae, head, val_features, val_labels, torch.ones(total_neurons, dtype=torch.bool))

    min_threshold = int(min_active_images) - 1
    max_count = int(train_counts.max())
    thresholds = sorted({min_threshold} | {c for c in train_counts.unique().tolist() if min_threshold <= c < max_count})

    curve, selected, post_failure_indices = [], None, None
    for index, threshold in enumerate(thresholds):
        if post_failure_indices is not None and index not in post_failure_indices:
            continue
        kept_mask = train_counts > threshold
        if not kept_mask.any():
            continue
        recovered_loss, recovered_acc = recovered_metrics(sae, head, val_features, val_labels, kept_mask)
        loss_drop = baseline_loss - recovered_loss
        if post_failure_indices is None and loss_drop <= tolerance:
            selected = {"threshold": threshold, "kept_mask": kept_mask, "recovered_loss": recovered_loss, "recovered_accuracy": recovered_acc, "loss_drop": loss_drop}
        elif post_failure_indices is None:
            remaining = list(range(index + 1, len(thresholds)))
            if len(remaining) > MAX_POST_SELECTION_CURVE_POINTS:
                remaining = [remaining[i] for i in np.linspace(0, len(remaining) - 1, MAX_POST_SELECTION_CURVE_POINTS, dtype=int)]
            post_failure_indices = set(remaining)
        curve.append(
            {
                "threshold": threshold,
                "kept_neurons": int(kept_mask.sum()),
                "pruned_neurons": int(total_neurons - kept_mask.sum()),
                "recovered_loss": recovered_loss,
                "recovered_loss_drop": loss_drop,
                "recovered_accuracy": recovered_acc,
            }
        )

    if selected is None:
        kept_mask = train_counts > min_threshold
        recovered_loss, recovered_acc = recovered_metrics(sae, head, val_features, val_labels, kept_mask)
        selected = {"threshold": min_threshold, "kept_mask": kept_mask, "recovered_loss": recovered_loss, "recovered_accuracy": recovered_acc, "loss_drop": baseline_loss - recovered_loss}

    kept_indices = torch.nonzero(selected["kept_mask"]).squeeze(1)
    summary = {
        "total_neurons": total_neurons,
        "kept_neurons": kept_indices.numel(),
        "pruned_neurons": total_neurons - kept_indices.numel(),
        "selected_activation_count_threshold": selected["threshold"],
        "min_active_images": int(min_active_images),
        "ce_drop_tolerance": tolerance,
        "baseline_recovered_loss": baseline_loss,
        "baseline_recovered_accuracy": baseline_acc,
        "selected_recovered_loss": selected["recovered_loss"],
        "recovered_loss_drop": selected["loss_drop"],
        "selected_recovered_accuracy": selected["recovered_accuracy"],
        "recovered_accuracy_drop": baseline_acc - selected["recovered_accuracy"],
    }
    return kept_indices, curve, summary


def plot_training_curves(path, history):
    epochs = [row["epoch"] for row in history]
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for axis, metric, title in zip(axes, ["reconstruction_loss", "avg_l0"], ["Reconstruction loss (MSE)", "Average L0"]):
        axis.plot(epochs, [row[f"train_{metric}"] for row in history], label="Train")
        axis.plot(epochs, [row[f"val_{metric}"] for row in history], label="Validation")
        axis.set_xlabel("Epoch")
        axis.set_title(f"SAE {title}")
        axis.legend()
        axis.grid(True)
    plt.tight_layout()
    plt.savefig(path)
    plt.close(fig)


def plot_feature_density(path, neuron_counts, n_samples, selected_threshold):
    counts = neuron_counts.numpy()
    log_density = np.log10(np.clip(counts / n_samples, 1e-8, None))
    dead = counts == 0
    low = (counts <= selected_threshold) & ~dead
    high = counts > selected_threshold
    plt.figure(figsize=(10, 6))
    plt.hist(
        [log_density[dead], log_density[low], log_density[high]],
        bins=100,
        stacked=True,
        color=["purple", "orange", "green"],
        edgecolor="black",
        label=["Dead", "Pruned / low density", "Kept"],
    )
    plt.xlabel("log10(feature density)")
    plt.ylabel("SAE neurons")
    plt.title("SAE feature density on the training split")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()


def plot_pruning_curve(path, curve, selected_threshold):
    thresholds = [row["threshold"] for row in curve]
    series = [
        ("recovered_loss", "Recovered CE loss"),
        ("recovered_accuracy", "Recovered accuracy"),
        ("kept_neurons", "SAE neurons kept"),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    for axis, (key, title) in zip(axes, series):
        values = [row[key] for row in curve]
        axis.plot(thresholds, values, zorder=2)
        if selected_threshold in thresholds:
            axis.scatter([selected_threshold], [values[thresholds.index(selected_threshold)]], color="red", marker="*", s=120, zorder=5)
        axis.set_xlabel("Activation-count pruning threshold")
        axis.set_title(title)
        axis.grid(True)
    plt.tight_layout()
    plt.savefig(path)
    plt.close(fig)


def train(config, activation_dir, run_dir, device):
    """Train, prune and plot one SAE into an existing run_dir. Returns the metrics saved to metrics.json."""
    set_seed(config["seed"])
    activation_dir = Path(activation_dir).resolve()
    activation_info = load_json(activation_dir / "run_info.json")
    (run_dir / "plots").mkdir()

    train_features, _ = load_split(activation_dir, "train")
    val_features, val_labels = load_split(activation_dir, "val")
    train_features, val_features, val_labels = train_features.to(device), val_features.to(device), val_labels.to(device)

    input_dim = train_features.shape[1]
    n_neurons = int(input_dim * config["sae_expansion_factor"])
    sae = SparseAutoencoder(input_dim, n_neurons).to(device)
    optimizer = torch.optim.Adam(sae.parameters(), lr=config["sae_learning_rate"])
    generator = torch.Generator().manual_seed(config["seed"])
    batch_size, l1 = config["sae_batch_size"], config["sae_l1_coefficient"]

    history, best_state, best_epoch, best_val_loss, stale_epochs = [], None, 0, float("inf"), 0
    for epoch in range(1, config["sae_epochs"] + 1):
        train_metrics = run_epoch(sae, train_features, batch_size, l1, optimizer, generator)
        val_metrics = run_epoch(sae, val_features, batch_size, l1)
        history.append({"epoch": epoch, **{f"train_{k}": v for k, v in train_metrics.items()}, **{f"val_{k}": v for k, v in val_metrics.items()}})
        print(
            f"epoch {epoch}: train recon {train_metrics['reconstruction_loss']:.6f} L0 {train_metrics['avg_l0']:.2f}, "
            f"val recon {val_metrics['reconstruction_loss']:.6f} L0 {val_metrics['avg_l0']:.2f}"
        )
        if val_metrics["total_loss"] < best_val_loss:
            best_val_loss, best_epoch, stale_epochs = val_metrics["total_loss"], epoch, 0
            best_state = copy.deepcopy(sae.state_dict())
        else:
            stale_epochs += 1
            if stale_epochs >= config["sae_patience"]:
                print(f"Stopping early after {epoch} epochs.")
                break

    sae.load_state_dict(best_state)
    sae.eval()
    final_train = run_epoch(sae, train_features, batch_size, l1)
    final_val = run_epoch(sae, val_features, batch_size, l1)
    save_sae(run_dir / "sae.pt", sae, {"best_epoch": best_epoch})

    head = load_backbone(activation_info["backbone"], activation_info["checkpoint"], device).head
    neuron_counts = neuron_active_counts(sae, train_features)
    kept_indices, curve, pruning_summary = run_pruning(
        sae, head, neuron_counts, val_features, val_labels, config["sae_ce_drop_tolerance"], config["sae_min_active_images"]
    )
    torch.save(kept_indices, run_dir / "kept_indices.pt")
    torch.save(neuron_counts, run_dir / "neuron_active_counts.pt")
    with (run_dir / "pruning_curve.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(curve[0]))
        writer.writeheader()
        writer.writerows(curve)

    plot_training_curves(run_dir / "plots" / "training_curves.png", history)
    plot_feature_density(run_dir / "plots" / "feature_density.png", neuron_counts, len(train_features), pruning_summary["selected_activation_count_threshold"])
    plot_pruning_curve(run_dir / "plots" / "pruning_curve.png", curve, pruning_summary["selected_activation_count_threshold"])

    metrics = {
        "input_dim": input_dim,
        "n_neurons": n_neurons,
        "epochs_trained": len(history),
        "best_epoch": best_epoch,
        "best_val_total_loss": best_val_loss,
        "train_reconstruction_loss": final_train["reconstruction_loss"],
        "val_reconstruction_loss": final_val["reconstruction_loss"],
        "train_avg_l0": final_train["avg_l0"],
        "val_avg_l0": final_val["avg_l0"],
        "pruning": pruning_summary,
    }
    save_json(run_dir / "history.json", history)
    save_json(run_dir / "metrics.json", metrics)
    save_json(run_dir / "run_info.json", {"activation_dir": str(activation_dir), "config": config, "device": str(device)})
    print(f"Best epoch {best_epoch}: val total loss {best_val_loss:.6f}")
    print(f"Pruning kept {pruning_summary['kept_neurons']}/{pruning_summary['total_neurons']} SAE neurons at threshold {pruning_summary['selected_activation_count_threshold']}.")
    return metrics


def main(argv=None):
    args = parse_args(argv)
    activation_dir = Path(args.activation_dir).resolve()
    backbone = load_json(activation_dir / "run_info.json")["backbone"]
    run_dir = new_run_dir(args.output_dir, "sae", f"sae_{backbone}")
    print(f"Saving SAE run to {run_dir}")
    train(load_config(args.config), activation_dir, run_dir, resolve_device(args.device))


if __name__ == "__main__":
    main()

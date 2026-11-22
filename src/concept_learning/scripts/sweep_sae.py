import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from concept_learning.scripts.train_sae import train
from concept_learning.utils import load_config, load_json, new_run_dir, resolve_device, save_json

PAPER_CUB_L0 = 7.66


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Train one SAE per L1 coefficient and compare sparsity with recovered performance.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--activation-dir", required=True)
    parser.add_argument("--l1", type=float, nargs="+", help="L1 coefficients to try (default: sae_l1_sweep from the config).")
    parser.add_argument("--output-dir")
    parser.add_argument("--device")
    return parser.parse_args(argv)


def summary_row(l1, run_dir, metrics):
    pruning = metrics["pruning"]
    return {
        "l1_coefficient": l1,
        "train_avg_l0": metrics["train_avg_l0"],
        "val_avg_l0": metrics["val_avg_l0"],
        "val_reconstruction_loss": metrics["val_reconstruction_loss"],
        "kept_neurons": pruning["kept_neurons"],
        "recovered_loss": pruning["selected_recovered_loss"],
        "recovered_accuracy": pruning["selected_recovered_accuracy"],
        "run_dir": str(run_dir),
    }


def plot_sweep(path, rows):
    l1 = [row["l1_coefficient"] for row in rows]
    series = [
        ("train_avg_l0", "Average L0 (train)"),
        ("val_reconstruction_loss", "Val reconstruction MSE"),
        ("recovered_loss", "Recovered CE loss (after pruning)"),
        ("recovered_accuracy", "Recovered accuracy (after pruning)"),
    ]
    fig, axes = plt.subplots(1, len(series), figsize=(5 * len(series), 4))
    for axis, (key, title) in zip(axes, series):
        axis.plot(l1, [row[key] for row in rows], marker="o")
        axis.set_xscale("log")
        axis.set_xlabel("L1 coefficient")
        axis.set_title(title)
        axis.grid(True)
    axes[0].axhline(PAPER_CUB_L0, color="red", linestyle="--", label=f"M-CBM on CUB ({PAPER_CUB_L0})")
    axes[0].legend()
    plt.tight_layout()
    plt.savefig(path)
    plt.close(fig)


def main(argv=None):
    args = parse_args(argv)
    config = load_config(args.config)
    device = resolve_device(args.device)
    activation_dir = Path(args.activation_dir).resolve()
    backbone = load_json(activation_dir / "run_info.json")["backbone"]
    sweep_dir = new_run_dir(args.output_dir, "sae_sweep", f"sweep_{backbone}")
    print(f"Saving SAE sweep to {sweep_dir}")

    rows = []
    for l1 in sorted(args.l1 or config["sae_l1_sweep"]):
        run_dir = sweep_dir / f"l1_{l1:g}"
        run_dir.mkdir()
        print(f"--- L1 coefficient {l1:g}")
        metrics = train({**config, "sae_l1_coefficient": l1}, activation_dir, run_dir, device)
        rows.append(summary_row(l1, run_dir, metrics))

    with (sweep_dir / "summary.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    save_json(sweep_dir / "summary.json", rows)
    plot_sweep(sweep_dir / "sweep.png", rows)

    print(f"{'L1':>8} {'L0 train':>9} {'val MSE':>9} {'kept':>5} {'rec. loss':>10} {'rec. acc':>9}")
    for row in rows:
        print(
            f"{row['l1_coefficient']:>8g} {row['train_avg_l0']:>9.2f} {row['val_reconstruction_loss']:>9.5f} "
            f"{row['kept_neurons']:>5} {row['recovered_loss']:>10.2%} {row['recovered_accuracy']:>9.2%}"
        )


if __name__ == "__main__":
    main()

import argparse
from contextlib import nullcontext

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader
from tqdm import tqdm

from concept_learning.data import eval_transform, get_splits, train_transform
from concept_learning.models import resnet18_backbone, save_classifier
from concept_learning.utils import load_config, new_run_dir, resolve_device, save_json, set_seed


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Fine-tune ResNet-18 on CUB-200-2011.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-dir")
    parser.add_argument("--device")
    return parser.parse_args(argv)


def make_loader(dataset, batch_size, shuffle, num_workers, device):
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=num_workers,
        pin_memory=device.type == "cuda",
        persistent_workers=num_workers > 0,
    )


def autocast(device):
    return torch.autocast("cuda", dtype=torch.bfloat16) if device.type == "cuda" else nullcontext()


def train_epoch(model, loader, optimizer, scheduler, device):
    model.train()
    total_loss, correct, n = 0.0, 0, 0
    for images, labels in tqdm(loader, desc="train", leave=False):
        images, labels = images.to(device, non_blocking=True), labels.to(device, non_blocking=True)
        with autocast(device):
            logits = model(images)
            loss = F.cross_entropy(logits, labels)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()
        scheduler.step()
        total_loss += loss.item() * len(labels)
        correct += (logits.argmax(1) == labels).sum().item()
        n += len(labels)
    return total_loss / n, correct / n


@torch.no_grad()
def evaluate(model, loader, device):
    model.eval()
    total_loss, correct, n = 0.0, 0, 0
    for images, labels in tqdm(loader, desc="eval", leave=False):
        images, labels = images.to(device, non_blocking=True), labels.to(device, non_blocking=True)
        with autocast(device):
            logits = model(images)
        total_loss += F.cross_entropy(logits.float(), labels, reduction="sum").item()
        correct += (logits.argmax(1) == labels).sum().item()
        n += len(labels)
    return total_loss / n, correct / n


def plot_history(path, history):
    epochs = [row["epoch"] for row in history]
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for axis, metric in zip(axes, ["loss", "accuracy"]):
        axis.plot(epochs, [row[f"train_{metric}"] for row in history], label="Train")
        axis.plot(epochs, [row[f"val_{metric}"] for row in history], label="Validation")
        axis.set_xlabel("Epoch")
        axis.set_title(f"Classifier {metric}")
        axis.legend()
        axis.grid(True)
    plt.tight_layout()
    plt.savefig(path)
    plt.close(fig)


def main(argv=None):
    args = parse_args(argv)
    config = load_config(args.config)
    set_seed(config["seed"])
    device = resolve_device(args.device)
    run_dir = new_run_dir(args.output_dir, "classifier", "resnet18_cub")
    print(f"Saving classifier run to {run_dir} (device: {device})")

    splits = get_splits(config["val_split"], config["seed"], train_tf=train_transform(), eval_tf=eval_transform())
    num_classes = len(splits["test"].class_names)
    batch_size, num_workers = config["clf_batch_size"], config["num_workers"]
    train_loader = make_loader(splits["train"], batch_size, True, num_workers, device)
    val_loader = make_loader(splits["val"], batch_size, False, num_workers, device)
    test_loader = make_loader(splits["test"], batch_size, False, num_workers, device)

    model = resnet18_backbone(num_classes, imagenet_init=config["clf_imagenet_init"]).to(device)
    optimizer = torch.optim.SGD(
        [
            {"params": model.feature_map.parameters(), "lr": config["clf_lr"]},
            {"params": model.head.parameters(), "lr": config["clf_head_lr"]},
        ],
        momentum=config["clf_momentum"],
        weight_decay=config["clf_weight_decay"],
    )
    epochs = config["clf_epochs"]
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs * len(train_loader))

    checkpoint_path = run_dir / "model.pt"
    history, best_val_accuracy, best_epoch = [], -1.0, 0
    for epoch in range(1, epochs + 1):
        train_loss, train_accuracy = train_epoch(model, train_loader, optimizer, scheduler, device)
        val_loss, val_accuracy = evaluate(model, val_loader, device)
        history.append(
            {
                "epoch": epoch,
                "train_loss": train_loss,
                "train_accuracy": train_accuracy,
                "val_loss": val_loss,
                "val_accuracy": val_accuracy,
            }
        )
        print(f"epoch {epoch}: train loss {train_loss:.4f} acc {train_accuracy:.4f}, val loss {val_loss:.4f} acc {val_accuracy:.4f}")
        if val_accuracy > best_val_accuracy:
            best_val_accuracy, best_epoch = val_accuracy, epoch
            save_classifier(checkpoint_path, model, num_classes, {"epoch": epoch, "val_accuracy": val_accuracy})

    model.load_state_dict(torch.load(checkpoint_path, map_location=device)["state_dict"])
    test_loss, test_accuracy = evaluate(model, test_loader, device)
    print(f"Best epoch {best_epoch}: val acc {best_val_accuracy:.4f}, test acc {test_accuracy:.4f}")

    save_json(run_dir / "history.json", history)
    save_json(
        run_dir / "metrics.json",
        {
            "best_epoch": best_epoch,
            "val_accuracy": best_val_accuracy,
            "test_loss": test_loss,
            "test_accuracy": test_accuracy,
        },
    )
    save_json(run_dir / "run_info.json", {"config": config, "device": str(device)})
    plot_history(run_dir / "training_curves.png", history)


if __name__ == "__main__":
    main()

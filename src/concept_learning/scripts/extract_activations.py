import argparse
from pathlib import Path

import torch
from torch.utils.data import DataLoader
from tqdm import tqdm

from concept_learning.data import eval_transform, get_splits, image_names
from concept_learning.models import BACKBONES, load_backbone
from concept_learning.utils import load_config, new_run_dir, resolve_device, save_json


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Save average-pooled backbone embeddings for train/val/test.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--backbone", choices=BACKBONES, default="resnet18_cub")
    parser.add_argument("--checkpoint", help="model.pt from train_classifier (required for resnet18_cub).")
    parser.add_argument("--output-dir")
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--device")
    return parser.parse_args(argv)


@torch.no_grad()
def extract_split(backbone, dataset, batch_size, num_workers, device, split_name):
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False, num_workers=num_workers, pin_memory=device.type == "cuda")
    features, labels, correct = [], [], 0
    for images, batch_labels in tqdm(loader, desc=f"Extracting {split_name}", unit="batch"):
        embeddings = backbone.embed(images.to(device))
        correct += (backbone.head(embeddings).argmax(1).cpu() == batch_labels).sum().item()
        features.append(embeddings.float().cpu())
        labels.append(batch_labels)
    return torch.cat(features), torch.cat(labels), correct / len(dataset)


def main(argv=None):
    args = parse_args(argv)
    config = load_config(args.config)
    device = resolve_device(args.device)
    backbone = load_backbone(args.backbone, args.checkpoint, device)
    run_dir = new_run_dir(args.output_dir, "activations", f"activations_{args.backbone}")
    print(f"Saving activations to {run_dir}")

    splits = get_splits(config["val_split"], config["seed"], eval_tf=eval_transform())

    accuracies = {}
    for split_name, dataset in splits.items():
        features, labels, accuracy = extract_split(backbone, dataset, args.batch_size, config["num_workers"], device, split_name)
        torch.save(
            {"features": features, "labels": labels, "image_names": image_names(dataset)},
            run_dir / f"activations_{split_name}.pt",
        )
        accuracies[split_name] = accuracy
        print(f"{split_name}: {tuple(features.shape)} embeddings, classifier accuracy {accuracy:.4f}")

    save_json(
        run_dir / "run_info.json",
        {
            "backbone": args.backbone,
            "checkpoint": str(Path(args.checkpoint).resolve()) if args.checkpoint else None,
            "val_split": config["val_split"],
            "seed": config["seed"],
            "classifier_accuracy": accuracies,
        },
    )


if __name__ == "__main__":
    main()

import os
from pathlib import Path

import pandas as pd
import torch
from PIL import Image
from sklearn.model_selection import train_test_split
from torch.utils.data import Subset
from torchvision import transforms

from concept_learning.utils import PROJECT_ROOT

DATASET_FOLDER = Path(os.environ.get("DATASET_FOLDER", PROJECT_ROOT / "datasets"))
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


def cub_root():
    return DATASET_FOLDER / "CUB_200_2011"


class CUBDataset(torch.utils.data.Dataset):
    def __init__(self, root_dir, transform=None, train=True):
        self.root_dir = Path(root_dir)
        self.transform = transform

        images = pd.read_csv(self.root_dir / "images.txt", sep=" ", header=None, names=["img_id", "filepath"])
        labels = pd.read_csv(self.root_dir / "image_class_labels.txt", sep=" ", header=None, names=["img_id", "label"])
        split = pd.read_csv(self.root_dir / "train_test_split.txt", sep=" ", header=None, names=["img_id", "is_train"])
        classes = pd.read_csv(self.root_dir / "classes.txt", sep=" ", header=None, names=["class_id", "name"])

        data = images.merge(labels, on="img_id").merge(split, on="img_id")
        self.data = data[data["is_train"] == int(train)].reset_index(drop=True)
        self.targets = (self.data["label"] - 1).astype(int).tolist()
        self.class_names = [name.split(".", 1)[-1].replace("_", " ") for name in classes.sort_values("class_id")["name"]]

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        image = self.load_image(idx)
        if self.transform:
            image = self.transform(image)
        return image, self.targets[idx]

    def get_image_name(self, idx):
        return str(self.data.iloc[idx]["filepath"])

    def load_image(self, idx):
        return self.load_image_by_name(self.get_image_name(idx))

    def load_image_by_name(self, image_name):
        return Image.open(self.root_dir / "images" / image_name).convert("RGB")


def eval_transform():
    return transforms.Compose(
        [
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ]
    )


def train_transform():
    return transforms.Compose(
        [
            transforms.RandomResizedCrop(224),
            transforms.RandomHorizontalFlip(),
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ]
    )


def display_transform():
    return transforms.Compose([transforms.Resize(256), transforms.CenterCrop(224)])


def stratified_val_indices(targets, val_split, seed):
    train_indices, val_indices = train_test_split(
        range(len(targets)),
        test_size=val_split,
        random_state=int(seed),
        stratify=targets,
    )
    return sorted(train_indices), sorted(val_indices)


def get_splits(val_split, seed, train_tf=None, eval_tf=None, root=None):
    """Official CUB test split plus a class-stratified validation split carved out of the official train split."""
    root = root or cub_root()
    train_full = CUBDataset(root, transform=train_tf or eval_tf, train=True)
    train_eval = CUBDataset(root, transform=eval_tf, train=True)
    train_indices, val_indices = stratified_val_indices(train_full.targets, val_split, seed)
    return {
        "train": Subset(train_full, train_indices),
        "val": Subset(train_eval, val_indices),
        "test": CUBDataset(root, transform=eval_tf, train=False),
    }


def image_names(dataset):
    if isinstance(dataset, Subset):
        return [dataset.dataset.get_image_name(i) for i in dataset.indices]
    return [dataset.get_image_name(i) for i in range(len(dataset))]

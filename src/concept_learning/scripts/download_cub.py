import argparse
import shutil
import tarfile
import urllib.request
from pathlib import Path

from tqdm import tqdm

from concept_learning.data import DATASET_FOLDER

CUB_URL = "https://data.caltech.edu/records/65de6-vp158/files/CUB_200_2011.tgz?download=1"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Download and extract CUB-200-2011.")
    parser.add_argument("--dataset-folder", type=Path, default=DATASET_FOLDER)
    return parser.parse_args(argv)


def download(url, path):
    request = urllib.request.Request(url, headers={"User-Agent": "concept-learning"})
    with urllib.request.urlopen(request) as response, path.open("wb") as f:
        total = int(response.headers.get("Content-Length", 0)) or None
        with tqdm(total=total, unit="B", unit_scale=True, desc=path.name) as progress:
            while chunk := response.read(1 << 20):
                f.write(chunk)
                progress.update(len(chunk))


def main(argv=None):
    args = parse_args(argv)
    target = args.dataset_folder / "CUB_200_2011"
    if (target / "images.txt").exists():
        print(f"CUB-200-2011 already present at {target}")
        return

    args.dataset_folder.mkdir(parents=True, exist_ok=True)
    archive = args.dataset_folder / "CUB_200_2011.tgz"
    partial = archive.with_suffix(".tgz.part")
    if not archive.exists():
        download(CUB_URL, partial)
        shutil.move(partial, archive)

    print(f"Extracting {archive}")
    with tarfile.open(archive) as tar:
        tar.extractall(args.dataset_folder, filter="data")
    archive.unlink()
    print(f"CUB-200-2011 ready at {target}")


if __name__ == "__main__":
    main()

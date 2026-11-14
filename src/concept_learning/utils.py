import json
import random
from datetime import datetime
from pathlib import Path

import numpy as np
import torch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUTS = PROJECT_ROOT / "outputs"


def load_config(path):
    return json.loads(Path(path).read_text())


def save_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2))


def load_json(path):
    return json.loads(Path(path).read_text())


def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def resolve_device(override=None):
    return torch.device(override or ("cuda" if torch.cuda.is_available() else "cpu"))


def new_run_dir(output_dir, default_parent, prefix):
    if output_dir is not None:
        run_dir = Path(output_dir)
    else:
        run_dir = OUTPUTS / default_parent / f"{prefix}_{datetime.now():%Y%m%d_%H%M%S}"
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir

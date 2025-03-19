import os
import yaml


def load_checkpoint(file="checkpoint/checkpoint.yaml"):
    if os.path.exists(file):
        with open(file, "r") as f:
            return yaml.safe_load(f)
    return {"version": None}


def save_checkpoint(checkpoint, file="checkpoint/checkpoint.yaml"):
    with open(file, "w") as f:
        yaml.dump(checkpoint, f)

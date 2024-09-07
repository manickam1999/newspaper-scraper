import yaml


def load_config(file):
    with open(file, "r") as f:
        return yaml.safe_load(f)

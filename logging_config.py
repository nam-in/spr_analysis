import logging.config
import sys

import yaml
import os
from pathlib import Path

def get_root_dir():
    if getattr(sys, 'frozen', False):
        return Path(os.path.dirname(sys.executable))
    else:
        return Path(os.path.abspath(__file__)).parent

def main():

    dir_path = Path(os.path.abspath(__file__)).parent
    root_dir = get_root_dir()
    log_dir_path = root_dir / "logs"
    log_dir_path.mkdir(exist_ok=True)

    with open(dir_path / "logging.yaml", 'r') as f:
        config = yaml.safe_load(f.read())
        for handler_name in config["handlers"]:
            handler = config["handlers"][handler_name]
            if "filename" in handler:
                handler["filename"] = handler["filename"].format(path=str(root_dir))
        logging.config.dictConfig(config)


def get_logger(name: str = None):
    return logging.getLogger(name)


main()

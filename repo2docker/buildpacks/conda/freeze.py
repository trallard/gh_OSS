#!/usr/bin/env python3
"""
Freeze the conda environment.yml

It runs the freeze in a continuumio/miniconda3 image to ensure portability

Usage:

python freeze.py [3.8]
"""

from datetime import datetime
import os
import pathlib
import shutil
from subprocess import check_call
import sys

from ruamel.yaml import YAML


# Docker image version can be different than conda version,
# since miniconda3 docker images seem to lag conda releases.
MINICONDA_DOCKER_VERSION = "4.7.12"
CONDA_VERSION = "4.7.12"

HERE = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))

ENV_FILE = HERE / "environment.yml"
FROZEN_FILE = os.path.splitext(ENV_FILE)[0] + ".frozen.yml"

ENV_FILE_T = HERE / "environment.py-{py}.yml"
FROZEN_FILE_T = os.path.splitext(ENV_FILE_T)[0] + ".frozen.yml"

yaml = YAML(typ="rt")


def freeze(env_file, frozen_file):
    """Freeze a conda environment.yml

    By running in docker:

        conda env create
        conda env export

    Result will be stored in frozen_file
    """
    frozen_dest = HERE / frozen_file

    if frozen_dest.exists():
        with frozen_dest.open("r") as f:
            line = f.readline()
            if "GENERATED" not in line:
                print(
                    f"{frozen_file.relative_to(HERE)} not autogenerated, not refreezing"
                )
                return
    print(f"Freezing {env_file} -> {frozen_file}")

    with frozen_dest.open("w") as f:
        f.write(
            f"# AUTO GENERATED FROM {env_file.relative_to(HERE)}, DO NOT MANUALLY MODIFY\n"
        )
        f.write(f"# Frozen on {datetime.utcnow():%Y-%m-%d %H:%M:%S UTC}\n")

    check_call(
        [
            "docker",
            "run",
            "--rm",
            "-v" f"{HERE}:/r2d",
            "-i",
            f"continuumio/miniconda3:{MINICONDA_DOCKER_VERSION}",
            "sh",
            "-c",
            "; ".join(
                [
                    "set -ex",
                    f"conda install -yq -S conda={CONDA_VERSION}",
                    "conda config --add channels conda-forge",
                    "conda config --system --set auto_update_conda false",
                    f"conda env create -v -f /r2d/{env_file.relative_to(HERE)} -n r2d",
                    # add conda-forge broken channel as lowest priority in case
                    # any of our frozen packages are marked as broken after freezing
                    "conda config --append channels conda-forge/label/broken",
                    f"conda env export -n r2d >> /r2d/{frozen_file.relative_to(HERE)}",
                ]
            ),
        ]
    )


def set_python(py_env_file, py):
    """Set the Python version in an env file"""
    if os.path.exists(py_env_file):
        # only clobber auto-generated files
        with open(py_env_file) as f:
            text = f.readline()
            if "GENERATED" not in text:
                return

    print(f"Regenerating {py_env_file} from {ENV_FILE}")
    with open(ENV_FILE) as f:
        env = yaml.load(f)
    for idx, dep in enumerate(env["dependencies"]):
        if dep.split("=")[0] == "python":
            env["dependencies"][idx] = f"python={py}.*"
            break
    else:
        raise ValueError(f"python dependency not found in {env['dependencies']}")
    # update python dependency
    with open(py_env_file, "w") as f:
        f.write(
            f"# AUTO GENERATED FROM {ENV_FILE.relative_to(HERE)}, DO NOT MANUALLY MODIFY\n"
        )
        f.write(f"# Generated on {datetime.utcnow():%Y-%m-%d %H:%M:%S UTC}\n")
        yaml.dump(env, f)


if __name__ == "__main__":
    # allow specifying which Pythons to update on argv
    pys = sys.argv[1:] or ("2.7", "3.6", "3.7", "3.8")
    default_py = "3.7"
    for py in pys:
        env_file = pathlib.Path(str(ENV_FILE_T).format(py=py))
        set_python(env_file, py)
        frozen_file = pathlib.Path(os.path.splitext(env_file)[0] + ".frozen.yml")
        freeze(env_file, frozen_file)
        if py == default_py:
            shutil.copy(frozen_file, FROZEN_FILE)

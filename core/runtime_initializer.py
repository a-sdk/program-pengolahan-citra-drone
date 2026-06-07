from pathlib import Path
import shutil
import json
from path_config import AppPaths

def copy_if_missing(source: Path, target: Path):

    if not target.exists():

        target.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        shutil.copy2(
            source,
            target
        )

def restore_models(config):

    models = config.get(
        "models",
        {}
    )

    for item in models.values():

        relative_path = item["path"]

        source = (
            AppPaths.assets(
                "defaults/models"
            )
            / relative_path
        )

        target = (
            AppPaths.MODELS
            / relative_path
        )

        copy_if_missing(
            source,
            target
        )

def restore_scalers(config):

    scalers = config.get(
        "scalers",
        {}
    )

    for item in scalers.values():

        relative_path = item["path"]

        source = (
            AppPaths.assets(
                "defaults/scalers"
            )
            / relative_path
        )

        target = (
            AppPaths.SCALERS
            / relative_path
        )

        copy_if_missing(
            source,
            target
        )

        
def initialize_runtime():

    AppPaths.ensure_runtime_dirs()

    default_config = AppPaths.assets(
        "defaults/config/models.json"
    )

    runtime_config = AppPaths.CONFIG / "models.json"

    copy_if_missing(
        default_config,
        runtime_config
    )

    with open(
        runtime_config,
        "r",
        encoding="utf-8"
    ) as f:

        config = json.load(f)

    restore_models(config)

    restore_scalers(config)
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

    default_model_config = AppPaths.assets(
        "defaults/config/models.json"
    )

    default_info_config = AppPaths.assets(
        "defaults/config/info.json"
    )

    runtime_model_config = AppPaths.CONFIG / "models.json"
    runtime_info_config = AppPaths.CONFIG / "info.json"

    copy_if_missing(
        default_model_config,
        runtime_model_config
    )

    copy_if_missing(
        default_info_config,
        runtime_info_config
    )

    with open(
        runtime_model_config,
        "r",
        encoding="utf-8"
    ) as f:

        model_config = json.load(f)

    restore_models(model_config)

    restore_scalers(model_config)
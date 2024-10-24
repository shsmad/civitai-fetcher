import argparse
import os

import loguru

from mkdocs.commands import build
from mkdocs.config import load_config

from .models import Settings
from src.civitai import Civitai
from src.db import DBApi
from src.mdgenerator import model_to_markdown, models_to_markdown
from src.metadata import MetadataManipulator
from src.tensorreader import get_corrupted_files

# loguru.logger.update(
#     {"format": "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"}
# )


def run():
    parser = argparse.ArgumentParser(description="Process some data.")
    parser.add_argument(
        "--force_calc_hashes",
        action="store_true",
        default=False,
        help="Force calculation of hashes (default: False)",
    )
    parser.add_argument(
        "--skip_fetch_metadata",
        action="store_true",
        default=False,
        help="Skip fetching metadata (default: False)",
    )
    args = parser.parse_args()

    settings = Settings()
    api = Civitai(base_url=settings.CIVITAI_API_BASE_URL, api_key=settings.CIVITAI_API_TOKEN)
    dbapi = DBApi(db_path=f"{settings.WORK_DIR}/db.sqlite")
    corrupted_tensors = get_corrupted_files(base_path=settings.BASE_PATH)
    if corrupted_tensors:
        loguru.logger.warning(f"{corrupted_tensors=}")

    meta = MetadataManipulator(
        csv_file_path=settings.MODEL_LIST_FILE,
        base_path=settings.BASE_PATH,
        work_dir=settings.WORK_DIR,
        models_path=settings.MODELS_PATH,
        loras_path=settings.LORAS_PATH,
        civitai_api=api,
        db_api=dbapi,
        hash_algorithm=settings.HASH_ALGORITHM,
        force_calc_hashes=args.force_calc_hashes,
        skip_fetch_metadata=args.skip_fetch_metadata,
    )

    # # alert about newer versions
    # meta.find_new_versions()
    # print()
    # # alert about having inpaint versions
    # meta.find_inpaint_versions()
    models = meta.list_models_with_versions()
    for model in models:
        # if model.id == 573152:
        #     import ipdb

        #     ipdb.set_trace()
        os.makedirs(f"{settings.WORK_DIR}/{model.type}", exist_ok=True)
        with open(f"{settings.WORK_DIR}/{model.type}/model-{model.id}.md", "w") as f:
            f.write(model_to_markdown(model))

    with open(f"{settings.WORK_DIR}/index.md", "w") as f:
        f.write(models_to_markdown(models))

    # for failed in tf_failed:
    #     print(failed.model_version_metadata.files)
    # api.download(
    #     "https://civitai.com/api/download/models/474400",
    #     "/stablediff/models/fetched/",
    # )

    config = load_config(config_file="mkdocs.yml", docs_dir=settings.WORK_DIR)
    build.build(config)


if __name__ == "__main__":
    run()

# TODO: всё плохо с model-4201.md

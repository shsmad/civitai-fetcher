from .models import Settings
from src.civitai import Civitai
from src.metadata import MetadataManipulator


def run():
    settings = Settings()
    api = Civitai(base_url=settings.CIVITAI_API_BASE_URL, api_key=settings.CIVITAI_API_TOKEN)
    meta = MetadataManipulator(
        csv_file_path=settings.MODEL_LIST_FILE,
        model_base_path=settings.MODEL_BASE_PATH,
        civitai_api=api,
    )
    tf_failed = meta.filter_failed_by_tensorflow()

    # meta.update_metadata_from_civitai()

    # validate checksums
    # alert about newer versions
    # alert about having inpaint versions

    # for failed in tf_failed:
    #     print(failed.model_version_metadata.files)
    api.download(
        "https://civitai.com/api/download/models/474400",
        "/stablediff/models/fetched/",
    )
    import ipdb

    ipdb.set_trace()


if __name__ == "__main__":
    run()

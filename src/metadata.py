import csv

from src.civitai import Civitai
from src.models import CivitaiModel, CSVModelRecord
from src.tensorreader import can_read_safetensor_metadata
from src.utils import recursively_find_all_files_by_extension_in_folder


class MetadataManipulator:
    def __init__(
        self,
        csv_file_path: str,
        model_base_path: str,
        civitai_api: Civitai,
    ):
        self.csv_file_path = csv_file_path
        self.model_base_path = model_base_path
        self.civitai_api = civitai_api
        self.modelmeta: list[CSVModelRecord] = []
        self.parse_csv()
        self.inject_filepath()

    def parse_csv(self):
        with open(self.csv_file_path) as f:
            reader = csv.DictReader(f, delimiter=";", quotechar='"', lineterminator="\n")
            self.modelmeta = [CSVModelRecord(**row) for row in reader]

    def inject_filepath(self):
        paths = recursively_find_all_files_by_extension_in_folder(folder=self.model_base_path, extension="safetensors")

        for model in self.modelmeta:
            model.filepath = paths.get(f"{model.model_name}.safetensors", None)

    def filter_failed_by_tensorflow(self):
        return [model for model in self.modelmeta if not can_read_safetensor_metadata(model.filepath)]

    def update_metadata_from_civitai(self) -> None:
        meta_dict: dict[str, CivitaiModel] = {}

        for model in self.modelmeta:
            if not model.model_id:
                continue

            if model.model_id in meta_dict:
                civitai_model = meta_dict[model.model_id]
            else:
                civitai_model = self.civitai_api.get_model(model.model_id)
                meta_dict[model.model_id] = civitai_model

                with open(f"{self.model_base_path}/{model.model_id}.json", "w") as f:
                    f.write(civitai_model.model_dump_json(indent=4))

            model.model_metadata = civitai_model
            model.model_version_metadata = next(
                (v for v in civitai_model.modelVersions if str(v.id) == model.model_version_id),
                None,
            )

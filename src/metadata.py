import os

import loguru

from tqdm import tqdm

from src.civitai import Civitai
from src.db import DBApi
from src.models import CivitaiModel, CivitaiModelVersion, DBAPIFileHash
from src.utils import find_position_by_id, gen_filehash, recursively_find_all_files_by_extension_in_folder


class MetadataManipulator:
    def __init__(
        self,
        csv_file_path: str,
        base_path: str,
        models_path: str,
        loras_path: str,
        work_dir: str,
        civitai_api: Civitai,
        db_api: DBApi,
        hash_algorithm: str = "blake3",
        force_calc_hashes: bool = False,
        skip_fetch_metadata: bool = False,
    ):
        self.csv_file_path = csv_file_path
        self.base_path = base_path
        self.models_path = models_path
        self.loras_path = loras_path
        self.work_dir = work_dir
        os.makedirs(self.work_dir, exist_ok=True)

        self.civitai_api = civitai_api
        self.db_api = db_api
        self.hash_algorithm = hash_algorithm
        self.force_calc_hashes = force_calc_hashes
        self.skip_fetch_metadata = skip_fetch_metadata
        self.model_versions: list[CivitaiModelVersion] = []
        self.models: list[CivitaiModel] = []
        # self.parse_csv()
        # self.inject_filepath()

        self.precalc_filehashes()
        self.update_model_version_metadata()

    def precalc_filehashes(self):
        old_hashes = self.db_api.get_filehashes()
        old_filenames = set(old_hashes.keys())

        for folder in (self.models_path, self.loras_path):
            loguru.logger.info(f"Calculating {self.hash_algorithm} for {folder}")
            paths = recursively_find_all_files_by_extension_in_folder(
                folder=os.path.join(self.base_path, folder),
                extension="safetensors",
            ).values()
            for path in paths:
                if path in old_filenames:
                    old_filenames.remove(path)

                if self.force_calc_hashes or path not in old_hashes or not old_hashes[path].filehash:
                    self.db_api.update_filehash(path, gen_filehash(path, algorithm=self.hash_algorithm))

        if old_filenames:
            loguru.logger.warning(f"Files not found: {old_filenames}, removing db records")
            for path in old_filenames:
                self.db_api.remove_filehash(path)

    def update_model_version_metadata(self) -> list[DBAPIFileHash]:
        loguru.logger.info("Fetching model versions by hash")
        models_not_found = []
        items = self.db_api.get_filehashes().values()

        for item in items:
            if not item.modelid or not item.modelversionid:
                if self.skip_fetch_metadata:
                    continue

                modelversion = self.civitai_api.get_modelversion_by_hash(filehash=item.filehash)
                if not modelversion:
                    models_not_found.append(item)
                    loguru.logger.warning(f"Model not found: {item.filehash} for {item.filepath}")
                    continue

                if modelversion.modelId:
                    self.db_api.update_data(
                        filepath=item.filepath,
                        model_id=modelversion.modelId,
                        model_version_id=modelversion.id,
                    )

                metafilename = f"{self.base_path}/.civitai-fetcher/modelversion-{modelversion.id}.json"

                with open(metafilename, "w") as f:
                    f.write(modelversion.model_dump_json(indent=4))
            else:
                metafilename = f"{self.base_path}/.civitai-fetcher/modelversion-{item.modelversionid}.json"
                with open(metafilename) as f:
                    modelversion = CivitaiModelVersion.model_validate_json(f.read())

            self.model_versions.append(modelversion)

        model_ids = {x.modelid for x in self.db_api.get_filehashes().values() if x.modelid}
        loguru.logger.info(f"Fetching {len(model_ids)} models by id")
        with tqdm(total=len(model_ids), initial=0) as progress:
            fetched_model_ids = set()
            for model_id in model_ids:
                progress.update(1)

                metafilename = f"{self.base_path}/.civitai-fetcher/model-{model_id}.json"

                if os.path.exists(metafilename) and (self.skip_fetch_metadata or model_id in fetched_model_ids):
                    with open(metafilename) as f:
                        model = CivitaiModel.model_validate_json(f.read())
                else:
                    model = self.civitai_api.get_model(model_id=model_id)
                    if not model:
                        loguru.logger.warning(f"Model not found: {model_id}")
                        continue

                    fetched_model_ids.add(model_id)

                    with open(metafilename, "w") as f:
                        f.write(model.model_dump_json(indent=4))
                # if model.id == 573152:
                #     import ipdb

                #     ipdb.set_trace()
                for mv in self.model_versions:
                    if mv.modelId == model_id:
                        # mv.model = model
                        for idx, mv2 in enumerate(model.modelVersions):
                            if not model.modelVersions[idx].modelId:
                                model.modelVersions[idx].modelId = model_id

                            if mv2.id == mv.id:
                                mv.index = mv2.index
                                model.modelVersions[idx] = mv
                                model.modelVersions[idx]._exists = True

                self.models.append(model)

        return models_not_found

    def list_models_with_versions(self) -> list[CivitaiModel]:
        # models: dict[int, CivitaiModel] = {}

        # for mv in self.model_versions:
        #     model_id = mv.model_id()
        #     if not model_id or not isinstance(mv.model, CivitaiModel):
        #         continue

        #     if mv.model_id() not in models:
        #         models[model_id] = mv.model

        #     for mv2 in models[model_id].modelVersions:
        #         if mv2.id == mv.id:
        #             mv2._exists = True
        #             break

        return self.models

    # def parse_csv(self):
    #     with open(self.csv_file_path) as f:
    #         reader = csv.DictReader(f, delimiter=";", quotechar='"', lineterminator="\n")
    #         self.modelmeta = [CSVModelRecord(**row) for row in reader]

    def inject_filepath(self):
        paths = recursively_find_all_files_by_extension_in_folder(folder=self.base_path, extension="safetensors")

        for model in self.modelmeta:
            model.filepath = paths.get(f"{model.model_name}.safetensors", None)

    def find_new_versions(self):
        for mv in self.model_versions:
            if not mv.model or not mv.model.modelVersions:
                continue

            position_in_model_versions = find_position_by_id(mv.model.modelVersions, "id", mv.id)
            if position_in_model_versions == 0:
                continue

            new_versions = [
                new_model
                for new_model in mv.model.modelVersions[:position_in_model_versions]
                if new_model.baseModel == mv.baseModel and new_model.baseModelType == mv.baseModelType
            ]
            if not new_versions:
                continue

            print(f"{mv.model.name}@{mv.name}. [{mv.baseModel}, {mv.baseModelType}] {mv.url()}")

            for new_model in new_versions:
                print(
                    f"\tNew version: {new_model.id} @{new_model.name} [{new_model.baseModel}, {new_model.baseModelType}]",
                )
                # for file in new_model.files:
                #     print(
                #         f"\t\t{file.name} {file.sizeKB} {file.metadata.format} {file.metadata.fp} {file.metadata.size} {file.downloadUrl}",
                #     )

    def find_inpaint_versions(self):
        for mv in self.model_versions:
            if not mv.model or not mv.model.modelVersions or mv.baseModelType == "Inpainting":
                continue

            inpaint_versions = [
                new_model
                for new_model in mv.model.modelVersions
                if new_model.baseModel == mv.baseModel and new_model.baseModelType == "Inpainting"
            ]

            if not inpaint_versions:
                continue

            print(f"{mv.model.name}@{mv.name}. [{mv.baseModel}, {mv.baseModelType}] {mv.url()}")

            for new_model in inpaint_versions:
                print(
                    f"\tInpaint version: {new_model.id} @{new_model.name} [{new_model.baseModel}, {new_model.baseModelType}]",
                )
                # for file in new_model.files:
                #     print(
                #         f"\t\t{file.name} {file.sizeKB} {file.metadata.format} {file.metadata.fp} {file.metadata.size} {file.downloadUrl}",
                #     )

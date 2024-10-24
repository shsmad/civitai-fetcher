from itertools import groupby
from operator import itemgetter
from typing import Any, Union

from pydantic import BaseModel
from pydantic_settings import BaseSettings

from src.utils import aggregate_min_max


class Settings(BaseSettings):
    CIVITAI_API_BASE_URL: str
    CIVITAI_API_TOKEN: str
    MODEL_LIST_FILE: str
    BASE_PATH: str
    WORK_DIR: str
    MODELS_PATH: str
    LORAS_PATH: str
    HASH_ALGORITHM: str = "blake3"


class CivitaiFileMetadata(BaseModel):
    format: str | None = None  # enum (SafeTensor, PickleTensor, Other) | undefined
    size: str | None = None  # enum (full, pruned) | undefined
    fp: str | None = None  # enum (fp16, fp32) | undefined

    @property
    def priority(self) -> int:
        value = 0
        if self.format == "SafeTensor":
            value += 200
        if self.size == "pruned":
            value += 20
        elif self.size == "full":
            value += 10
        if self.fp == "fp16":
            value += 2
        elif self.fp == "fp32":
            value += 1
        return value


class CivitaiHashes(BaseModel):
    AutoV1: str | None = None
    AutoV2: str | None = None
    SHA256: str | None = None
    CRC32: str | None = None
    BLAKE3: str | None = None
    AutoV3: str | None = None


class CivitaiImage(BaseModel):
    url: str
    nsfwLevel: int
    width: int
    height: int
    hash: str
    type: str
    hasMeta: bool
    onSite: bool
    meta: dict[str, Any] | None = None

    def is_sfw(self) -> bool:
        return self.nsfwLevel < 4


class CivitaiFile(BaseModel):
    id: int
    sizeKB: float
    name: str
    type: str
    downloadUrl: str
    metadata: CivitaiFileMetadata
    hashes: CivitaiHashes


class CivitaiShortModel(BaseModel):
    name: str
    type: str  # enum (Checkpoint, TextualInversion, Hypernetwork, AestheticGradient, LORA, Controlnet, Poses)


class CivitaiModelVersion(BaseModel):
    id: int
    modelId: int | None = None
    index: int | None = None
    name: str
    description: str | None = None
    trainedWords: list[str] | None = None
    baseModel: str
    baseModelType: str | None = None
    air: str | None = None
    downloadUrl: str
    model: Union[CivitaiShortModel, "CivitaiModel"] | None = None
    files: list[CivitaiFile]
    images: list[CivitaiImage] | None = None

    _exists: bool = False

    def model_id(self) -> int | None:
        return self.modelId or (self.model.id if self.model else None)

    def url(self) -> str | None:
        model_id = self.model_id()
        return f"https://civitai.com/models/{model_id}?modelVersionId={self.id}" if model_id else None

    def get_meta(self):
        elements = [x.meta for x in self.images if x.hasMeta and x.meta.get("sampler")]
        for element in elements:
            sampler_full = element.get("sampler")
            if element.get("Schedule type"):
                sampler_full = f"{sampler_full} {element.get('Schedule type')}"
            element["sampler_full"] = sampler_full

        elements.sort(key=itemgetter("sampler_full"))

        result = {}
        for sampler, sampler_group in groupby(elements, key=itemgetter("sampler_full")):
            sampler_grou_list = list(sampler_group)
            result[sampler] = aggregate_min_max(sampler_grou_list)
        return result


class CivitaiModel(CivitaiShortModel):
    id: int
    description: str | None = None
    modelVersions: list[CivitaiModelVersion]


# class CivitaiResponseMetadata(BaseModel):
#     nextCursor: str | None = None
#     currentPage: int | None = None
#     pageSize: int | None = None
#     totalPages: int | None = None
#     nextPage: int | None = None


# class CivitaiModelResponse(BaseModel):
#     items: list[CivitaiModel]
#     metadata: CivitaiResponseMetadata


# class CSVModelRecord(BaseModel):
#     model_name: str
#     model_version_name: str
#     model_id: str | None
#     model_version_id: str | None
#     base_model: str
#     req_sampler: str
#     req_steps: str
#     req_cfg: str
#     req_other: str
#     user_sampler: str
#     user_steps: str
#     user_cfg: str
#     lora_trigger: str
#     filepath: str | None = None
#     model_metadata: CivitaiModel | None = None
#     model_version_metadata: CivitaiModelVersion | None = None

#     model_config = ConfigDict(
#         protected_namespaces=(),
#     )


class DBAPIFileHash(BaseModel):
    filepath: str
    filehash: str | None = None
    modelid: int | None = None
    modelversionid: int | None = None

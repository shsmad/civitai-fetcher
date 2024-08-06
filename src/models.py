from datetime import datetime

from pydantic import BaseModel, ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    CIVITAI_API_BASE_URL: str
    CIVITAI_API_TOKEN: str
    MODEL_BASE_PATH: str
    MODEL_LIST_FILE: str


class CivitaiCreator(BaseModel):
    username: str
    image: str | None = None


class CivitaiStats(BaseModel):
    downloadCount: int
    favoriteCount: int
    thumbsUpCount: int
    thumbsDownCount: int
    commentCount: int
    ratingCount: int
    rating: int
    tippedAmountCount: int


class CivitaiFileMetadata(BaseModel):
    format: str | None = None  # enum (SafeTensor, PickleTensor, Other) | undefined
    size: str | None = None  # enum (full, pruned) | undefined
    fp: str | None = None  # enum (fp16, fp32) | undefined


class CivitaiHashes(BaseModel):
    AutoV1: str | None = None
    AutoV2: str | None = None
    SHA256: str | None = None
    CRC32: str | None = None
    BLAKE3: str | None = None
    AutoV3: str | None = None


class CivitaiFile(BaseModel):
    id: int
    sizeKB: float
    name: str
    type: str
    downloadUrl: str
    metadata: CivitaiFileMetadata
    hashes: CivitaiHashes


class CivitaiModelVersion(BaseModel):
    id: int
    index: int
    name: str
    baseModel: str
    baseModelType: str
    publishedAt: datetime
    availability: str
    nsfwLevel: int
    description: str | None = None
    trainedWords: list[str] | None = None
    files: list[CivitaiFile]


class CivitaiModel(BaseModel):
    id: int
    name: str
    description: str
    # allowNoCredit: bool
    # allowCommercialUse: list[str]
    # allowDerivatives: bool
    # allowDifferentLicenses: bool
    type: str  # enum (Checkpoint, TextualInversion, Hypernetwork, AestheticGradient, LORA, Controlnet, Poses)
    # minor: bool
    # poi: bool
    nsfw: bool
    # nsfwLevel: int
    # cosmetic: Any
    stats: CivitaiStats
    creator: CivitaiCreator | None = None
    tags: list[str]
    modelVersions: list[CivitaiModelVersion]


class CivitaiResponseMetadata(BaseModel):
    nextCursor: str | None = None
    currentPage: int | None = None
    pageSize: int | None = None
    totalPages: int | None = None
    nextPage: int | None = None


class CivitaiModelResponse(BaseModel):
    items: list[CivitaiModel]
    metadata: CivitaiResponseMetadata


class CSVModelRecord(BaseModel):
    model_name: str
    model_version_name: str
    model_id: str | None
    model_version_id: str | None
    base_model: str
    req_sampler: str
    req_steps: str
    req_cfg: str
    req_other: str
    user_sampler: str
    user_steps: str
    user_cfg: str
    lora_trigger: str
    filepath: str | None = None
    model_metadata: CivitaiModel | None = None
    model_version_metadata: CivitaiModelVersion | None = None

    model_config = ConfigDict(
        protected_namespaces=(),
    )

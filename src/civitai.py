# types: enum[] (Checkpoint, TextualInversion, Hypernetwork, AestheticGradient, LORA, Controlnet, Poses)
# sort: enum (Highest Rated, Most Downloaded, Newest)
# perios: enum (AllTime, Year, Month, Week, Day)
# allowCommercialUse: enum (None, Image, Rent, Sell)


import os
import re
import shutil
import tempfile

import httpx
import loguru

from tqdm import tqdm

from src.models import CivitaiModel, CivitaiModelVersion


def parse_content_disposition(header):
    # Define a regular expression pattern to match the filename parameter
    pattern = r'filename=["\']?([^"\';]+)["\']?'
    match = re.search(pattern, header)
    if match:
        filename = match[1]
        # Remove quotes around the filename if present
        if filename.startswith('"') and filename.endswith('"') or filename.startswith("'") and filename.endswith("'"):
            filename = filename[1:-1]
        return filename
    return None


class Civitai:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {"Authorization": f"Bearer {self.api_key}"}

    def get_model(self, model_id: int):
        url = f"{self.base_url}/models/{model_id}"
        x = httpx.get(url, headers=self.headers, timeout=None)
        return CivitaiModel(**x.json())

    # def get_by_modelVersion(self, modelVersionId: str):
    #     url = f"{self.base_url}/model-versions/{modelVersionId}"
    #     x = httpx.get(url, headers=self.headers)
    #     # return ModelVersion(x.json())
    #     return x.json()

    def get_modelversion_by_hash(self, filehash: str) -> CivitaiModelVersion | None:
        url = f"{self.base_url}/model-versions/by-hash/{filehash}"
        x = httpx.get(url, headers=self.headers)
        return None if x.status_code == 404 else CivitaiModelVersion(**x.json())

    # def search(
    #     self,
    #     limit: int | None = None,
    #     page: int | None = None,
    #     query: str | None = None,
    #     tag: str | None = None,
    #     username: str | None = None,
    #     types: str | None = None,
    #     sort: str | None = None,
    #     period: str | None = None,
    #     favorites: bool | None = None,
    #     hidden: bool | None = None,
    #     primaryFileOnly: bool | None = None,
    #     allowNoCredit: bool | None = None,
    #     allowDerivatives: bool | None = None,
    #     allowDifferentLicenses: bool | None = None,
    #     allowCommercialUse: bool | None = None,
    #     nsfw: bool | None = None,
    # ):
    #     params = {
    #         "limit": limit,
    #         "page": page,
    #         "query": query,
    #         "tag": tag,
    #         "username": username,
    #         "types": types,
    #         "sort": sort,
    #         "period": period,
    #         "favorites": favorites,
    #         "hidden": hidden,
    #         "primaryFileOnly": primaryFileOnly,
    #         "allowNoCredit": allowNoCredit,
    #         "allowDerivatives": allowDerivatives,
    #         "allowDifferentLicenses": allowDifferentLicenses,
    #         "allowCommercialUse": allowCommercialUse,
    #         "nsfw": nsfw,
    #     }
    #     params = {k: v for k, v in params.items() if v is not None}

    #     url = f"{self.base_url}/models"
    #     x = httpx.get(url, headers=self.headers, params=params, timeout=None)
    #     return CivitaiModelResponse(**x.json())

    def download(self, downloadUrl: str, outdir: str) -> str:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as download_file:
            temp_file_path = download_file.name

        # Check the current size of the temporary file
        current_size = os.path.getsize(temp_file_path)

        real_filename = None

        while True:
            try:
                # Open the temporary file in append mode
                with open(temp_file_path, "ab") as f:
                    loguru.logger.info(
                        f"Downloading {downloadUrl} to {temp_file_path} starting from {current_size} bytes",
                    )
                    headers = self.headers.copy()
                    if current_size:
                        headers["Range"] = "bytes={current_size}-"

                    with httpx.stream(
                        "GET",
                        downloadUrl,
                        headers=headers,
                        timeout=None,
                        follow_redirects=True,
                    ) as response:
                        if response.headers.get("Content-Disposition"):
                            # при продолжении докачки после обрыва скачивания имя пустое
                            real_filename = parse_content_disposition(response.headers["Content-Disposition"])

                        total = int(response.headers["Content-Length"]) + current_size

                        with tqdm(
                            total=total,
                            initial=current_size,
                            unit_scale=True,
                            unit_divisor=1024,
                            unit="B",
                        ) as progress:
                            num_bytes_downloaded = response.num_bytes_downloaded + current_size
                            for chunk in response.iter_bytes():
                                f.write(chunk)
                                progress.update(len(chunk))
                                num_bytes_downloaded += len(chunk)
                                current_size += len(chunk)
                    os.makedirs(f"{outdir}/.civitai-fetcher/", exist_ok=True)
                    shutil.move(temp_file_path, f"{outdir}/.civitai-fetcher/{real_filename}")
                    break
            except (httpx.RequestError, httpx.RemoteProtocolError) as e:
                loguru.logger.exception(f"Request error: {e}")
                # Handle the error and retry the download
                continue

        return f"{outdir}/.civitai-fetcher/{real_filename}"

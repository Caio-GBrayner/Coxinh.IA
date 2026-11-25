"""Onde ficam as imagens geradas: em disco ou no Postgres, conforme PERSISTENCE."""

import os
from pathlib import Path
import tempfile
from typing import Protocol

from src.persistence.database import database_url, persistence_mode


DEFAULT_IMAGE_DIR = "data/images"
IMAGE_EXTENSIONS = (".png", ".jpg", ".webp", ".svg")


class ImageStore(Protocol):
    def find(self, key: str) -> str | None:
        """Nome do arquivo já gravado para a chave, ou None."""
        ...

    def save(self, key: str, extension: str, data: bytes) -> str:
        """Grava a imagem e devolve o nome do arquivo."""
        ...

    def read(self, filename: str) -> bytes | None:
        """Conteúdo do arquivo, ou None. Quem chama já validou o nome."""
        ...


class FileImageStore:
    """Um arquivo por chave em `directory`, com gravação atômica."""

    def __init__(self, directory: str | Path) -> None:
        self._directory = Path(directory)

    def find(self, key: str) -> str | None:
        for extension in IMAGE_EXTENSIONS:
            if (self._directory / f"{key}{extension}").is_file():
                return f"{key}{extension}"
        return None

    def save(self, key: str, extension: str, data: bytes) -> str:
        self._directory.mkdir(parents=True, exist_ok=True)
        target = self._directory / f"{key}{extension}"
        fd, temp_name = tempfile.mkstemp(dir=self._directory, suffix=".tmp")
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
            os.replace(temp_name, target)
        except OSError:
            Path(temp_name).unlink(missing_ok=True)
            raise
        return target.name

    def read(self, filename: str) -> bytes | None:
        root = self._directory.resolve()
        path = (root / filename).resolve()
        if path.parent != root or not path.is_file():
            return None
        return path.read_bytes()


def build_image_store() -> ImageStore:
    """Postgres no modo `postgres`; nos demais, a pasta IMAGE_STORAGE_DIR."""
    if persistence_mode() == "postgres":
        from src.persistence.postgres import PostgresImageStore, get_pool

        return PostgresImageStore(get_pool(database_url()))
    return FileImageStore(
        os.getenv("IMAGE_STORAGE_DIR", "").strip() or DEFAULT_IMAGE_DIR
    )

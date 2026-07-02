"""Abstraccion de almacenamiento documental."""

from pathlib import Path, PurePosixPath
from typing import BinaryIO, Protocol


class StorageError(Exception):
    """Fallo controlado de almacenamiento."""


class DocumentStorage(Protocol):
    """Contrato de almacenamiento documental reemplazable."""

    def save(self, source_path: Path, storage_key: str) -> None: ...

    def open(self, storage_key: str) -> BinaryIO: ...

    def delete(self, storage_key: str) -> None: ...

    def exists(self, storage_key: str) -> bool: ...


class LocalDocumentStorage:
    """Almacenamiento local bajo una raiz configurable."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, source_path: Path, storage_key: str) -> None:
        destination = self._resolve(storage_key)
        if destination.exists():
            raise StorageError("La clave de almacenamiento ya existe.")
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            source_path.replace(destination)
        except OSError as exc:
            raise StorageError("No fue posible guardar el archivo.") from exc

    def open(self, storage_key: str) -> BinaryIO:
        path = self._resolve(storage_key)
        if not path.is_file():
            raise StorageError("El archivo almacenado no existe.")
        try:
            return path.open("rb")
        except OSError as exc:
            raise StorageError("No fue posible abrir el archivo.") from exc

    def delete(self, storage_key: str) -> None:
        path = self._resolve(storage_key)
        try:
            if path.exists():
                path.unlink()
        except OSError as exc:
            raise StorageError("No fue posible eliminar el archivo.") from exc

    def exists(self, storage_key: str) -> bool:
        return self._resolve(storage_key).is_file()

    def _resolve(self, storage_key: str) -> Path:
        if "\\" in storage_key or ":" in storage_key:
            raise StorageError("Clave de almacenamiento invalida.")
        key = PurePosixPath(storage_key)
        if key.is_absolute() or any(part in {"", ".", ".."} for part in key.parts):
            raise StorageError("Clave de almacenamiento invalida.")
        path = (self.root / Path(*key.parts)).resolve()
        if not path.is_relative_to(self.root):
            raise StorageError("Clave de almacenamiento fuera de la raiz permitida.")
        return path

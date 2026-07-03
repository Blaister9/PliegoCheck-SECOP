"""Registro versionado de prompts de agentes."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from unicodedata import category, normalize

from sqlalchemy import select
from sqlalchemy.orm import Session

from pliegocheck_api.models import PromptVersion
from pliegocheck_schemas import NormalizationErrorCode

PROMPT_ROOT = Path(__file__).resolve().parents[4] / "prompts" / "requirement-normalization" / "v1"
PROMPT_SEMANTIC_VERSION = "1.0.0"
PROMPT_PROVIDER = "openai"
REQUIRED_BLOCKS = [
    "IDENTIDAD Y RESPONSABILIDAD",
    "OBJETIVO",
    "CONTEXTO DISPONIBLE",
    "ENTRADAS",
    "DATOS NO CONFIABLES",
    "HERRAMIENTAS",
    "REGLAS DE EJECUCION",
    "REGLAS DE EVIDENCIA",
    "RESTRICCIONES",
    "ESQUEMA DE SALIDA",
    "CRITERIOS DE CALIDAD",
    "CONDICIONES DE PARADA",
    "MANEJO DE INCERTIDUMBRE",
    "ESCALAMIENTO HUMANO",
]


class PromptRegistryError(RuntimeError):
    def __init__(self, message: str, code: NormalizationErrorCode) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class PromptFiles:
    prompt_name: str
    system_path: Path
    user_path: Path


NORMALIZATION_PROMPT = PromptFiles(
    prompt_name="requirement-normalization",
    system_path=PROMPT_ROOT / "normalization-system.md",
    user_path=PROMPT_ROOT / "normalization-user.md",
)
CONSOLIDATION_PROMPT = PromptFiles(
    prompt_name="requirement-consolidation",
    system_path=PROMPT_ROOT / "consolidation-system.md",
    user_path=PROMPT_ROOT / "consolidation-user.md",
)


def ensure_prompt_version(session: Session, prompt_files: PromptFiles) -> PromptVersion:
    system_content = _read_prompt(prompt_files.system_path)
    user_template = _read_prompt(prompt_files.user_path)
    _validate_blocks(system_content, prompt_files.system_path)
    _validate_blocks(user_template, prompt_files.user_path)
    digest = prompt_digest(system_content, user_template)
    existing = session.scalar(
        select(PromptVersion)
        .where(
            PromptVersion.prompt_name == prompt_files.prompt_name,
            PromptVersion.semantic_version == PROMPT_SEMANTIC_VERSION,
            PromptVersion.content_sha256 == digest,
            PromptVersion.provider == PROMPT_PROVIDER,
        )
        .order_by(PromptVersion.created_at.desc())
        .limit(1)
    )
    if existing is not None:
        if not existing.is_active:
            existing.is_active = True
        return existing

    session.query(PromptVersion).filter(
        PromptVersion.prompt_name == prompt_files.prompt_name,
        PromptVersion.is_active.is_(True),
    ).update({"is_active": False})
    prompt = PromptVersion(
        prompt_name=prompt_files.prompt_name,
        semantic_version=PROMPT_SEMANTIC_VERSION,
        content_sha256=digest,
        system_content=system_content,
        user_template_content=user_template,
        provider=PROMPT_PROVIDER,
        is_active=True,
    )
    session.add(prompt)
    session.flush()
    return prompt


def prompt_digest(system_content: str, user_template: str) -> str:
    canonical = f"{system_content}\n---USER TEMPLATE---\n{user_template}".encode()
    return sha256(canonical).hexdigest()


def _read_prompt(path: Path) -> str:
    if not path.exists():
        raise PromptRegistryError(
            f"No existe el prompt versionado: {path.name}",
            NormalizationErrorCode.PROMPT_VERSION_NOT_FOUND,
        )
    return path.read_text(encoding="utf-8").strip() + "\n"


def _validate_blocks(content: str, path: Path) -> None:
    normalized = _strip_accents(content).upper()
    missing = [block for block in REQUIRED_BLOCKS if f"# {block}" not in normalized]
    if missing:
        raise PromptRegistryError(
            f"Prompt invalido {path.name}: faltan bloques {', '.join(missing)}",
            NormalizationErrorCode.PROMPT_INVALID,
        )


def _strip_accents(value: str) -> str:
    decomposed = normalize("NFD", value)
    return "".join(char for char in decomposed if category(char) != "Mn")

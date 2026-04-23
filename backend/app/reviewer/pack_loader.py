from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from app.config import settings
from app.models import PackSummary


@dataclass(frozen=True)
class PackModels:
    reviewer: str | None = None
    consolidator: str | None = None


@dataclass(frozen=True)
class Pack:
    id: str
    name: str
    description: str
    version: str
    can_rewrite: bool
    severity_model: dict[str, str]
    models: PackModels
    guidelines: str
    reviewer_template: str  # raw jinja2 source (or None → default)
    consolidator_template: str  # raw jinja2 source (or None → default)
    path: Path

    @property
    def summary(self) -> PackSummary:
        return PackSummary(
            id=self.id,
            name=self.name,
            description=self.description,
            version=self.version,
        )


_DEFAULT_REVIEWER_PATH = Path(__file__).parent / "prompts" / "reviewer.jinja2"
_DEFAULT_CONSOLIDATOR_PATH = Path(__file__).parent / "prompts" / "consolidator.jinja2"


def _read_or_default(pack_dir: Path, filename: str, default_path: Path) -> str:
    p = pack_dir / filename
    if p.exists():
        return p.read_text(encoding="utf-8")
    return default_path.read_text(encoding="utf-8")


def load_pack(pack_id: str, packs_dir: Path | None = None) -> Pack:
    root = packs_dir or settings.packs_path
    pack_dir = root / pack_id
    if not pack_dir.exists():
        raise FileNotFoundError(f"Pack not found: {pack_id} (looked in {pack_dir})")

    yaml_path = pack_dir / "pack.yaml"
    if not yaml_path.exists():
        raise FileNotFoundError(f"Missing pack.yaml in {pack_dir}")

    meta = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))

    guidelines_path = pack_dir / "guidelines.md"
    if not guidelines_path.exists():
        raise FileNotFoundError(f"Missing guidelines.md in {pack_dir}")
    guidelines = guidelines_path.read_text(encoding="utf-8")

    models_cfg = meta.get("models") or {}
    return Pack(
        id=meta["id"],
        name=meta["name"],
        description=meta.get("description", ""),
        version=str(meta.get("version", "0.0.0")),
        can_rewrite=bool(meta.get("can_rewrite", False)),
        severity_model=meta.get("severity_model", {}),
        models=PackModels(
            reviewer=models_cfg.get("reviewer"),
            consolidator=models_cfg.get("consolidator"),
        ),
        guidelines=guidelines,
        reviewer_template=_read_or_default(pack_dir, "reviewer.jinja2", _DEFAULT_REVIEWER_PATH),
        consolidator_template=_read_or_default(
            pack_dir, "consolidator.jinja2", _DEFAULT_CONSOLIDATOR_PATH
        ),
        path=pack_dir,
    )


def list_packs(packs_dir: Path | None = None) -> list[PackSummary]:
    root = packs_dir or settings.packs_path
    if not root.exists():
        return []
    out: list[PackSummary] = []
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        if not (child / "pack.yaml").exists():
            continue
        try:
            out.append(load_pack(child.name, root).summary)
        except Exception:
            # Skip broken packs rather than failing the whole list.
            continue
    return out

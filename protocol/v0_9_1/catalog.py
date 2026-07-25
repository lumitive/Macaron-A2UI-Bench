"""Active catalog resolution for A2UI 0.9.1 (basic | lumi)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

_SPEC_DIR = Path(__file__).resolve().parent / "spec"

BASIC_CATALOG_ID = "https://a2ui.org/specification/v0_9/catalogs/basic/catalog.json"
LUMI_CATALOG_ID = "lumi.ai:a2ui:lumi-catalog"

# Back-compat alias used across Phase-1 call sites
LOCKED_CATALOG_ID = BASIC_CATALOG_ID


@dataclass(frozen=True)
class CatalogInfo:
    name: str
    catalog_id: str
    path: Path
    component_types: frozenset[str]


def _load_types(path: Path) -> frozenset[str]:
    catalog = json.loads(path.read_text(encoding="utf-8"))
    components = catalog.get("components") or {}
    if not isinstance(components, dict):
        return frozenset()
    return frozenset(components.keys())


_CATALOGS: dict[str, CatalogInfo] = {
    "basic": CatalogInfo(
        name="basic",
        catalog_id=BASIC_CATALOG_ID,
        path=_SPEC_DIR / "catalogs" / "basic" / "catalog.json",
        component_types=_load_types(_SPEC_DIR / "catalogs" / "basic" / "catalog.json"),
    ),
    "lumi": CatalogInfo(
        name="lumi",
        catalog_id=LUMI_CATALOG_ID,
        path=_SPEC_DIR / "catalogs" / "lumi" / "catalog.json",
        component_types=_load_types(_SPEC_DIR / "catalogs" / "lumi" / "catalog.json"),
    ),
}


def get_catalog(name: str) -> CatalogInfo:
    key = (name or "basic").strip().lower()
    if key not in _CATALOGS:
        raise ValueError(
            f"Unsupported protocol catalog: {name!r} (expected 'basic' or 'lumi')"
        )
    info = _CATALOGS[key]
    if not info.path.is_file():
        raise FileNotFoundError(f"Catalog asset missing: {info.path}")
    return info


def list_catalog_names() -> tuple[str, ...]:
    return tuple(_CATALOGS.keys())

"""ValidationContext: pre-processes A2UI messages into lookup indexes."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ..a2ui_schema_registry import build_a2ui_message_schema_dict
from .component_schema import ComponentSchema

# ---------------------------------------------------------------------------
# Schema loading with module-level cache
# ---------------------------------------------------------------------------

_default_schema: ComponentSchema | None = None


def get_schema(path: str | Path | None = None) -> ComponentSchema:
    """Return the cached default ComponentSchema, or load from *path*."""
    global _default_schema
    if path is not None:
        return ComponentSchema.from_file(path)
    if _default_schema is None:
        _default_schema = ComponentSchema.from_dict(build_a2ui_message_schema_dict())
    return _default_schema


# ---------------------------------------------------------------------------
# Backward-compatible module-level constants (derived from default schema)
# ---------------------------------------------------------------------------

def _schema() -> ComponentSchema:
    return get_schema()

# Lazy properties that derive from the default schema on first access.
# We use a simple class to avoid loading the schema at import time.

class _LazyConstants:
    """Module-level constants derived lazily from the default schema."""
    _loaded = False

    KNOWN_COMPONENT_TYPES: set[str] = set()
    CONTAINER_CHILD_FIELDS: dict[str, list[str]] = {}
    CONTAINER_CHILDREN_TYPES: set[str] = set()
    ICON_NAMES: set[str] = set()
    VALUE_TYPE_KEYS: set[str] = set()

    @classmethod
    def _ensure(cls) -> None:
        if cls._loaded:
            return
        s = _schema()
        cls.KNOWN_COMPONENT_TYPES = s.known_component_types
        cls.CONTAINER_CHILD_FIELDS = s.container_child_fields
        cls.CONTAINER_CHILDREN_TYPES = s.container_children_types
        cls.ICON_NAMES = s.icon_names
        cls.VALUE_TYPE_KEYS = s.value_type_keys
        cls._loaded = True


def _get_known_component_types() -> set[str]:
    _LazyConstants._ensure()
    return _LazyConstants.KNOWN_COMPONENT_TYPES

def _get_container_child_fields() -> dict[str, list[str]]:
    _LazyConstants._ensure()
    return _LazyConstants.CONTAINER_CHILD_FIELDS

def _get_container_children_types() -> set[str]:
    _LazyConstants._ensure()
    return _LazyConstants.CONTAINER_CHILDREN_TYPES

def _get_icon_names() -> set[str]:
    _LazyConstants._ensure()
    return _LazyConstants.ICON_NAMES

def _get_value_type_keys() -> set[str]:
    _LazyConstants._ensure()
    return _LazyConstants.VALUE_TYPE_KEYS


# These remain as module-level names for backward compatibility.
# They are accessed frequently so we keep them as direct references
# (populated on first use in ValidationContext.__post_init__).
KNOWN_COMPONENT_TYPES: set[str] = set()
CONTAINER_CHILD_FIELDS: dict[str, list[str]] = {}
CONTAINER_CHILDREN_TYPES: set[str] = set()
ICON_NAMES: set[str] = set()
VALUE_TYPE_KEYS: set[str] = set()

# Protocol-level constant — not derived from schema
VALID_ACTION_KEYS: set[str] = {
    "beginRendering", "surfaceUpdate", "dataModelUpdate", "deleteSurface",
}


def _ensure_module_constants() -> None:
    """Populate the module-level constants from the default schema (once)."""
    global KNOWN_COMPONENT_TYPES, CONTAINER_CHILD_FIELDS, CONTAINER_CHILDREN_TYPES
    global ICON_NAMES, VALUE_TYPE_KEYS
    if KNOWN_COMPONENT_TYPES:
        return
    _LazyConstants._ensure()
    KNOWN_COMPONENT_TYPES = _LazyConstants.KNOWN_COMPONENT_TYPES
    CONTAINER_CHILD_FIELDS = _LazyConstants.CONTAINER_CHILD_FIELDS
    CONTAINER_CHILDREN_TYPES = _LazyConstants.CONTAINER_CHILDREN_TYPES
    ICON_NAMES = _LazyConstants.ICON_NAMES
    VALUE_TYPE_KEYS = _LazyConstants.VALUE_TYPE_KEYS


@dataclass
class ComponentInfo:
    """Stored info about a single component."""
    comp_id: str
    msg_idx: int          # index into messages list
    comp_idx: int         # index inside surfaceUpdate.components
    comp_dict: dict       # the raw component dict
    comp_type: str = ""   # resolved component type name (e.g. "Text")
    comp_props: dict = field(default_factory=dict)  # the inner props of that type


@dataclass
class ValidationContext:
    """Pre-processed indexes built from a list of A2UI messages.

    These indexes are shared across all validation levels so each
    level can look things up in O(1) rather than re-walking the tree.
    """

    messages: list[dict]
    schema: ComponentSchema | None = None

    # Categorised messages
    begin_renderings: list[tuple[int, dict]] = field(default_factory=list)
    surface_updates: list[tuple[int, dict]] = field(default_factory=list)
    data_model_updates: list[tuple[int, dict]] = field(default_factory=list)
    delete_surfaces: list[tuple[int, dict]] = field(default_factory=list)

    # Component index: id → ComponentInfo
    components: dict[str, ComponentInfo] = field(default_factory=dict)
    # Duplicate IDs: id → list of (msg_idx, comp_idx)
    duplicate_ids: dict[str, list[tuple[int, int]]] = field(default_factory=dict)

    # Graph: parent_id → list[child_id]
    children_graph: dict[str, list[str]] = field(default_factory=dict)
    # Reverse graph: child_id → parent_id
    parent_graph: dict[str, str] = field(default_factory=dict)

    # Template component IDs (components used as template.componentId)
    template_component_ids: set[str] = field(default_factory=set)
    # Template data bindings: componentId → dataBinding path
    template_bindings: dict[str, str] = field(default_factory=dict)

    # Data paths from dataModelUpdate (flattened, absolute)
    data_paths: set[str] = field(default_factory=set)

    # Surface IDs seen across all messages
    surface_ids: set[str] = field(default_factory=set)

    # Root IDs from beginRendering
    root_ids: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if self.schema is None:
            self.schema = get_schema()
        # Also populate module-level constants for backward compat
        _ensure_module_constants()
        self._build_indexes()

    def _build_indexes(self) -> None:
        for msg_idx, msg in enumerate(self.messages):
            if not isinstance(msg, dict):
                continue

            # Categorise by action type
            if "beginRendering" in msg:
                br = msg["beginRendering"]
                self.begin_renderings.append((msg_idx, br))
                sid = br.get("surfaceId")
                if sid:
                    self.surface_ids.add(sid)
                root = br.get("root")
                if root:
                    self.root_ids.add(root)

            if "surfaceUpdate" in msg:
                su = msg["surfaceUpdate"]
                self.surface_updates.append((msg_idx, su))
                sid = su.get("surfaceId")
                if sid:
                    self.surface_ids.add(sid)
                self._index_components(msg_idx, su)

            if "dataModelUpdate" in msg:
                dmu = msg["dataModelUpdate"]
                self.data_model_updates.append((msg_idx, dmu))
                sid = dmu.get("surfaceId")
                if sid:
                    self.surface_ids.add(sid)
                self._index_data_paths(dmu)

            if "deleteSurface" in msg:
                ds = msg["deleteSurface"]
                self.delete_surfaces.append((msg_idx, ds))
                sid = ds.get("surfaceId")
                if sid:
                    self.surface_ids.add(sid)

    def _index_components(self, msg_idx: int, su: dict) -> None:
        components = su.get("components")
        if not isinstance(components, list):
            return

        known = self.schema.known_component_types

        for comp_idx, comp in enumerate(components):
            if not isinstance(comp, dict):
                continue
            comp_id = comp.get("id", "")
            wrapper = comp.get("component", {})
            comp_type = ""
            comp_props: dict = {}
            if isinstance(wrapper, dict):
                for key in wrapper:
                    if key in known:
                        comp_type = key
                        comp_props = wrapper[key] if isinstance(wrapper[key], dict) else {}
                        break
                # If no known type found, pick first key anyway
                if not comp_type and wrapper:
                    comp_type = next(iter(wrapper))
                    val = wrapper[comp_type]
                    comp_props = val if isinstance(val, dict) else {}

            info = ComponentInfo(
                comp_id=comp_id,
                msg_idx=msg_idx,
                comp_idx=comp_idx,
                comp_dict=comp,
                comp_type=comp_type,
                comp_props=comp_props,
            )

            # Track duplicates
            if comp_id in self.components:
                if comp_id not in self.duplicate_ids:
                    prev = self.components[comp_id]
                    self.duplicate_ids[comp_id] = [(prev.msg_idx, prev.comp_idx)]
                self.duplicate_ids[comp_id].append((msg_idx, comp_idx))
            self.components[comp_id] = info

            # Build child graph
            self._extract_children(comp_id, comp_type, comp_props)

    def _extract_children(self, parent_id: str, comp_type: str, props: dict) -> None:
        child_ids: list[str] = []

        # Single-child containers: Card.child, Button.child, Modal.*Child
        if comp_type in self.schema.container_child_fields:
            for field_name in self.schema.container_child_fields[comp_type]:
                child = props.get(field_name)
                if isinstance(child, str):
                    child_ids.append(child)

        # Multi-child containers: Row/Column/List → children.explicitList / children.template
        if comp_type in self.schema.container_children_types:
            children_obj = props.get("children", {})
            if isinstance(children_obj, dict):
                explicit = children_obj.get("explicitList", [])
                if isinstance(explicit, list):
                    for cid in explicit:
                        if isinstance(cid, str):
                            child_ids.append(cid)
                template = children_obj.get("template", {})
                if isinstance(template, dict):
                    tid = template.get("componentId")
                    if isinstance(tid, str):
                        child_ids.append(tid)
                        self.template_component_ids.add(tid)
                        binding = template.get("dataBinding")
                        if isinstance(binding, str):
                            self.template_bindings[tid] = binding

        # Tabs.tabItems[].child
        if comp_type == "Tabs":
            tab_items = props.get("tabItems", [])
            if isinstance(tab_items, list):
                for tab in tab_items:
                    if isinstance(tab, dict):
                        child = tab.get("child")
                        if isinstance(child, str):
                            child_ids.append(child)

        self.children_graph[parent_id] = child_ids
        for cid in child_ids:
            self.parent_graph[cid] = parent_id

    def _index_data_paths(self, dmu: dict) -> None:
        base = dmu.get("path", "/")
        if not isinstance(base, str):
            base = "/"
        if not base.startswith("/"):
            base = "/" + base
        contents = dmu.get("contents", [])
        if isinstance(contents, list):
            self._flatten_data_paths(base, contents)

    def _flatten_data_paths(self, prefix: str, entries: list) -> None:
        if prefix != "/":
            self.data_paths.add(prefix)
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            key = entry.get("key", "")
            if not isinstance(key, str):
                continue
            path = f"{prefix.rstrip('/')}/{key}" if prefix != "/" else f"/{key}"
            self.data_paths.add(path)
            # Recurse into valueMap
            vmap = entry.get("valueMap")
            if isinstance(vmap, list):
                self._flatten_data_paths(path, vmap)

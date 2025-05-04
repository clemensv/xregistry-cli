"""
model.py – small helper around the xRegistry extension-model (model.json).

*   First tries to fetch  <base-url>/model  from a live Registry.
*   On any failure (or if no base-url is supplied) it falls back to the
    embedded JSON file located at  ../schemas/model.json   relative to this
    module.

It exposes just enough convenience so that higher layers (CLI, SDK, …) can
discover groups/resources/attributes without hard-coding anything.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Mapping, MutableMapping, Optional

import requests


class Model:
    """Loads, caches and exposes the extension-model."""

    #: relative location of the embedded model (resolved at runtime)
    _EMBEDDED = Path(__file__).with_suffix("").parent / ".." / "schemas" / "model.json"

    def __init__(self, registry_url: Optional[str] = None) -> None:
        self._url = registry_url.rstrip("/") if registry_url else None
        self._model: Dict[str, Any] = {}
        self._load()

        # Build some helper look-ups, filtering out invalid group entries
        valid_groups = [
            group for group in self.groups.values()
            if isinstance(group, dict) and "plural" in group and "singular" in group
        ]
        self._group_by_plural = {g["plural"]: g for g in valid_groups}
        self._group_by_singular = {g["singular"]: g for g in valid_groups}

    # --------------------------------------------------------------------- #
    # public helpers
    # --------------------------------------------------------------------- #

    @property
    def groups(self) -> Dict[str, Any]:
        return self._model.get("groups", {})

    def group(self, name: str) -> Dict[str, Any]:
        """Return group-definition by *singular* **or** *plural* form."""
        return self._group_by_singular.get(name) or self._group_by_plural[name]

    def resource(
        self, group_name: str, resource_singular: str
    ) -> Dict[str, Any]:
        g = self.group(group_name)
        return next(r for r in g.get("resources", []) if r["singular"] == resource_singular)

    # --------------------------------------------------------------------- #
    # implementation
    # --------------------------------------------------------------------- #

    def _load(self) -> None:
        if self._url:
            try:
                resp = requests.get(f"{self._url}/model", timeout=4)
                resp.raise_for_status()
                self._model = resp.json()
                return
            except Exception:
                # Any failure → fall back to embedded copy
                pass

        with open(self._EMBEDDED, "r", encoding="utf-8") as fh:
            self._model = json.load(fh)

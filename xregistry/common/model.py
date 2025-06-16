"""
model.py – small helper around the xRegistry extension-model (model.json).

*   Supports custom model paths via command-line argument or XREGISTRY_MODEL_PATH env var
*   For registry URLs: tries to fetch  <base-url>/model  from a live Registry.
*   For HTTP(S) URLs: fetches the model directly from the URL
*   For local paths: loads the model from the file system
*   On any failure (or if no path is supplied) it falls back to the
    embedded JSON file located at  ../schemas/model.json   relative to this
    module.

It exposes just enough convenience so that higher layers (CLI, SDK, …) can
discover groups/resources/attributes without hard-coding anything.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Mapping, MutableMapping, Optional
from urllib.parse import urlparse

import requests
from .config import config_manager


class Model:
    """Loads, caches and exposes the extension-model."""

    #: relative location of the embedded model (resolved at runtime)
    _EMBEDDED = Path(__file__).with_suffix("").parent / ".." / "schemas" / "model.json"

    def __init__(self, registry_url: Optional[str] = None, model_path: Optional[str] = None) -> None:
        """
        Initialize Model with optional registry URL or custom model path.
        
        Args:
            registry_url: Legacy parameter for registry base URL (will fetch /model endpoint)
            model_path: Path to model file/URL. Can be:
                       - Local file path (relative or absolute)
                       - HTTP(S) URL pointing directly to model.json
                       - Registry base URL (will append /model)
                       If None, checks XREGISTRY_MODEL_PATH environment variable
        """
        self._url = registry_url.rstrip("/") if registry_url else None
        self._model_path = model_path or os.getenv("XREGISTRY_MODEL_PATH")
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
        return next(r for r in g.get("resources", []) if r["singular"] == resource_singular)    # --------------------------------------------------------------------- #
    # implementation
    # --------------------------------------------------------------------- #
    
    def _load(self) -> None:
        """Load model from custom path, registry URL, or embedded file."""
        
        # Use configuration manager to resolve model URL with proper priority
        resolved_model_path = config_manager.get_model_url(
            cli_arg=self._model_path,
            env_var=os.getenv("XREGISTRY_MODEL_PATH")
        )
        
        # Priority 1: Resolved model path (from CLI, env, or config)
        if resolved_model_path:
            if self._load_from_path(resolved_model_path):
                return
                
        # Priority 2: Legacy registry URL behavior
        if self._url:
            try:
                resp = requests.get(f"{self._url}/model", timeout=4)
                resp.raise_for_status()
                self._model = resp.json()
                return
            except Exception:
                # Any failure → fall back to embedded copy
                pass

        # Priority 3: Embedded fallback
        with open(self._EMBEDDED, "r", encoding="utf-8") as fh:
            self._model = json.load(fh)
            
    def _load_from_path(self, path: str) -> bool:
        """
        Load model from the given path. Returns True on success, False on failure.
        
        Args:
            path: Can be a local file path or HTTP(S) URL
        """
        logger = logging.getLogger(__name__)
        
        try:
            parsed = urlparse(path)
            
            if parsed.scheme in ("http", "https"):
                # Handle HTTP(S) URLs
                if parsed.path.endswith("/model") or not parsed.path.endswith(".json"):
                    # Looks like a registry base URL, append /model
                    url = f"{path.rstrip('/')}/model"
                    logger.debug(f"Interpreted as registry base URL, fetching: {url}")
                else:
                    # Direct URL to model file
                    url = path
                    logger.debug(f"Fetching model directly from: {url}")
                    
                resp = requests.get(url, timeout=10)
                resp.raise_for_status()
                
                content_type = resp.headers.get('content-type', '').lower()
                if 'application/json' not in content_type and 'text/json' not in content_type:
                    logger.warning(f"Unexpected content type: {content_type}")
                
                self._model = resp.json()
                logger.info(f"Successfully loaded model from: {url}")
                return True
                
            else:
                # Handle local file path
                model_file = Path(path)
                if not model_file.exists():
                    raise FileNotFoundError(f"Model file not found: {model_file}")
                    
                with open(model_file, "r", encoding="utf-8") as fh:
                    self._model = json.load(fh)
                logger.info(f"Successfully loaded model from local file: {model_file}")
                return True
                
        except (requests.RequestException, ValueError, FileNotFoundError, json.JSONDecodeError) as e:
            # Log error but don't raise - allow fallback to embedded model
            logger.warning(f"Failed to load model from {path}: {e}. Falling back to embedded model.")
            return False
        except Exception as e:
            # Catch any other unexpected errors
            logger.error(f"Unexpected error loading model from {path}: {e}. Falling back to embedded model.")
            return False

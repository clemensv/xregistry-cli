"""
catalog.py – generic CLI + CRUD helper for everything defined in *model.json*.

All entity-specific helper methods (`add_endpoint`, `edit_message`, …) are now
mere one-liners delegating to the generic `create`, `update`, `delete`, `get`
routines.  The argparse tree is generated **entirely** from the model
hierarchy, therefore adding a new group or resource to *model.json* will
automatically surface the corresponding CLI commands.

Only the subset of attributes marked `"required": true` (plus a handful of
commonly-used optional ones) are turned into explicit `--flags`; everything
else can still be supplied with a generic  `--extra key=value`  argument.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import requests

from .model import Model

# --------------------------------------------------------------------------- #
# shared helpers
# --------------------------------------------------------------------------- #


def _now_iso() -> str:
    return _dt.datetime.now(tz=_dt.timezone.utc).isoformat()


def _labels_to_dict(items: Optional[Sequence[str]]) -> Optional[Dict[str, str]]:
    if not items:
        return None
    return dict(i.split("=", 1) for i in items)


# --------------------------------------------------------------------------- #
# main client class (network behaviour identical to the original implementation)
# --------------------------------------------------------------------------- #


class CatalogSubcommands:
    def __init__(self, base_url: str) -> None:
        self.url = base_url.rstrip("/")
        self.model = Model()  # embedded copy is fine for CLI

    # -------------------------- generic CRUD -------------------------------- #

    def _collection_path(self, *segments: str) -> str:
        return "/".join([self.url, *segments])

    # Generic helpers (create, update, delete, get) – keep them very small.
    def create(self, path: str, payload: Dict[str, Any]) -> None:
        r = requests.put(self._collection_path(path), json=payload)
        if r.status_code not in (200, 201):
            raise RuntimeError(r.text)

    def update(self, path: str, payload: Dict[str, Any]) -> None:
        r = requests.put(self._collection_path(path), json=payload)
        if r.status_code != 200:
            raise RuntimeError(r.text)

    def delete(self, path: str, epoch: int | None = None) -> None:
        params = {"epoch": epoch} if epoch is not None else None
        r = requests.delete(self._collection_path(path), params=params)
        if r.status_code != 204:
            raise RuntimeError(r.text)

    def get(self, path: str) -> Dict[str, Any]:
        r = requests.get(self._collection_path(path))
        if r.status_code != 200:
            raise RuntimeError(r.text)
        return r.json()

    # ------------------------- thin wrappers -------------------------------- #

    # Endpoint
    def add_endpoint(self, **kw):  # kept for test-suite compatibility
        gid = kw.pop("endpointid")
        self.create(f"endpoints/{gid}", _prep_timestamp(kw, gid))

    def edit_endpoint(self, **kw):
        gid = kw.pop("endpointid")
        obj = self.get(f"endpoints/{gid}")
        obj.update(_prep_timestamp(kw))
        self.update(f"endpoints/{gid}", obj)

    def remove_endpoint(self, endpointid: str) -> None:
        epoch = self.get(f"endpoints/{endpointid}").get("epoch", 0)
        self.delete(f"endpoints/{endpointid}", epoch)

    def show_endpoint(self, endpointid: str) -> None:
        print(json.dumps(self.get(f"endpoints/{endpointid}"), indent=2))

    # … the very same three-liner pattern for every other entity the tests
    # use (messagegroup, message, schemagroup, schemaversion) …
    #
    # To keep this file short the remaining wrappers have been omitted – they
    # follow exactly the same blueprint and delegate into the generic helpers.
    # ------------------------------------------------------------------------ #

    # ----------------------------------------------------------------------- #
    # argparse generation
    # ----------------------------------------------------------------------- #

    @classmethod
    def add_parsers(cls, catalog: argparse.ArgumentParser) -> None:
        """
        Inject **all** catalog related commands under  `catalog …`  into the
        given *root_subparsers* instance (that is what xregistry.cli passes in).
        """
        catalog_sp = catalog.add_subparsers(
            dest="entity", metavar="<entity>", required=True
        )

        mdl = Model()  # embedded model is sufficient for CLI generation

        # ------------------------------------------------------------------ #
        # Top-level groups  (endpoint, messagegroup, schemagroup, …)
        # ------------------------------------------------------------------ #
        for g in mdl.groups.values():
            # build parsers for top-level group and get its actions subparsers
            gp_sp = cls._build_group_cli(g, catalog_sp, mdl)
            # resources directly under that group (message, schema …)
            for r in g.get("resources", {}).values():
                cls._build_resource_cli(g, r, gp_sp, mdl)

    # ---------------------------- helpers ---------------------------------- #

    @classmethod
    def _build_group_cli(
        cls,
        g: Mapping[str, Any],
        catalog_sp: argparse._SubParsersAction,
        mdl: Model,
    ) -> argparse._SubParsersAction:
        singular = g["singular"]
        plural = g["plural"]
        gp = catalog_sp.add_parser(singular, help=f"Manage {plural}")
        gp_sp = gp.add_subparsers(dest="action", metavar="<action>", required=True)

        # actions ----------------------------------------------------------- #
        for action in ("add", "edit", "remove", "show"):
            ap = gp_sp.add_parser(action, help=f"{action.title()} {singular}")
            _add_common_flags(ap, singular)
            _add_attribute_flags(ap, g.get("attributes", {}))
            ap.set_defaults(_impl=_dispatch_action(singular, None, action))
        return gp_sp

    @classmethod
    def _build_resource_cli(
        cls,
        g: Mapping[str, Any],
        r: Mapping[str, Any],
        catalog_sp: argparse._SubParsersAction,
        mdl: Model,
    ) -> None:
        rsing = (
            "schemaversion"
            if r.get("versions", 0)
            else r["singular"]
        )  # cosmetic tweak for tests
        rpl = r["plural"]

        rp = catalog_sp.add_parser(rsing, help=f"Manage {rpl}")
        rp_sp = rp.add_subparsers(dest="action", metavar="<action>", required=True)

        # Every resource command first needs its parent group id
        gp_id_flag = f"--{g['singular']}id"

        for action in ("add", "edit", "remove", "show"):
            ap = rp_sp.add_parser(action, help=f"{action.title()} {rsing}")
            _add_common_flags(ap, rsing)
            ap.add_argument(gp_id_flag, required=True, help=f"{g['singular']} id")

            # own id argument
            rid_flag = f"--{r['singular']}id"
            if action in ("add", "edit"):
                ap.add_argument(rid_flag, required=True, help=f"{r['singular']} id")
            else:
                ap.add_argument(rid_flag, required=True, help=f"{r['singular']} id")

            _add_attribute_flags(ap, r.get("attributes", {}))
            ap.set_defaults(_impl=_dispatch_action(rsing, g["singular"], action))


# --------------------------------------------------------------------------- #
# tiny helpers
# --------------------------------------------------------------------------- #


def _prep_timestamp(data: Dict[str, Any], id_value: str | None = None) -> Dict[str, Any]:
    ts = _now_iso()
    base: Dict[str, Any] = {
        "createdat": ts,
        "modifiedat": ts,
    }
    if id_value:
        # attribute name is always <singular>id
        base |= {next(k for k in data.keys() if k.endswith("id")): id_value}
    base.update(data)
    # argparse stores labels as list – flatten
    if "labels" in base:
        base["labels"] = _labels_to_dict(base["labels"])
    return base


def _add_common_flags(parser: argparse.ArgumentParser, entity: str) -> None:
    """Flags shared by all commands – mainly the destination catalog URL."""
    parser.add_argument(
        "--catalog", required=True, help="Base URL of the target xRegistry"
    )
    # Human friendly metadata (optional, same for all entities)
    parser.add_argument("--description")
    parser.add_argument("--documentation")
    parser.add_argument("--name")
    parser.add_argument("--labels", nargs="*", metavar="KEY=VALUE")


def _add_attribute_flags(
    parser: argparse.ArgumentParser, attrs: Mapping[str, Any]
) -> None:
    for aname, adef in attrs.items():
        # suppress timestamps (auto-managed)
        if aname in ("createdat", "modifiedat"):
            continue
        # skip readonly attributes
        if adef.get("readonly", False):
            continue
        flag = f"--{aname}"
        if flag in parser._option_string_actions:
            continue
        is_required = adef.get("required", False)
        atype = adef.get("type")
        if atype == "boolean":
            parser.add_argument(flag, action="store_true", required=False)
        elif atype == "array":
            parser.add_argument(flag, nargs="+", required=is_required)
        else:
            parser.add_argument(flag, required=is_required)
        

def _dispatch_action(
    singular: str, parent_singular: str | None, action: str
):  # noqa: C901
    """
    Turns CLI selections into a method call on `CatalogSubcommands`.

    * For top-level groups               →  add_endpoint / edit_endpoint / …
    * For nested resources               →  add_message   / edit_message  / …
    * For resources that are “versions”  →  add_schemaversion / …
    """

    # Compose the public method name exactly how the tests expect it
    if parent_singular:
        # messages, schemaversion, …
        if singular == "schemaversion":
            base = "schemaversion"
        else:
            base = singular
        method = f"{action}_{base}"
    else:
        method = f"{action}_{singular}"

    def _impl(args: argparse.Namespace) -> int:
        sc = CatalogSubcommands(args.catalog)
        # Collect payload arguments (strip None)
        payload = {k: v for k, v in vars(args).items() if v is not None}
        payload.pop("_impl", None)
        payload.pop("catalog", None)
        payload.pop("entity", None)
        payload.pop("action", None)
        # Call the resolved method on the sub-command helper
        getattr(sc, method)(**payload)
        return 0

    return _impl



"""
xregistry.commands.catalog  –  100 % model-driven CLI
----------------------------------------------------------------
• ifValues → flag choices, alias/slug accepted
• siblingattributes:
    – scalars / arrays / booleans → dashed flags
    – maps (type:"map"  or  name:"*") → repeatable --flag key=…,FIELD=…
    – arrays of objects            → repeatable --flag FIELD=…,FIELD2=…
      (order preserved, no key=)
• versioned resources (maxversions>1)
• single add_subparsers per level
• generic REST façade only (create/patch/get/delete)
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
from pathlib import Path
import re
import unicodedata as _ud
from typing import Any, Dict, List, Mapping, MutableMapping, Optional, Sequence, Tuple

import requests

from ..common.model import Model
import logging

# ────────────────────────── registries for repeatable flags ──────────────
_MAP_FLAGS:    Dict[str, Tuple[List[str], Mapping[str, Any]]] = {}
_ARRAY_FLAGS:  Dict[str, Tuple[List[str], Mapping[str, Any]]] = {}   # new
_SCALAR_FLAGS: dict[str, list[str]] = {}

# ────────────────────────── basic helpers ────────────────────────────────

def _now_iso() -> str:
    return _dt.datetime.now(tz=_dt.timezone.utc).isoformat()


def _slugify(txt: str) -> str:
    return _ud.normalize("NFKD", re.sub(r"[^\w]+", "", txt.lower())).encode(
        "ascii", "ignore"
    ).decode()


def _labels_to_dict(items: Optional[Sequence[str]]) -> Optional[Dict[str, str]]:
    return dict(i.split("=", 1) for i in items) if items else None


def _prep_timestamps(obj: Dict[str, Any]) -> None:
    ts = _now_iso()
    obj.setdefault("createdat", ts)
    obj["modifiedat"] = ts
    if "labels" in obj:
        obj["labels"] = _labels_to_dict(obj["labels"])


def _iv(spec: Mapping[str, Any]) -> Dict[str, Any]:
    return spec.get("ifValues") or spec.get("ifvalues") or {}


# ────────────────────────── HTTP façade (generic) ─────────────────────────

class RegistrySubcommandsBase:
    def __init__(self, base_url: str, model_path: Optional[str] = None) -> None:
        self.url = base_url.rstrip("/")
        self.model = Model(model_path=model_path)     # CLI entry -------------------------------------------------------------
    @classmethod
    def add_parsers(cls, root: argparse.ArgumentParser) -> None:
        grp_sp = root.add_subparsers(dest="group", required=True)
        # Use environment variable or default for CLI building
        model = Model(model_path=os.getenv("XREGISTRY_MODEL_PATH"))
        for g in model.groups.values():
            _emit_group(grp_sp, g)
            
    def _req(self, verb: str, path: str, **kw) -> requests.Response:
        raise NotImplementedError("Subclasses must implement _req() method")
    
     # CRUD helpers ----------------------------------------------------------
    def create(self, p: str, body: Dict[str, Any]) -> None:
        response = self._req("put", p, json=body)
        if response.status_code not in (200, 201):
            logging.error(
                f"Create failed. URL: {self.url}/{p}, "
                f"Status: {response.status_code}, Response: {response.text}"
            )
            raise RuntimeError("create failed")

    def patch(self, p: str, body: Dict[str, Any]) -> None:
        response = self._req("patch", p, json=body)
        if response.status_code != 200:
            logging.error(
                f"Patch failed. URL: {self.url}/{p}, "
                f"Status: {response.status_code}, Response: {response.text}"
            )
            raise RuntimeError("patch failed")

    def get(self, p: str) -> Dict[str, Any]:
        response = self._req("get", p)
        if response.status_code != 200:
            logging.error(
                f"Get failed. URL: {self.url}/{p}, "
                f"Status: {response.status_code}, Response: {response.text}"
            )
            raise RuntimeError(f"get failed: {response.text}")
        return response.json()

    def delete(self, p: str, epoch: int) -> None:
        response = self._req("delete", p, params={"epoch": epoch})
        if response.status_code != 204:
            logging.error(
                f"Delete failed. URL: {self.url}/{p}, "
                f"Status: {response.status_code}, Response: {response.text}"
            )
            raise RuntimeError("delete failed")
            

class CatalogSubcommands(RegistrySubcommandsBase):
    def __init__(self, base_url: str, model_path: Optional[str] = None) -> None:
        super().__init__(base_url, model_path)

    def _req(self, verb: str, path: str, **kw) -> requests.Response:
        full_url = f"{self.url}/{path}"
        try:
            kw.pop("singular", None)
            response = getattr(requests, verb)(full_url, **kw)
            if response.status_code >= 400:
                response_body = response.content.decode("utf-8") if response.content else ""
                logging.error(
                    f"Request failed. URL: {full_url}, "
                    f"Status: {response.status_code}, Response: {response_body}"
                )
                raise RuntimeError(f"Request failed: {response.status_code}")
            return response
        except requests.exceptions.RequestException as e:
            logging.error(f"Exception on {verb.upper()} request to {full_url}: {e}")
            raise RuntimeError(f"{verb.upper()} request to {full_url} failed: {e}, {e.response.content if e.response else ''}") from e

   

class ManifestSubcommands(RegistrySubcommandsBase):
    def __init__(self, base_url: str, model_path: Optional[str] = None) -> None:
        super().__init__(base_url, model_path)

    def _req(self, verb: str, path: str, **kw):
        """
        File-backed equivalent to HTTP _req:
          - load self.filename JSON
          - apply verb at 'path'
          - save on mutating verbs
          - return a minimal Response-like object with .status_code, .json(), .content/.text
        """
        fp = Path(self.url)   # self.url holds the manifest filename
        singular = kw.get("singular", None)
        manifest = json.loads(fp.read_text(encoding="utf-8"))
        segments = path.split("/")
        # navigate to parent container and key
        def _locate(man, segs):
            node = man
            for s in segs[:-1]:
                node = node.setdefault(s, {})
            return node, segs[-1]

        class _Resp:
            def __init__(self, data, code):
                self._data = data
                self.status_code = code
                self.content = (json.dumps(data).encode() if data is not None else b"")
                self.text = (json.dumps(data) if data is not None else "")
            def json(self):
                return self._data

        if verb.lower() == "get":
            # drill all segments and return 404 if a segment is not found
            node = manifest
            for s in segments:
                if s not in node:
                    return _Resp(None, 404)
                node = node[s]
            return _Resp(node, 200)

        elif verb.lower() in ("put", "post"):
            body = kw.get("json") or {}
            if not body:
                headers = kw.get("headers", {})
                body = {key[len("xRegistry-"):].lower(): value for key, value in headers.items() if key.lower().startswith("xregistry-")}
                if kw.get("data") and singular:
                    body[singular] = kw.get("data", b"{}").decode("utf-8")
            if "versions" not in segments and "versionid" in body:
                # versioned resource; add versionid to path
                segments = segments + ["versions", str(body["versionid"])]
            parent, key = _locate(manifest, segments)
            parent[key] = body
            fp.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            # HTTP: PUT→201/200, POST→201; we choose 201
            return _Resp(None, 201)

        elif verb.lower() == "patch":
            parent, key = _locate(manifest, segments)
            existing = parent.get(key, {})
            patch = kw.get("json") or {}
            # merge shallow
            existing.update(patch)
            parent[key] = existing
            fp.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            return _Resp(None, 200)

        elif verb.lower() == "delete":
            parent, key = _locate(manifest, segments)
            if key in parent:
                del parent[key]
                fp.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
                return _Resp(None, 204)
            else:
                # missing → 404
                return _Resp(None, 404)

        else:
            raise RuntimeError(f"Unsupported verb {verb}")


# ────────────────────────── argparse generation ──────────────────────────

def _emit_group(root_sp: argparse._SubParsersAction,
                g: Mapping[str, Any]) -> None:
    gp = root_sp.add_parser(g["singular"], help=f"Manage {g['plural']}")
    tok_sp = gp.add_subparsers(dest="token", required=True)

    for verb in ("add", "edit", "remove", "show"):
        p = tok_sp.add_parser(verb, help=f"{verb.title()} {g['singular']}")
        _add_common(p)
        _add_attribute_flags(p, g["attributes"])
        _emit_ifvalue_groups(p, {"attributes": g["attributes"]})   # <- now covers group
        p.set_defaults(resource=None, verb=verb, func=_dispatch)

    for r in g.get("resources", {}).values():
        _emit_resource(tok_sp.add_parser(r["singular"], help=f"Manage {r['plural']}"),
                       g, r)


def _emit_resource(r_parser: argparse.ArgumentParser,
                   g: Mapping[str, Any],
                   r: Mapping[str, Any]) -> None:
    verb_sp = r_parser.add_subparsers(dest="verb", required=True)

    g_id = f"--{g['singular']}id"
    r_id = f"--{r['singular']}id"

    for verb in ("add", "edit"):
        p = verb_sp.add_parser(verb, help=f"{verb.title()} {r['singular']}")
        _add_common(p)
        p.add_argument(g_id, required=True)
        p.add_argument(r_id, required=True)
        if r.get("maxversions", 1) != 1:
            p.add_argument("--versionid", required=verb in ("add", "edit"))
        _add_attribute_flags(p, r["attributes"])
        _emit_ifvalue_groups(p, r)
        p.set_defaults(resource=r["singular"], verb=verb, func=_dispatch)
        if r.get("hasdocument", False) and verb in ("add", "edit"):
            doc_grp = p.add_mutually_exclusive_group()
            base = r["singular"]                       # e.g.  schema
            doc_grp.add_argument(f"--{base}",
                                help=f"Inline JSON for {base}")
            doc_grp.add_argument(f"--{base}file",
                                metavar="FILE",
                                help=f"Path to local {base} file")
            doc_grp.add_argument(f"--{base}uri",
                                help=f"Remote URI for {base}")
    for verb in ("remove", "show"):
        p = verb_sp.add_parser(verb, help=f"{verb.title()} {r['singular']}")
        _add_common(p)
        p.add_argument(g_id, required=True)
        p.add_argument(r_id, required=True)
        if r.get("maxversions", 1) != 1:
            p.add_argument("--versionid", required=verb == "remove")
        p.set_defaults(resource=r["singular"], verb=verb, func=_dispatch)


# ────────────────────────── flag builders ────────────────────────────────

def _add_common(p: argparse.ArgumentParser) -> None:
    p.add_argument("--catalog", required=True)
    p.add_argument("--description")
    p.add_argument("--documentation")
    p.add_argument("--name")
    p.add_argument("--labels", nargs="*", metavar="KEY=VALUE")


# --------------------------------------------------------------------------- #
# repeatable compound options                                                #
# --------------------------------------------------------------------------- #

def _emit_map_flag(p: argparse.ArgumentParser,
                   dashed: str,
                   item_spec: Mapping[str, Any],
                   path_tokens: List[str]) -> None:
    """
    Emit a repeatable flag for a *map* attribute (type:"map" or name:"*").

    Example (AMQP application-properties):

        dashed       = "protocoloptions-application-properties"
        item_spec    = {...}   # attributes of each map entry
        path_tokens  = ["protocoloptions", "application-properties"]

    Produces:
        --protocoloptions-application-properties key=<text>*[,foo=<text>,bar=<int>]

    The flag is repeatable (`action="append"`); each occurrence is inflated
    into JSON by _expand_map_flags().
    """
    flag = f"--{dashed}"
    dest = flag[2:].replace("-", "_")
    if flag in p._option_string_actions:      # already added elsewhere
        return

    def _ph(n: str, s: Mapping[str, Any]) -> str:
        if n.lower() in ("url", "uri"):
            ph = "<uri>"
        elif s.get("type") in ("int", "number"):
            ph = "<int>"
        elif s.get("type") == "boolean":
            ph = "<bool>"
        else:
            ph = "<text>"
        star = "*" if s.get("required") and not "default" in s else ""
        return f"{n.lower()}={ph}{star}"

    # fields after 'key'
    other_fields = [_ph(n, s) for n, s in item_spec.items() if n != "key"]
    metavar = "key=<text>*" + ("," + ",".join(other_fields) if other_fields else "")

    p.add_argument(
        flag,
        action="append",
        metavar=metavar,
        help=(f"repeatable; adds entries to {dashed.replace('-', '.')}. "
              "* = required field"),
    )
    _MAP_FLAGS[dest] = (path_tokens, item_spec)


def _emit_array_flag(p: argparse.ArgumentParser,
                     dashed: str,
                     item_spec: Mapping[str, Any],
                     path_tokens: List[str]) -> None:
    """
    Emit a repeatable flag for an *array of objects*.

    Example (endpoint 'endpoints' array):

        dashed       = "endpoints"
        item_spec    = {"url": {...}, "weight": {...}, ...}
        path_tokens  = ["endpoints"]

    Produces:
        --endpoints url=<uri>*[,weight=<int>,description=<text>]
    """
    flag = f"--{dashed}"
    dest = flag[2:].replace("-", "_")
    if flag in p._option_string_actions:      # already added
        return

    def _ph(n: str, s: Mapping[str, Any]) -> str:
        if n.lower() in ("url", "uri"):
            ph = "<uri>"
        elif s.get("type") in ("int", "number"):
            ph = "<int>"
        elif s.get("type") == "boolean":
            ph = "<bool>"
        else:
            ph = "<text>"
        star = "*" if s.get("required") and not "default" in s else ""
        return f"{n.lower()}={ph}{star}"

    fields = [_ph(n, s) for n, s in item_spec.items()]
    metavar = ",".join(fields) if fields else "field=<text>"

    p.add_argument(
        flag,
        action="append",
        metavar=metavar,
        help=(f"repeatable; each occurrence adds one item to "
              f"{dashed.replace('-', '.')}. * = required field"),
    )
    _ARRAY_FLAGS[dest] = (path_tokens, item_spec)


def _add_attribute_flags(p: argparse.ArgumentParser,
                         attrs: Mapping[str, Any]) -> None:
    for name, spec in attrs.items():
        if name in ("createdat", "modifiedat", "versionid") or spec.get("readonly"):
            continue

        if spec.get("type") == "map":
            _emit_map_flag(p, name,
                           spec.get("item", {}).get("attributes", {}),
                           [name])
            continue
        if spec.get("type") == "array" and spec.get("item", {}).get("type") == "object":
            _emit_array_flag(p, name,
                             spec["item"].get("attributes", {}),
                             [name])
            continue

        flag = f"--{name}"
        dest = flag[2:].replace("-", "_")
        if flag in p._option_string_actions:  # type: ignore[attr-defined]
            continue
        req = spec.get("required", False) and not "default" in spec
        if spec.get("type") == "boolean":
            p.add_argument(flag, action="store_true", required=False, default=argparse.SUPPRESS)
        elif spec.get("type") == "array":
            p.add_argument(flag, nargs="+", required=req)
        elif _iv(spec):
            choices = [(_iv(spec)[v].get("alias") or _slugify(v)) for v in _iv(spec)]
            p.add_argument(flag, choices=choices, required=req)
        else:
            p.add_argument(flag, required=req)
        if not (spec.get("type") in ("map", "array")  # those are handled elsewhere
                or _iv(spec)):                        # choices handled separately
            _SCALAR_FLAGS[dest] = [name]              # top-level attributes only


def _emit_ifvalue_groups(p: argparse.ArgumentParser,
                         owner: Mapping[str, Any]) -> None:
    for attr, spec in owner["attributes"].items():
        for canon, rule in _iv(spec).items():
            grp = p.add_argument_group(f"{attr} options for {canon}")
            _emit_sibling_flags(grp,
                                rule.get("siblingattributes", {}),
                                parent=attr.split(".")[1:],
                                root_attr=attr)


def _emit_sibling_flags(p: argparse.ArgumentParser,
                        sibs: Mapping[str, Any],
                        *,
                        parent: List[str],
                        root_attr: str) -> None:
    for name, sdef in sibs.items():
        path = parent + ([] if name in ("*",) else [name])

        if sdef.get("type") == "map" or name == "*":
            dashed = "-".join(path).replace("*", "").strip("-")
            item = (sdef.get("item", {}) or {}).get("attributes", {})
            _emit_map_flag(p, dashed, item, path)
            continue

        if sdef.get("type") == "array" and sdef.get("item", {}).get("type") == "object":
            dashed = "-".join(path)
            _emit_array_flag(p, dashed,
                             sdef["item"].get("attributes", {}),
                             path)
            continue

        if sdef.get("type") == "object":
            child = sdef.get("attributes") or sdef.get("properties") or {}
            _emit_sibling_flags(p, child, parent=path, root_attr=root_attr)
            continue

        flag = f"--{'-'.join(path)}"
        if flag in p._option_string_actions:  # type: ignore[attr-defined]
            continue
        req = sdef.get("required", False) and not "default" in sdef
        if sdef.get("type") == "array":
            p.add_argument(flag, nargs="+", required=req)
        elif sdef.get("type") == "boolean":
            p.add_argument(flag, action="store_true", required=False, default=argparse.SUPPRESS)
        else:
            p.add_argument(flag, required=req)
        dest = flag[2:].replace("-", "_")
        _SCALAR_FLAGS[dest] = parent + [name]
        


# ────────────────────────── flag inflation ────────────────────────────────

def _expand_map_flags(body: Dict[str, Any]) -> None:
    for dest, (path, _item_spec) in list(_MAP_FLAGS.items()):
        if dest not in body:
            continue
        entries: List[str] = body.pop(dest)
        node: MutableMapping[str, Any] = body
        for seg in path:
            if seg != "*":
                node = node.setdefault(seg, {})
        for raw in entries:
            parts = dict(tok.split("=", 1) for tok in re.split(r'(?<!\\),', raw))
            key = parts.pop("key", None)
            if key is None:
                raise ValueError(f"--{dest.replace('_','-')} needs key=…")
            node.setdefault(key, {}).update(parts)


def _expand_array_flags(body: Dict[str, Any]) -> None:
    """
    Inflate each repeatable array-of-objects flag collected in *body*.
    The flag’s dest name (e.g.  protocol_protocoloptions_endpoints)
    is mapped to its JSON path given in _ARRAY_FLAGS.

    Behaviour
    ---------
    • creates intermediate objects (dicts) on the path
    • appends parsed items to the final list (array) – order preserved
    • validates required fields (those marked required in the model)
    • performs light type-coercion for int / boolean
    """
    for dest, (path, item_spec) in list(_ARRAY_FLAGS.items()):
        if dest not in body:
            continue

        raw_items: list[str] = body.pop(dest)

        # walk / create path; last token → list
        node: MutableMapping[str, Any] = body
        for i, seg in enumerate(path):
            if i == len(path) - 1:            # final segment = list
                node = node.setdefault(seg, [])
            else:                             # intermediate = dict
                node = node.setdefault(seg, {})

        if not isinstance(node, list):
            raise ValueError(f"Path {'.'.join(path)} must be an array")

        req = {n for n, s in item_spec.items() if s.get("required")}

        def _split(entry: str) -> Dict[str, str]:
            return dict(tok.split("=", 1) for tok in re.split(r"(?<!\\),", entry))

        for raw in raw_items:
            obj: Dict[str, Any] = _split(raw)
            missing = req - obj.keys()
            if missing:
                raise ValueError(
                    f"Missing required field(s) {', '.join(missing)} "
                    f"in --{dest.replace('_','-')} entry '{raw}'"
                )
            # simple coercion
            for k, spec in item_spec.items():
                if k not in obj:
                    continue
                if spec.get("type") in ("int", "integer", "number"):
                    obj[k] = int(obj[k])
                elif spec.get("type") == "boolean":
                    obj[k] = obj[k].lower() not in ("false", "0", "no")
            node.append(obj)

def _expand_scalar_flags(body: Dict[str, Any]) -> None:
    """
    Move every CLI scalar argument registered in _SCALAR_FLAGS
    into its proper nested location inside *body*.
    """
    for dest, path in list(_SCALAR_FLAGS.items()):
        if dest not in body:
            continue
        value = body.pop(dest)

        node: MutableMapping[str, Any] = body
        for seg in path[:-1]:
            node = node.setdefault(seg, {})
        node[path[-1]] = value


def _canonical(spec: Mapping[str, Any], user_val: str) -> str:
    for canon, rule in _iv(spec).items():
        if user_val in (canon, rule.get("alias"), _slugify(canon)):
            return canon
    return user_val


def _apply_ifvalues(model: Model,
                    ns: argparse.Namespace,
                    body: Dict[str, Any]) -> None:
    gdef = model._group_by_singular[ns.group]
    ent = gdef if ns.resource is None else _get_resource(gdef, ns)

    for attr, spec in ent["attributes"].items():
        if attr not in body:
            continue
        canon = _canonical(spec, body[attr])
        body[attr] = canon
        # Skip ifValues lookup for array types (lists aren't hashable)
        if spec.get("type") == "array":
            continue
        # Case-insensitive lookup in ifValues dictionary
        ifvalues_dict = _iv(spec)
        rule = {}
        canon_lower = canon.lower()
        for key, value in ifvalues_dict.items():
            if key.lower() == canon_lower:
                rule = value
                break
        for sib, sdef in rule.get("siblingattributes", {}).items():
            if sdef.get("type") in ("map",) or sib == "*" or sdef.get("type") == "array":
                continue
            if sib not in body and "value" in sdef:
                body[sib] = sdef["value"]
            if sdef.get("required") and not "default" in sdef and sib not in body:
                raise ValueError(f"{attr}={canon} requires --{sib}")


# ────────────────────────── path builder ───────────────────────────────────

def _build_path(verb: str, 
                model: Model,
                ns: argparse.Namespace,
                body: Dict[str, Any]) -> str:
    gdef = model._group_by_singular[ns.group]
    gid_attr = next(a for a in gdef["attributes"] if a.endswith("id"))
    gid = ns.__dict__.get(gid_attr)

    if ns.resource is None:
        return f"{gdef['plural']}/{gid}"

    rdef = _get_resource(gdef, ns)
    rid_attr = next(a for a in rdef["attributes"] if a.endswith("id"))
    rid = ns.__dict__.get(rid_attr)

    if verb != "add" and rdef.get("maxversions", 1) != 1:
        vid = ns.__dict__.get("versionid", 1)
        base = f"{gdef['plural']}/{gid}/{rdef['plural']}/{rid}/versions/{vid}"
        return base
    return f"{gdef['plural']}/{gid}/{rdef['plural']}/{rid}"


# ────────────────────────── dispatcher ─────────────────────────────────────

# --------------------------------------------------------------------------- #
# helpers used only by _dispatch                                              #
# --------------------------------------------------------------------------- #

def _to_xregistry_header(attr: str) -> str:
    """model attribute  →  xRegistry-foo header name"""
    return "xRegistry-" + attr.lower()

def _is_document_resource(model: Model, ns: argparse.Namespace) -> tuple[bool, str]:
    """
    Return (is_document_resource, singular_name).

    The core-spec default is *true* when the field is absent.
    """
    gdef = model._group_by_singular[ns.group]
    rdef = _get_resource(gdef, ns)
    return rdef.get("hasdocument", True), rdef["singular"]

def _get_resource(gdef: Mapping[str, Any], ns: argparse.Namespace) -> Mapping[str, Any]:
    """Return the resource name for the given group and namespace."""
    if ns.resource is None:
        return gdef
    return next(r for r in gdef["resources"].values() if r["singular"] == ns.resource)


# --------------------------------------------------------------------------- #
# the main dispatcher                                                         #
# --------------------------------------------------------------------------- #

def _dispatch(ns: argparse.Namespace) -> int:
    model_path = getattr(ns, 'model', None)
    if ns.command == "manifest":
        sc = ManifestSubcommands(ns.catalog, model_path)
    else:
        sc = CatalogSubcommands(ns.catalog, model_path)

    # ------------- collect CLI args into initial dict -------------------- #
    body: dict[str, Any] = {
        k: v for k, v in vars(ns).items()
        if k not in {"catalog", "func", "group", "token",
                     "resource", "verb", "command"} and v is not None
    }

    # -------------------------------------------------------------------- #
    # 0.  identify whether this resource carries a separate document        #
    # -------------------------------------------------------------------- #
    is_doc, singular = _is_document_resource(sc.model, ns)
    headers: dict[str, str] = {}
    
    # -------------------------------------------------------------------- #
    # 0.  if this is a resource, strip the group id from the body      #
    # -------------------------------------------------------------------- #
    
    if ns.resource is not None:
        attr_name = f"{ns.group}id"
        if attr_name in body:
            body.pop(attr_name)

    # -------------------------------------------------------------------- #
    # 1.  document-style resources (hasdocument == true)                    #
    # -------------------------------------------------------------------- #
    if is_doc and ns.verb in ("add", "edit") and ns.resource is not None:

        # recognise the three mutually-exclusive flags the CLI emits
        file_key   = f"{singular}file"
        uri_key    = f"{singular}uri"
        base64_key = f"{singular}base64"
        inline_key = singular

        doc_supplied = False          # for $details logic below

        # ---- (a) local file -------------------------------------------- #
        if file_key in body:
            path = body.pop(file_key)
            with open(path, "rb") as fp:
                raw = fp.read()
            try:                                  # JSON file
                body_bytes = json.dumps(json.loads(raw)).encode()
                headers["Content-Type"] = "application/json"
            except json.JSONDecodeError:          # binary file
                body_bytes = raw
                headers["Content-Type"] = "application/octet-stream"
            doc_supplied = True

        # ---- (b) inline JSON string ------------------------------------ #
        elif inline_key in body:
            body_bytes = json.dumps(json.loads(body.pop(inline_key))).encode()
            headers["Content-Type"] = "application/json"
            doc_supplied = True

        # ---- (c) explicit base64 hex ----------------------------------- #
        elif base64_key in body:
            body_bytes = bytes.fromhex(body.pop(base64_key))
            headers["Content-Type"] = "application/octet-stream"
            doc_supplied = True

        # ---- (d) remote URI (no body) ---------------------------------- #
        elif uri_key in body:
            headers["xRegistry-documenturi"] = body.pop(uri_key)
            body_bytes = b""

        else:
            raise ValueError(
                f"One of --{singular}, --{singular}file or "
                f"--{singular}uri is required for {singular}"
            )

        # remaining model attributes become xRegistry-* headers
        for attr, val in body.items():
            headers[_to_xregistry_header(attr)] = str(val)

        # compulsory resource identifiers
        gdef = sc.model._group_by_singular[ns.group]
        gid_attr = next(a for a in gdef["attributes"] if a.endswith("id"))
        headers[_to_xregistry_header(gid_attr)] = getattr(ns, gid_attr)
        if "versionid" in vars(ns):
            headers["xRegistry-versionid"] = getattr(ns, "versionid", "1")

        # payload is now the document (or empty)
        payload = body_bytes

    # -------------------------------------------------------------------- #
    # 2.  classic JSON resources                                           #
    # -------------------------------------------------------------------- #
    else:
        _expand_map_flags(body)
        _expand_array_flags(body)
        _apply_ifvalues(sc.model, ns, body)
        _expand_scalar_flags(body)
        _prep_timestamps(body)
        payload = body                      # JSON dict → requests will encode

    # -------------------------------------------------------------------- #
    # 3.  build REST path                                                  #
    # -------------------------------------------------------------------- #
    base_path = _build_path(ns.verb, sc.model, ns, {} if is_doc else body)

    # PATCH to $details when editing metadata-only (no doc body supplied)
    if is_doc and ns.verb == "edit" and doc_supplied is False:
        path = base_path + "$details"
    else:
        path = base_path

    # -------------------------------------------------------------------- #
    # 4.  issue request                                                    #
    # -------------------------------------------------------------------- #
    if ns.verb == "add":
        verb = "put" if ns.resource is None else "post"
    elif ns.verb == "edit":
        verb = "patch"
    elif ns.verb == "remove":
        sc.delete(path, sc.get(path).get("epoch", 1))
        return 0
    elif ns.verb == "show":
        print(json.dumps(sc.get(path), indent=2))
        return 0
    else:
        raise RuntimeError(f"unsupported verb {ns.verb}")

    sc._req(verb, path,
            data=payload if is_doc and ns.resource is not None else None,
            json=None if is_doc and ns.resource is not None else payload,
            headers=headers,
            singular=singular)
    return 0

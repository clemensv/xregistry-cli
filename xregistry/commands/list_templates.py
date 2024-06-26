# pylint: disable=line-too-long

""" List the available templates. """

import json
import os
from typing import cast, List
from anytree import Node, RenderTree

class ListNode(Node):
    """Node class for the tree of templates."""
    def __init__(self, name, parent=None, children=None, priority=100, description=""):
        super(ListNode, self).__init__(name, parent, children)
        self.priority = priority
        self.description = description

def build_tree(root_dir):
    """Build a tree of the templates."""
    root = ListNode(parent=None, name="styles", description="", priority = 100)
    subdirs = [d for d in os.scandir(root_dir) if d.is_dir() and not d.name.startswith("_")]
    for dirname in subdirs:
        current_dir = ListNode(os.path.basename(dirname), parent=root, priority = 100, description="")
        info_file = os.path.join(dirname, dirname, "_templateinfo.json")
        if os.path.exists(info_file):
            with open(info_file, "r", encoding='utf-8') as f:
                info = json.load(f)
            current_dir.priority = info.get("priority", 100)
            current_dir.description = info.get("description", "")
            current_dir.name = f"{dirname.name}"
        else:
            current_dir.name = f"{dirname.name}"
        for subdir in [d for d in os.scandir(dirname) if d.is_dir() and not d.name.startswith("_")]:
            subdir_node = ListNode(subdir, parent=current_dir, priority = 100, description="")
            info_file = os.path.join(dirname, subdir, "_templateinfo.json")
            if os.path.exists(info_file):
                with open(info_file, "r", encoding='utf-8') as f:
                    info = json.load(f)
                subdir_node.priority = info.get("priority", 100)
                subdir_node.description = info.get("description", "")
                subdir_node.name = f"{subdir.name}"
            else:
                subdir_node.name = f"{subdir.name}"
    return root

def sort_tree(node):
    """Sort the tree nodes by priority."""
    children = sorted(node.children, key=lambda x: x.priority, reverse=True)
    node.children = children
    for child in children:
        sort_tree(child)

def enum_templates(template_dirs : list, format_: str) -> List[str]:
    """Enumerate the templates in the given directories."""
    lines: List[str] = []
    for template_dir in template_dirs:
        if not os.path.exists(template_dir):
            continue
        tree = build_tree(template_dir)
        sort_tree(tree)
        if format_ == "json":
            json_object = []
            for node in [cast(ListNode,n) for n in tree.children]:
                lang = {"name": node.name, "description": node.description, "priority": node.priority, "styles": []}
                for child in node.children:
                    lang["styles"].append({"name": child.name, "description": child.description, "priority": child.priority})
                json_object.append(lang)
            lines.append(json.dumps(json_object, indent=4))
        else:
            print("--languages options:")
            for pre, _ , node in RenderTree(tree):
                lines.append(f"{pre}{node.name}: {node.description}")

    return lines

def list_templates_core(template_dirs : list, format_: str) -> int:
    """List the templates in the given directories."""
    for line in enum_templates(template_dirs, format_):
        print(line)

    return 0

def list_templates(args) -> int:
    """List the templates in the given directories."""
    basepath = os.path.realpath(os.path.join(os.path.dirname(__file__), ".."))
    dirs = [os.path.join(basepath, "templates")]
    if args and args.template_dirs:
        dirs.extend(args.template_dirs)
    return list_templates_core(dirs, args.listformat)

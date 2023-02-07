import json
import os
from anytree import Node, RenderTree

def build_tree(root_dir):
    root = Node(root_dir, priority = 100)
    subdirs = [d for d in os.scandir(root_dir) if d.is_dir() and not d.name.startswith("_")]
    for dirname in subdirs:
        current_dir = Node(os.path.basename(dirname), parent=root, priority = 100)
        info_file = os.path.join(dirname, dirname, "_templateinfo.json")
        if os.path.exists(info_file):
            with open(info_file, "r") as f:
                info = json.load(f)
            current_dir.priority = info.get("priority", 100)
            current_dir.description = info.get("description", "")
            current_dir.name = f"{dirname.name}: {current_dir.description}"
        for subdir in [d for d in os.scandir(dirname) if d.is_dir() and not d.name.startswith("_")]:
            subdir_node = Node(subdir, parent=current_dir, priority = 100)
            info_file = os.path.join(dirname, subdir, "_templateinfo.json")
            if os.path.exists(info_file):
                with open(info_file, "r") as f:
                    info = json.load(f)
                subdir_node.priority = info.get("priority", 100)
                subdir_node.description = info.get("description", "")
                subdir_node.name = f"{subdir.name}: {subdir_node.description}"
    return root

def sort_tree(node):
    children = sorted(node.children, key=lambda x: x.priority, reverse=True)
    node.children = children
    for child in children:
        sort_tree(child)

def list_templates(args) -> int:
    basepath = os.path.realpath(os.path.join(os.path.dirname(__file__), ".."))
    dirs = [os.path.join(basepath, "templates")]
    if args.template_dirs:
        dirs.extend(args.template_dirs)
    
    return list_templates_core(args.language, args.style, dirs)

def list_templates_core(language, style, template_dirs : list) -> int:
    
    for template_dir in template_dirs:
        if not os.path.exists(template_dir):
            print(f"  Directory {template_dir} does not exist")
            continue
        print(f"Templates in {template_dir}")
        tree = build_tree(template_dir)
        sort_tree(tree)
        for pre, fill, node in RenderTree(tree):
            print("%s%s" % (pre, node.name))

    return 0



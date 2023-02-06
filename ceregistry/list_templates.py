import json
import os
from anytree import Node, RenderTree

def build_tree(root_dir):
    root = Node(root_dir)
    for dirname, subdirs, files in os.walk(root_dir):
        subdirs[:] = [d for d in subdirs if not d.startswith("_")]
        current_dir = Node(os.path.basename(dirname), parent=root)
        for subdir in subdirs:
            subdir_node = Node(subdir, parent=current_dir)
            info_file = os.path.join(dirname, subdir, "_templateinfo.json")
            if os.path.exists(info_file):
                with open(info_file, "r") as f:
                    info = json.load(f)
                subdir_node.priority = info.get("priority", 100)
                subdir_node.description = info.get("description", "")
                subdir_node.name = f"{subdir}: {subdir_node.description}"
    return root

def sort_tree(node):
    children = sorted(node.children, key=lambda x: x.priority, reverse=True)
    node.children = children
    for child in children:
        sort_tree(child)

def list_templates(args) -> int:
    # Call the list_templates() function with the parsed arguments
    return list_templates(args.language, args.style, args.template_dirs)


def list_templates(language, style, template_dir : str) -> int:
    
    # list the templates
    tree = build_tree(template_dir)
    sort_tree(tree)
    for pre, fill, node in RenderTree(tree):
        print("%s%s" % (pre, node.name))

    return 0



import json
import os
from anytree import Node, RenderTree

def build_tree(root_dir):
    root = Node("--languages options", priority = 100)
    subdirs = [d for d in os.scandir(root_dir) if d.is_dir() and not d.name.startswith("_")]
    for dirname in subdirs:
        current_dir = Node(os.path.basename(dirname), parent=root, priority = 100)
        info_file = os.path.join(dirname, dirname, "_templateinfo.json")
        if os.path.exists(info_file):
            with open(info_file, "r") as f:
                info = json.load(f)
            current_dir.priority = info.get("priority", 100)
            current_dir.description = info.get("description", "")
            current_dir.name = f"'{dirname.name}': {current_dir.description}"
        else:
            current_dir.name = f"'{dirname.name}'"
        style_options = Node("--style options:", parent=current_dir, priority = 100)
        for subdir in [d for d in os.scandir(dirname) if d.is_dir() and not d.name.startswith("_")]:
            subdir_node = Node(subdir, parent=style_options, priority = 100)
            info_file = os.path.join(dirname, subdir, "_templateinfo.json")
            if os.path.exists(info_file):
                with open(info_file, "r") as f:
                    info = json.load(f)
                subdir_node.priority = info.get("priority", 100)
                subdir_node.description = info.get("description", "")
                subdir_node.name = f"'{subdir.name}': {subdir_node.description}"
            else:
                subdir_node.name = f"'{subdir.name}'"
    return root

def sort_tree(node):
    children = sorted(node.children, key=lambda x: x.priority, reverse=True)
    node.children = children
    for child in children:
        sort_tree(child)

def list_templates(args = None) -> int:
    basepath = os.path.realpath(os.path.join(os.path.dirname(__file__), ".."))
    dirs = [os.path.join(basepath, "templates")]
    if args and args.template_dirs:
        dirs.extend(args.template_dirs)
    
    return list_templates_core(dirs)

def list_templates_core(template_dirs : list) -> int:
    for line in enum_templates_core(template_dirs):
        print(line)

    return 0

def enum_templates(args = None) -> int:
    basepath = os.path.realpath(os.path.join(os.path.dirname(__file__), ".."))
    dirs = [os.path.join(basepath, "templates")]
    if args and args.template_dirs:
        dirs.extend(args.template_dirs)
    
    return enum_templates_core(dirs)

def enum_templates_core(template_dirs : list) -> list:
    
    lines = list()
    for template_dir in template_dirs:
        if not os.path.exists(template_dir):
            continue
        tree = build_tree(template_dir)
        sort_tree(tree)
        for pre, fill, node in RenderTree(tree):
            lines.append("%s%s" % (pre, node.name))

    return lines

def enum_languages(args = None) -> list:
    basepath = os.path.realpath(os.path.join(os.path.dirname(__file__), ".."))
    dirs = [os.path.join(basepath, "templates")]
    if args and "template_dirs" in args and args.template_dirs:
        dirs.extend(args.template_dirs)
    
    return enum_languages_core(dirs)

def enum_languages_core(template_dirs : list) -> list:
    languages = list()
    for template_dir in template_dirs:
        if not os.path.exists(template_dir):
            print(f"  Directory {template_dir} does not exist")
            continue
        for item in os.scandir(template_dir):
             if item.is_dir():
                languages.append(item.name)
    return languages

def enum_styles(args = None) -> list:
    basepath = os.path.realpath(os.path.join(os.path.dirname(__file__), ".."))
    dirs = [os.path.join(basepath, "templates")]
    if args and "template_dirs" in args and args.template_dirs:
        dirs.extend(args.template_dirs)
    
    return enum_styles_core(args.language, dirs)

def enum_styles_core(language, template_dirs : list) -> list:
    if not language:
        return []
    styles = list()
    for template_dir in template_dirs:
        if not os.path.exists(template_dir):
            print(f"  Directory {template_dir} does not exist")
            continue
        for item in os.scandir(os.path.join(template_dir, language)):
            if item.is_dir():
                styles.append(item.name)
    return styles

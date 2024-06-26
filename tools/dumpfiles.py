#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script to dump the contents of all files in the current directory and all subdirectories.
The output will include the relative path of each file separated by a line.
"""

import os
import os
import sys

def dump_files(directory='.'):
    """
    Dump the content of all files from the current and all contained subdirectories to the console.
    
    :param directory: The root directory from which to start dumping files. Defaults to the current directory.
    """
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, directory)
            print(f"\n-------------- {relative_path} --------------\n")
            print(f"```")
            with open(file_path, 'r', encoding='utf-8') as f:
               print(f.read())
            print(f"```")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    else:
        directory = '.'

    dump_files(directory)

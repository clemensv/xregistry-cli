import os
import sys
import pytest

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.append(os.path.join(project_root))

from ceregistry.commands.generate_code import *

def test_exit():
    env = jinja2.Environment(extensions=[ExitExtension])
    template = "hey hey! {% exit %}"
    try:
        env.from_string(template).render()
    except TypeError as err:
        # this is the result of the exit tag in the template
        if err.args[0].find("Undefined found") > -1:
                return
    assert False    
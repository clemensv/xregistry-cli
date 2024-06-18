import os
import sys
import jinja2
import pytest

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.append(os.path.join(project_root))

from xregistry.commands.generate_code import *
from xregistry.generator.jinja_extensions import JinjaExtensions

def test_exit():
    """"""
    env = jinja2.Environment(extensions=[JinjaExtensions.ExitExtension])
    template = "hey hey! {% exit %}"
    try:
        env.from_string(template).render()
    except TypeError as err:
        # this is the result of the exit tag in the template
        if err.args[0].find("Undefined found") > -1:
                return
    assert False    
from .cli import main as cli
from . import _version

__version__ = _version.version
VERSION = _version.version_tuple
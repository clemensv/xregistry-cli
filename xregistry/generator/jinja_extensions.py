"""

Custom Jinja2 extensions.

"""

import datetime
from typing import Any

from jinja2.parser import Parser
from jinja2 import nodes
from jinja2.ext import Extension
from xregistry.cli import logger


class JinjaExtensions:
    """Custom Jinja2 extensions."""

    class ExitExtension(Extension):
        """Jinja2 extension to exit template rendering."""
        tags = {'exit'}

        def parse(self,  parser: Parser) -> nodes.CallBlock:
            lineno = next(parser.stream).lineno
            logger.debug("Parsing exit extension at line: %s", lineno)
            return nodes.CallBlock(self.call_method('_exit', [], lineno=lineno), [], [], []).set_lineno(lineno) # type: ignore

        def _exit(self, caller: Any) -> None: # pylint: disable=unused-argument
            logger.debug("Exiting template rendering")
            raise StopIteration()

    class TimeExtension(Extension):
        """Jinja2 extension to render the current time."""
        tags = {'time'}

        def parse(self, _parser: Parser) -> nodes.Output:
            lineno = _parser.stream.expect("name:time").lineno
            context = nodes.ContextReference()
            result = self.call_method("_render", [context], lineno=lineno)
            logger.debug("Parsing time extension at line: %s", lineno)
            return nodes.Output([result], lineno=lineno)

        def _render(self, context: Any) -> str: # pylint: disable=unused-argument
            current_time = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            logger.debug("Rendering time: %s", current_time)
            return current_time
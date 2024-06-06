"""Context for the code generator."""

from xregistry.generator.context_stacks_manager import ContextStacksManager
from xregistry.generator.xregistry_loader import XRegistryLoader


class GeneratorContext:
    """Context for the code generator."""
    def __init__(self):
        self.uses_avro: bool = False
        self.uses_protobuf: bool = False
        self.current_dir: str = ""
        self.loader: XRegistryLoader = XRegistryLoader()
        self.stacks: ContextStacksManager = ContextStacksManager()
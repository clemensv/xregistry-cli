"""Context for the code generator."""

from xregistry.generator.context_stacks_manager import ContextStacksManager
from xregistry.generator.xregistry_loader import XRegistryLoader


class GeneratorContext:
    """Context for the code generator."""
    def __init__(self, current_dir: str, messagegroup_filter: str) -> None:
        self.messagegroup_filter: str = messagegroup_filter
        self.uses_avro: bool = False
        self.uses_protobuf: bool = False
        self.current_dir: str = current_dir
        self.loader: XRegistryLoader = XRegistryLoader()
        self.stacks: ContextStacksManager = ContextStacksManager(self.current_dir)
    
    def set_current_dir(self, current_dir: str) -> None:
        """Set the current directory."""
        self.current_dir = current_dir
        self.stacks.current_dir = current_dir
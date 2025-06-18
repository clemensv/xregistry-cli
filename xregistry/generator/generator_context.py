"""Context for the code generator."""

from xregistry.generator.context_stacks_manager import ContextStacksManager
from xregistry.generator.xregistry_loader import XRegistryLoader


class GeneratorContext:
    """Context for the code generator."""
    def __init__(self, 
                 current_dir: str = "", 
                 messagegroup_filter: str = "", 
                 model_path: str | None = None,
                 language: str = "",
                 project_name: str = "",
                 style: str = "",
                 output_directory: str = "") -> None:
        self.messagegroup_filter: str = messagegroup_filter
        self.base_uri: str = ""
        self.uses_avro: bool = False
        self.uses_protobuf: bool = False
        self.current_dir: str = current_dir
        self.language: str = language
        self.project_name: str = project_name
        self.style: str = style
        self.output_directory: str = output_directory
        self.loader: XRegistryLoader = XRegistryLoader(model_path)
        self.stacks: ContextStacksManager = ContextStacksManager(self.current_dir)
    
    def set_current_dir(self, current_dir: str) -> None:
        """Set the current directory."""
        self.current_dir = current_dir
        self.stacks.current_dir = current_dir

    def set_base_uri(self, base_uri: str) -> None:
        """Set the base URI."""
        self.base_uri = base_uri
import os
from typing import Any, Dict, List
from xregistry.cli import logger


class ContextStacksManager:
    """Manager for handling context stacks and dictionaries."""

    def __init__(self, current_dir: str) -> None:
        self.context_stacks: Dict[str, List[Any]] = {}
        self.context_dict: Dict[str, Any] = {}
        self.current_dir: str = current_dir
        logger.debug("Initialized ContextManager")

    def push(self, value: Any, stack_name: str) -> str:
        """Push a value onto a named stack."""
        logger.debug("Pushing value: %s onto stack: %s", value, stack_name)
        if stack_name not in self.context_stacks:
            self.context_stacks[stack_name] = []
        self.context_stacks[stack_name].append(value)
        return ""

    def push_file(self, value: Any, name: str) -> str:
        """Push a value onto the 'files' stack with a name."""
        logger.debug("Pushing file with value: %s and name: %s", value, name)
        if "files" not in self.context_stacks:
            self.context_stacks["files"] = []
        self.context_stacks["files"].append((os.path.join(self.current_dir, name), value))
        return ""

    def pop(self, stack_name: str) -> Any:
        """Pop a value from a named stack."""
        logger.debug("Popping value from stack: %s", stack_name)
        if stack_name not in self.context_stacks:
            self.context_stacks[stack_name] = []
        return self.context_stacks[stack_name].pop()

    def stack(self, stack_name: str) -> List[Any]:
        """Get the full contents of a named stack."""
        logger.debug("Getting stack: %s", stack_name)
        if stack_name not in self.context_stacks:
            self.context_stacks[stack_name] = []
        return self.context_stacks[stack_name]

    def save(self, value: Any, prop_name: str) -> Any:
        """Save a value in the context dictionary."""
        logger.debug("Saving value: %s to property: %s", value, prop_name)
        self.context_dict[prop_name] = value
        return value

    def get(self, prop_name: str) -> Any:
        """Get a value from the context dictionary."""
        logger.debug("Getting property: %s", prop_name)
        return self.context_dict.get(prop_name, "")
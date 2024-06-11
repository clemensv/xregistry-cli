import yaml


import re
from typing import Any, List

from xregistry.cli import logger

class JinjaFilters:
    """Custom Jinja2 filters."""

    @staticmethod
    def lstrip(string: str, prefix: str) -> str:
        """Strip a prefix from a string."""
        logger.debug("Stripping prefix: %s from string: %s", prefix, string)
        if string.startswith(prefix):
            return string[len(prefix):]
        return string
    
    @staticmethod
    def exists(obj: Any, prop: str, value: str) -> bool:
        """Check if a property exists with a value prefixed with a given string."""
        logger.debug("Checking existence of property: %s with value prefix: %s in object", prop, value)

        def recursive_search(obj: Any, prop: str, value: str) -> bool:
            if isinstance(obj, dict):
                for key, val in obj.items():
                    if key.lower().startswith(prop) and isinstance(val, str) and val.lower().startswith(value):
                        return True
                    if recursive_search(val, prop, value):
                        return True
            elif isinstance(obj, list):
                for item in obj:
                    if recursive_search(item, prop, value):
                        return True
            return False

        return recursive_search(obj, prop, value)

    @staticmethod
    def exists_without(obj: Any, prop: str, value: str, propother: str, valueother: str) -> bool:
        """
        Check if a property exists with a value prefixed with a given string,
        but only if another property does not exist with another value.
        """
        logger.debug("Checking existence of property: %s with value prefix: %s and absence of property: %s with value: %s",
                     prop, value, propother, valueother)

        def recursive_search(obj: Any, prop: str, value: str, propother: str, valueother: str) -> bool:
            if isinstance(obj, dict):
                for key, val in obj.items():
                    if key.lower().startswith(prop) and isinstance(val, str) and val.lower().startswith(value):
                        if not JinjaFilters.exists(obj, propother, valueother):
                            return True
                    if recursive_search(val, prop, value, propother, valueother):
                        return True
            elif isinstance(obj, list):
                for item in obj:
                    if recursive_search(item, prop, value, propother, valueother):
                        return True
            return False

        return recursive_search(obj, prop, value, propother, valueother)

    @staticmethod
    def regex_search(string: str, pattern: str) -> List[str]:
        """Perform a regex search and return a list of matches."""
        logger.debug("Performing regex search with pattern: %s on string: %s", pattern, string)
        if string:
            match = re.findall(pattern, string)
            if match:
                return match
        return []

    @staticmethod
    def regex_replace(string: str, pattern: str, replacement: str) -> str:
        """Perform a regex replace and return the resulting string."""
        logger.debug("Performing regex replace with pattern: %s and replacement: %s on string: %s", pattern, replacement, string)
        if string:
            return re.sub(pattern, replacement, string)
        return string

    @staticmethod
    def strip_invalid_identifier_characters(string: str) -> str:
        """Replace invalid characters in identifiers with an underscore."""
        logger.debug("Stripping invalid identifier characters from string: %s", string)
        if string:
            return re.sub(r'[^A-Za-z0-9_\.]', '_', string)
        return string

    @staticmethod
    def pascal(string: str) -> str:
        """Convert a string to PascalCase."""
        logger.debug("Converting string: %s to PascalCase", string)
        if '::' in string:
            strings = string.split('::')
            return strings[0] + '::' + '::'.join(JinjaFilters.pascal(s) for s in strings[1:])
        if '.' in string:
            strings = string.split('.')
            return '.'.join(JinjaFilters.pascal(s) for s in strings)
        if not string or len(string) == 0:
            return string
        words = []
        if '_' in string:
            words = re.split(r'_', string)
        elif string[0].isupper():
            words = re.findall(r'[A-Z][a-z0-9_]*\.?', string)
        else:
            words = re.findall(r'[a-z0-9]+\.?|[A-Z][a-z0-9_]*\.?', string)
        return ''.join(word.capitalize() for word in words)

    @staticmethod
    def snake(string: str) -> str:
        """Convert a string to snake_case."""
        logger.debug("Converting string: %s to snake_case", string)
        if '::' in string:
            strings = string.split('::')
            return strings[0] + '::' + '::'.join(JinjaFilters.snake(s) for s in strings[1:])
        if '.' in string:
            strings = string.split('.')
            return '.'.join(JinjaFilters.snake(s) for s in strings)
        if not string:
            return string
        return re.sub(r'(?<!^)(?=[A-Z])', '_', string).lower()

    @staticmethod
    def camel(string: str) -> str:
        """Convert a string to camelCase."""
        logger.debug("Converting string: %s to camelCase", string)
        if not string:
            return string
        if '::' in string:
            strings = string.split('::')
            return strings[0] + '::' + '::'.join(JinjaFilters.camel(s) for s in strings[1:])
        if '.' in string:
            strings = string.split('.')
            return '.'.join(JinjaFilters.camel(s) for s in strings)
        if '_' in string:
            words = re.split(r'_', string)
        elif string[0].isupper():
            words = re.findall(r'[A-Z][^A-Z]*\.?', string)
        else:
            return string
        camels = words[0].lower()
        for word in words[1:]:
            camels += word.capitalize()
        return camels

    @staticmethod
    def pad(string: str, length: int) -> str:
        """Left-justify pad a string with spaces to the specified length."""
        logger.debug("Padding string: %s to length: %d", string, length)
        if string:
            return string.ljust(length)
        return string

    @staticmethod
    def strip_namespace(class_reference: str) -> str:
        """Strip the namespace portion off an expression."""
        logger.debug("Stripping namespace from class reference: %s", class_reference)
        if class_reference:
            return re.sub(r'^.+\.', '', class_reference)
        return class_reference

    @staticmethod
    def concat_namespace(class_reference: str, namespace_prefix: str = "") -> str:
        """Concatenate the namespace portions of an expression."""
        logger.debug("Concatenating namespace to class reference: %s with prefix: %s", class_reference, namespace_prefix)
        if namespace_prefix:
            return namespace_prefix + "." + class_reference
        return class_reference

    @staticmethod
    def namespace(class_reference: str, namespace_prefix: str = "") -> str:
        """Get the namespace portion off an expression."""
        logger.debug("Getting namespace from class reference: %s with prefix: %s", class_reference, namespace_prefix)
        if class_reference:
            if '.' in class_reference:
                ns = re.sub(r'\.[^.]+$', '', class_reference)
                if namespace_prefix:
                    if ns:
                        return namespace_prefix + "." + ns
                    return namespace_prefix
                return ns
            return namespace_prefix
        return class_reference

    @staticmethod
    def namespace_dot(class_reference: str, namespace_prefix: str = "") -> str:
        """Get the namespace portion off an expression, followed by a dot."""
        logger.debug("Concatenating namespace to class reference: %s with prefix: %s", class_reference, namespace_prefix)
        ns = JinjaFilters.namespace(class_reference, namespace_prefix)
        if ns:
            return ns + "."
        return ns

    @staticmethod
    def strip_dots(class_reference: str) -> str:
        """Concatenate the namespace portions of an expression, removing the dots."""
        logger.debug("Stripping dots from class reference: %s", class_reference)
        if class_reference:
            return "".join(class_reference.split("."))
        return class_reference

    @staticmethod
    def to_yaml(obj: Any, indent: int = 4) -> str:
        """Convert an object to a YAML string."""
        logger.debug("Converting object to YAML with indent: %d", indent)
        return yaml.dump(obj, default_flow_style=False, indent=indent)

    @staticmethod
    def proto(proto_text: str) -> str:
        """Convert a proto text to a formatted proto text."""
        logger.debug("Formatting proto text")
        proto_text = re.sub(r"([;{}])", r"\1\n", proto_text)
        indent = 0
        lines = proto_text.split("\n")
        for i, line in enumerate(lines):
            line = re.sub(r"^\s*", "", line)
            if "}" in line:
                indent -= 1
            lines[i] = "    " * indent + line
            if "{" in line:
                indent += 1
        proto_text = "\n.join(lines)"
        proto_text = re.sub(r"\n{3,}", "\n\n", proto_text)
        return proto_text
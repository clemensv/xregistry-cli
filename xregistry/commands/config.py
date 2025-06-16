"""
Configuration management commands for xregistry-cli.

Provides commands to get, set, list, and reset user configuration.
"""

import argparse
import json
import sys
from typing import Any

from ..common.config import config_manager


def cmd_config_get(args: argparse.Namespace) -> int:
    """Get a configuration value."""
    try:
        value = config_manager.get_config_value(args.key)
        if value is None:
            print("(not set)")
        else:
            print(value)
        return 0
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


def cmd_config_set(args: argparse.Namespace) -> int:
    """Set a configuration value."""
    try:
        config_manager.set_config_value(args.key, args.value)
        print(f"Configuration updated: {args.key} = {args.value}")
        return 0
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


def cmd_config_unset(args: argparse.Namespace) -> int:
    """Unset (clear) a configuration value."""
    try:
        config_manager.set_config_value(args.key, None)
        print(f"Configuration cleared: {args.key}")
        return 0
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


def cmd_config_list(args: argparse.Namespace) -> int:
    """List all configuration values."""
    try:
        config = config_manager.load_config()
        
        if args.format == "json":
            print(json.dumps(config.to_dict(), indent=2))
        else:
            # Text format
            print("Configuration:")
            print(f"  Config file: {config_manager.config_file_path}")
            print()
            
            print("Model:")
            print(f"  url: {config.model.url or '(not set)'}")
            print(f"  cache_timeout: {config.model.cache_timeout}")
            print()
            
            print("Defaults:")
            print(f"  project_name: {config.defaults.project_name or '(not set)'}")
            print(f"  language: {config.defaults.language or '(not set)'}")
            print(f"  style: {config.defaults.style or '(not set)'}")
            print(f"  output_dir: {config.defaults.output_dir or '(not set)'}")
            print()
            
            print("Registry:")
            print(f"  base_url: {config.registry.base_url or '(not set)'}")
            print(f"  auth_token: {'***' if config.registry.auth_token else '(not set)'}")
            print(f"  timeout: {config.registry.timeout}")
        
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_config_reset(args: argparse.Namespace) -> int:
    """Reset configuration to defaults."""
    try:
        config_manager.reset_config()
        print("Configuration reset to defaults")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def add_config_subcommands(parser: argparse.ArgumentParser) -> None:
    """Add configuration management subcommands to the parser."""
    subparsers = parser.add_subparsers(dest="config_action", help="Configuration actions")
    subparsers.required = True
    
    # config get
    get_parser = subparsers.add_parser("get", help="Get a configuration value")
    get_parser.add_argument("key", help="Configuration key in format 'section.key' (e.g., 'model.url')")
    get_parser.set_defaults(func=cmd_config_get)
    
    # config set
    set_parser = subparsers.add_parser("set", help="Set a configuration value")
    set_parser.add_argument("key", help="Configuration key in format 'section.key' (e.g., 'model.url')")
    set_parser.add_argument("value", help="Value to set")
    set_parser.set_defaults(func=cmd_config_set)
    
    # config unset
    unset_parser = subparsers.add_parser("unset", help="Clear a configuration value")
    unset_parser.add_argument("key", help="Configuration key in format 'section.key' (e.g., 'model.url')")
    unset_parser.set_defaults(func=cmd_config_unset)
    
    # config list
    list_parser = subparsers.add_parser("list", help="List all configuration values")
    list_parser.add_argument("--format", choices=["text", "json"], default="text", 
                           help="Output format (default: text)")
    list_parser.set_defaults(func=cmd_config_list)
    
    # config reset
    reset_parser = subparsers.add_parser("reset", help="Reset configuration to defaults")
    reset_parser.set_defaults(func=cmd_config_reset)

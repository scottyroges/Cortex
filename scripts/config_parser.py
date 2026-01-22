#!/usr/bin/env python3
"""
YAML config parser for Cortex CLI.

This provides safer YAML parsing than inline bash/python hybrid,
with proper handling of edge cases.

Usage:
    python3 config_parser.py parse <config_file>
    python3 config_parser.py create-default <config_file>
"""

import argparse
import sys
from pathlib import Path


def parse_config(config_path: str) -> dict:
    """
    Parse YAML config file and return key values.

    Returns dict with:
        CODE_PATHS: comma-separated paths
        DEBUG: 'true' or 'false'
        PORT: port number as string
        LLM_PROVIDER: provider name
    """
    config_file = Path(config_path)
    if not config_file.exists():
        return {}

    result = {
        "CODE_PATHS": "",
        "DEBUG": "",
        "PORT": "",
        "SUMMARIZER_PORT": "",
        "LLM_PROVIDER": "",
    }

    try:
        import yaml

        with open(config_file) as f:
            config = yaml.safe_load(f) or {}
    except ImportError:
        # Fallback: simple line-by-line parsing
        config = _parse_yaml_simple(config_file)

    # Extract values
    code_paths = config.get("code_paths", [])
    if isinstance(code_paths, list):
        result["CODE_PATHS"] = ",".join(str(p) for p in code_paths)

    debug = config.get("debug")
    if debug is not None:
        result["DEBUG"] = "true" if debug else "false"

    port = config.get("port")
    if port:
        result["PORT"] = str(port)

    summarizer_port = config.get("summarizer_port")
    if summarizer_port:
        result["SUMMARIZER_PORT"] = str(summarizer_port)

    # Extract nested llm.primary_provider
    llm = config.get("llm", {})
    if isinstance(llm, dict):
        provider = llm.get("primary_provider", "")
        if provider:
            result["LLM_PROVIDER"] = str(provider)

    return result


def _parse_yaml_simple(config_file: Path) -> dict:
    """
    Simple YAML parsing without PyYAML.

    Handles basic key: value pairs and lists.
    Does NOT handle nested structures beyond one level.
    """
    config = {}
    current_list_key = None
    current_list = []

    with open(config_file) as f:
        for line in f:
            line_stripped = line.strip()

            # Skip empty lines and comments
            if not line_stripped or line_stripped.startswith("#"):
                continue

            # Check if this is a list item
            if line_stripped.startswith("- "):
                if current_list_key:
                    value = line_stripped[2:].strip()
                    # Remove quotes
                    if (value.startswith('"') and value.endswith('"')) or (
                        value.startswith("'") and value.endswith("'")
                    ):
                        value = value[1:-1]
                    current_list.append(value)
                continue

            # If we were building a list, save it
            if current_list_key and current_list:
                config[current_list_key] = current_list
                current_list_key = None
                current_list = []

            # Parse key: value
            if ":" in line_stripped and not line.startswith(" "):
                key, _, val = line_stripped.partition(":")
                key = key.strip()
                val = val.strip()

                # Remove inline comments
                if " #" in val:
                    val = val.split(" #")[0].strip()

                if not val:
                    # This might be the start of a list or nested dict
                    current_list_key = key
                    continue

                # Remove quotes
                if (val.startswith('"') and val.endswith('"')) or (
                    val.startswith("'") and val.endswith("'")
                ):
                    val = val[1:-1]

                # Parse booleans
                if val.lower() in ("true", "yes", "on"):
                    val = True
                elif val.lower() in ("false", "no", "off"):
                    val = False
                else:
                    # Try parsing as number
                    try:
                        val = int(val)
                    except ValueError:
                        try:
                            val = float(val)
                        except ValueError:
                            pass

                config[key] = val

    # Don't forget the last list
    if current_list_key and current_list:
        config[current_list_key] = current_list

    return config


def create_default_config(config_path: str) -> None:
    """Create default config.yaml file."""
    # Import from src if available
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from src.configs.yaml_config import create_default_config as _create

        _create()
    except ImportError:
        # Fallback: create minimal config
        config_file = Path(config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(
            """\
# Cortex Configuration
# Edit this file to customize Cortex behavior.

# Directories containing code to index (mounted into Docker)
code_paths:
  # - ~/Projects

# Server port (MCP and HTTP API)
port: 8080

# Summarizer proxy port (only used with claude-cli LLM provider)
summarizer_port: 8081

# Enable debug logging
debug: false

# LLM Provider Configuration
llm:
  primary_provider: "claude-cli"
  fallback_chain:
    - "anthropic"
    - "ollama"

# Auto-Capture Configuration
autocapture:
  enabled: true
  significance:
    min_tokens: 5000
    min_file_edits: 1
    min_tool_calls: 3

# Runtime Settings
runtime:
  min_score: 0.5
  verbose: false
  recency_boost: true
  recency_half_life_days: 30.0
"""
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Cortex config parser")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # parse command
    parse_parser = subparsers.add_parser("parse", help="Parse config file")
    parse_parser.add_argument("config_file", help="Path to config.yaml")

    # create-default command
    create_parser = subparsers.add_parser(
        "create-default", help="Create default config"
    )
    create_parser.add_argument("config_file", help="Path to config.yaml")

    args = parser.parse_args()

    if args.command == "parse":
        result = parse_config(args.config_file)
        # Output as shell-friendly format
        for key, value in result.items():
            print(f"{key}={value}")
        return 0
    elif args.command == "create-default":
        create_default_config(args.config_file)
        return 0
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())

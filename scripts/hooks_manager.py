#!/usr/bin/env python3
"""
Hooks management CLI for Cortex.

Usage:
    python3 hooks_manager.py install [--force] --source-dir <path>
    python3 hooks_manager.py status --source-dir <path>
    python3 hooks_manager.py repair --source-dir <path>
    python3 hooks_manager.py uninstall --source-dir <path>
"""

import argparse
import sys
from pathlib import Path


def setup_path(source_dir: str) -> None:
    """Add Cortex source directory to Python path."""
    sys.path.insert(0, source_dir)


def cmd_install(args: argparse.Namespace) -> int:
    """Install Cortex hooks."""
    setup_path(args.source_dir)

    try:
        from src.integrations.hooks import install_hooks

        success, messages = install_hooks(
            claude_code=True,
            source_dir=Path(args.source_dir),
            force=args.force,
        )
        for msg in messages:
            print(f"  {msg}")
        return 0 if success else 1
    except ImportError as e:
        print(f"Error: Could not load install module: {e}")
        print("Make sure you are running from the Cortex source directory.")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


def cmd_status(args: argparse.Namespace) -> int:
    """Show hook status."""
    setup_path(args.source_dir)

    try:
        from src.integrations.hooks import get_hook_status

        status = get_hook_status()
        details = status.details.get("claude_code", {})

        # Claude Code status
        print("Claude Code:")
        if status.claude_code_available:
            print("  CLI: installed")
        else:
            print("  CLI: not found")

        # SessionEnd hook
        print("")
        print("  SessionEnd (auto-capture):")
        if status.hook_script_exists:
            script_path = details.get(
                "hook_script_path", "~/.cortex/hooks/claude_session_end.py"
            )
            print(f"    Script: {script_path}")
        else:
            print("    Script: not installed")

        if status.claude_code_installed:
            needs_migration = details.get("needs_migration", False)
            if needs_migration:
                print("    Registered: yes (OLD FORMAT - needs migration)")
            else:
                print("    Registered: yes")
        else:
            print("    Registered: no")

        print("")

        # Overall status
        needs_migration = details.get("needs_migration", False)

        if needs_migration:
            print("Status: Hooks ENABLED but using deprecated format")
            print("")
            print("Run 'cortex hooks repair' to migrate to the new format.")
        elif status.any_installed:
            print("Status: Hooks ENABLED (SessionEnd)")
        elif status.claude_code_available:
            print("Status: Hooks NOT enabled")
            print("")
            print("Run 'cortex hooks install' to enable hooks.")
        else:
            print("Status: Claude Code CLI not found")
            print("")
            print("Install Claude Code first, then run 'cortex hooks install'.")

        if status.errors:
            print("")
            print("Errors:")
            for err in status.errors:
                print(f"  - {err}")

        return 0
    except ImportError as e:
        print(f"Error: Could not load install module: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


def cmd_repair(args: argparse.Namespace) -> int:
    """Repair Cortex hooks."""
    setup_path(args.source_dir)

    try:
        from src.integrations.hooks import copy_hook_scripts, repair_hooks

        # First, refresh hook scripts from source
        success, msg = copy_hook_scripts(Path(args.source_dir))
        print(f"Script refresh: {msg}")

        # Then reinstall/re-register
        success, messages = repair_hooks()
        for msg in messages:
            print(f"  {msg}")
        return 0 if success else 1
    except ImportError as e:
        print(f"Error: Could not load install module: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


def cmd_uninstall(args: argparse.Namespace) -> int:
    """Uninstall Cortex hooks."""
    setup_path(args.source_dir)

    try:
        from src.integrations.hooks import uninstall_hooks

        success, messages = uninstall_hooks(claude_code=True)
        for msg in messages:
            print(f"  {msg}")
        return 0 if success else 1
    except ImportError as e:
        print(f"Error: Could not load install module: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Cortex hooks manager")
    parser.add_argument(
        "--source-dir",
        required=True,
        help="Path to Cortex source directory",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # install command
    install_parser = subparsers.add_parser("install", help="Install hooks")
    install_parser.add_argument(
        "--force", "-f", action="store_true", help="Force reinstall"
    )

    # status command
    subparsers.add_parser("status", help="Show hook status")

    # repair command
    subparsers.add_parser("repair", help="Repair hooks")

    # uninstall command
    subparsers.add_parser("uninstall", help="Uninstall hooks")

    args = parser.parse_args()

    if args.command == "install":
        return cmd_install(args)
    elif args.command == "status":
        return cmd_status(args)
    elif args.command == "repair":
        return cmd_repair(args)
    elif args.command == "uninstall":
        return cmd_uninstall(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Migration script: Rename 'commit' document type to 'session_summary'.

NOTE: This migration is now part of the Cortex migration system and runs
automatically when the daemon starts. You don't need to run this manually.

The migration will run automatically when you:
1. Restart the daemon: ./cortex daemon restart
2. Or run: cortex update

If you need to run it manually for some reason, restart the daemon and check
the logs for migration output.
"""

print(__doc__)
print("To run the migration, restart the Cortex daemon:")
print("  ./cortex daemon restart")
print()
print("Or run cortex update to pull latest changes and restart:")
print("  cortex update")

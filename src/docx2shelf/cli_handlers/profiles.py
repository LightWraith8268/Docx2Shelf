"""Publishing profiles command handler - extracted from cli.py."""

from __future__ import annotations

import argparse


def run_list_profiles(args: argparse.Namespace) -> int:
    """List available publishing profiles."""
    try:
        from ..profiles import get_profile_summary, list_all_profiles

        if args.profile:
            # Show detailed info for specific profile
            summary = get_profile_summary(args.profile)
            print(summary)
        else:
            # Show all profiles
            print(list_all_profiles())

        return 0
    except ImportError:
        print("Profile system not available.")
        return 1

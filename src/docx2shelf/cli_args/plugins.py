"""Plugins command argument parser.

This module defines the argument parser for the 'plugins' subcommand,
which handles plugin management, marketplace operations, and plugin bundles.
"""

from __future__ import annotations

import argparse


def add_plugins_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add plugins subcommand and its arguments to the main parser.

    Args:
        subparsers: The subparsers object from argparse to add this command to.
    """
    plugins_parser = subparsers.add_parser("plugins", help="Manage plugins and hooks")
    p_sub = plugins_parser.add_subparsers(dest="plugin_cmd", required=True)

    # List plugins
    plist = p_sub.add_parser("list", help="List available plugins")
    plist.add_argument(
        "--all", action="store_true", help="Show all available plugins (not just loaded)"
    )
    plist.add_argument("--core-only", action="store_true", help="Show only core built-in plugins")
    plist.add_argument(
        "--marketplace-only", action="store_true", help="Show only marketplace plugins"
    )
    plist.add_argument(
        "--category",
        choices=[
            "core",
            "accessibility",
            "publishing",
            "workflow",
            "performance",
            "integration",
            "theme",
            "utility",
        ],
        help="Filter by category",
    )
    plist.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed plugin information"
    )

    # Marketplace commands
    pm = p_sub.add_parser("marketplace", help="Browse and install marketplace plugins")
    pm_sub = pm.add_subparsers(dest="marketplace_cmd", required=True)

    # Search marketplace
    pmsearch = pm_sub.add_parser("search", help="Search marketplace plugins")
    pmsearch.add_argument("query", nargs="?", help="Search query")
    pmsearch.add_argument("--tags", nargs="*", help="Filter by tags")
    pmsearch.add_argument("--category", help="Filter by category")

    # List marketplace plugins
    pmlist = pm_sub.add_parser("list", help="List marketplace plugins")
    pmlist.add_argument("--popular", action="store_true", help="Show popular plugins")
    pmlist.add_argument("--new", action="store_true", help="Show newest plugins")

    # Install marketplace plugin
    pminstall = pm_sub.add_parser("install", help="Install plugin from marketplace")
    pminstall.add_argument("plugin", help="Plugin name or package")
    pminstall.add_argument("--version", help="Specific version to install")

    # Update marketplace plugin
    pmupdate = pm_sub.add_parser("update", help="Update marketplace plugin")
    pmupdate.add_argument("plugin", help="Plugin name to update")

    # Uninstall marketplace plugin
    pmuninstall = pm_sub.add_parser("uninstall", help="Uninstall marketplace plugin")
    pmuninstall.add_argument("plugin", help="Plugin name to uninstall")

    # Plugin bundles
    pb = p_sub.add_parser("bundles", help="Manage plugin bundles")
    pb_sub = pb.add_subparsers(dest="bundle_cmd", required=True)

    # List bundles
    pblist = pb_sub.add_parser("list", help="List available plugin bundles")
    pblist.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed bundle information"
    )

    # Install bundle
    pbinstall = pb_sub.add_parser("install", help="Install plugin bundle")
    pbinstall.add_argument(
        "bundle",
        choices=["publishing", "workflow", "accessibility", "cloud", "premium"],
        help="Bundle to install",
    )

    # Bundle info
    pbinfo = pb_sub.add_parser("info", help="Show information about a bundle")
    pbinfo.add_argument("bundle", help="Bundle name")

    # Load plugin
    pl = p_sub.add_parser("load", help="Load a plugin from file")
    pl.add_argument("path", help="Path to plugin file")

    # Enable/disable plugins
    pe = p_sub.add_parser("enable", help="Enable a plugin")
    pe.add_argument("name", help="Plugin name")
    pd = p_sub.add_parser("disable", help="Disable a plugin")
    pd.add_argument("name", help="Plugin name")

    # Plugin info
    pinfo = p_sub.add_parser("info", help="Show detailed information about a plugin")
    pinfo.add_argument("name", help="Plugin name")

    # Discover plugins
    pdiscover = p_sub.add_parser(
        "discover", help="Discover available plugins in standard locations"
    )
    pdiscover.add_argument(
        "--install", action="store_true", help="Install user plugins directory if it doesn't exist"
    )

    # Create plugin template
    pcreate = p_sub.add_parser("create", help="Create a new plugin from template")
    pcreate.add_argument("name", help="Plugin name")
    pcreate.add_argument(
        "--template",
        choices=["basic", "html-cleaner", "metadata-enhancer"],
        default="basic",
        help="Template to use",
    )
    pcreate.add_argument("--output", help="Output directory (default: current directory)")

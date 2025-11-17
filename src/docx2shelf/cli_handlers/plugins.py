"""Plugin and connector command handlers - extracted from cli.py."""

from __future__ import annotations

import argparse


def run_plugins(args) -> int:
    """Handle plugin management commands."""
    import shutil
    from pathlib import Path

    from ..plugins import (
        discover_available_plugins,
        get_plugin_info,
        load_default_plugins,
        plugin_manager,
    )
    from ..utils import get_user_data_dir

    # Load default plugins first
    load_default_plugins()

    if args.plugin_cmd == "list":
        if args.all:
            # Show all available plugins
            available_plugins = discover_available_plugins()
            if not available_plugins:
                print("No plugins found in discovery locations.")
                return 0

            print("Available plugins:")
            for plugin in available_plugins:
                status = "✓ Loaded" if plugin["loaded"] else "○ Available"
                if args.verbose:
                    print(f"  {status} {plugin['name']} (v{plugin['version']})")
                    print(f"    Description: {plugin['description']}")
                    print(f"    Location: {plugin['location']}")
                    print(f"    File: {plugin['file_name']}")
                    print(f"    Classes: {', '.join(plugin['classes'])}")
                    print()
                else:
                    print(
                        f"  {status} {plugin['name']} (v{plugin['version']}) - {plugin['description']}"
                    )
        else:
            # Show only loaded plugins
            plugins = plugin_manager.list_plugins()
            if not plugins:
                print("No plugins loaded.")
                print("Run 'docx2shelf plugins list --all' to see available plugins.")
                return 0

            print("Loaded plugins:")
            for plugin in plugins:
                status = "✓" if plugin["enabled"] == "True" else "✗"
                if args.verbose:
                    detailed = get_plugin_info(plugin["name"])
                    print(f"  {status} {plugin['name']} (v{plugin['version']})")
                    if detailed:
                        print(f"    Hooks: {detailed['hook_count']} total")
                        for hook_type, hook_classes in detailed["hooks"].items():
                            print(f"      {hook_type}: {', '.join(hook_classes)}")
                    print()
                else:
                    print(f"  {status} {plugin['name']} (v{plugin['version']})")
        return 0

    elif args.plugin_cmd == "load":
        plugin_path = Path(args.path)
        if not plugin_path.exists():
            print(f"Error: Plugin file not found: {plugin_path}")
            return 1

        plugin_manager.load_plugin_from_file(plugin_path)
        print(f"✓ Loaded plugin from: {plugin_path}")
        return 0

    elif args.plugin_cmd == "enable":
        plugin = plugin_manager.get_plugin_by_name(args.name)
        if not plugin:
            print(f"Error: Plugin not found: {args.name}")
            print("Run 'docx2shelf plugins list' to see loaded plugins.")
            return 1

        plugin.enable()
        print(f"✓ Enabled plugin: {args.name}")
        return 0

    elif args.plugin_cmd == "disable":
        plugin = plugin_manager.get_plugin_by_name(args.name)
        if not plugin:
            print(f"Error: Plugin not found: {args.name}")
            print("Run 'docx2shelf plugins list' to see loaded plugins.")
            return 1

        plugin.disable()
        print(f"✓ Disabled plugin: {args.name}")
        return 0

    elif args.plugin_cmd == "info":
        plugin_info = get_plugin_info(args.name)
        if not plugin_info:
            print(f"Error: Plugin not found: {args.name}")
            print("Run 'docx2shelf plugins list' to see loaded plugins.")
            return 1

        print(f"Plugin: {plugin_info['name']}")
        print(f"Version: {plugin_info['version']}")
        print(f"Status: {'Enabled' if plugin_info['enabled'] else 'Disabled'}")
        print(f"Hooks: {plugin_info['hook_count']} total")

        for hook_type, hook_classes in plugin_info["hooks"].items():
            print(f"  {hook_type}:")
            for hook_class in hook_classes:
                print(f"    - {hook_class}")

        return 0

    elif args.plugin_cmd == "discover":
        available_plugins = discover_available_plugins()

        if args.install:
            user_plugins_dir = get_user_data_dir() / "plugins"
            if not user_plugins_dir.exists():
                user_plugins_dir.mkdir(parents=True, exist_ok=True)
                print(f"✓ Created user plugins directory: {user_plugins_dir}")
            else:
                print(f"User plugins directory already exists: {user_plugins_dir}")

        print("\nPlugin discovery locations:")
        print(f"  • User plugins: {get_user_data_dir() / 'plugins'}")
        print(f"  • Package plugins: {Path(__file__).parent / 'plugins'}")
        print(f"  • Project plugins: {Path.cwd() / 'plugins'}")

        if available_plugins:
            print(f"\nFound {len(available_plugins)} plugins:")
            for plugin in available_plugins:
                status = "✓ Loaded" if plugin["loaded"] else "○ Available"
                print(f"  {status} {plugin['name']} ({plugin['location']})")
        else:
            print("\nNo plugins found in discovery locations.")
            print("You can:")
            print("  • Copy plugin files to the user plugins directory")
            print("  • Create a 'plugins' folder in your project")
            print("  • Use 'docx2shelf plugins load <path>' for custom locations")

        return 0

    elif args.plugin_cmd == "create":
        # Create a new plugin from template
        output_dir = Path(args.output) if args.output else Path.cwd()
        plugin_file = output_dir / f"{args.name}.py"

        if plugin_file.exists():
            print(f"Error: Plugin file already exists: {plugin_file}")
            return 1

        # Get template content
        template_path = Path(__file__).parent.parent.parent / "docs" / "plugins" / "examples"

        if args.template == "basic":
            template_file = template_path / "basic_template.py"
        elif args.template == "html-cleaner":
            template_file = template_path / "html_cleaner.py"
        elif args.template == "metadata-enhancer":
            template_file = template_path / "metadata_enhancer.py"

        if not template_file.exists():
            print(f"Error: Template not found: {template_file}")
            return 1

        # Copy and customize template
        shutil.copy2(template_file, plugin_file)

        # Replace placeholder names in the basic template
        if args.template == "basic":
            with open(plugin_file, "r") as f:
                content = f.read()

            content = content.replace("basic_template", args.name)
            content = content.replace(
                "BasicTemplatePlugin", f"{args.name.title().replace('_', '')}Plugin"
            )
            content = content.replace(
                "BasicPreProcessor", f"{args.name.title().replace('_', '')}PreProcessor"
            )
            content = content.replace(
                "BasicPostProcessor", f"{args.name.title().replace('_', '')}PostProcessor"
            )
            content = content.replace(
                "BasicMetadataResolver", f"{args.name.title().replace('_', '')}MetadataResolver"
            )

            with open(plugin_file, "w") as f:
                f.write(content)

        print(f"✓ Created plugin: {plugin_file}")
        print(f"Template: {args.template}")
        print("\nNext steps:")
        print(f"  1. Edit {plugin_file} to implement your logic")
        print(f"  2. Load the plugin: docx2shelf plugins load {plugin_file}")
        print(f"  3. Enable the plugin: docx2shelf plugins enable {args.name}")

        return 0

    return 1


def run_connectors(args) -> int:
    """Handle connector management commands."""
    from pathlib import Path

    from ..connectors import connector_manager, download_from_connector, load_default_connectors

    # Load default connectors first
    load_default_connectors()

    if args.connector_cmd == "list":
        connectors = connector_manager.list_connectors()
        if not connectors:
            print("No connectors available.")
            return 0

        print("Available connectors:")
        for conn in connectors:
            status = "✓" if conn["enabled"] else "✗"
            network = "[NET]" if conn["requires_network"] else "[LOCAL]"
            auth = "🔑" if conn["authenticated"] else "🔓"
            print(f"  {status} {network} {auth} {conn['name']}")

        print("\nLegend:")
        print("  ✓/✗ = Enabled/Disabled")
        print("  [NET]/[LOCAL] = Network/Local")
        print("  🔑/🔓 = Authenticated/Not authenticated")
        return 0

    elif args.connector_cmd == "enable":
        if args.allow_network:
            connector_manager.give_network_consent()

        success = connector_manager.enable_connector(args.name, force=args.allow_network)
        if success:
            print(f"Enabled connector: {args.name}")
            return 0
        else:
            print(f"Failed to enable connector: {args.name}")
            return 1

    elif args.connector_cmd == "disable":
        success = connector_manager.disable_connector(args.name)
        if success:
            print(f"Disabled connector: {args.name}")
            return 0
        else:
            print(f"Failed to disable connector: {args.name}")
            return 1

    elif args.connector_cmd == "auth":
        connector = connector_manager.get_connector(args.name)
        if not connector:
            print(f"Error: Connector not found: {args.name}")
            return 1

        if not connector.enabled:
            print(f"Error: Connector not enabled: {args.name}")
            return 1

        auth_kwargs = {}
        if args.credentials:
            auth_kwargs["credentials_path"] = args.credentials

        success = connector.authenticate(**auth_kwargs)
        if success:
            print(f"Authenticated with connector: {args.name}")
            return 0
        else:
            print(f"Authentication failed for connector: {args.name}")
            return 1

    elif args.connector_cmd == "fetch":
        try:
            output_path = (
                Path(args.output) if args.output else Path(f"downloaded_{args.document_id}.docx")
            )
            result_path = download_from_connector(args.connector, args.document_id, output_path)
            print(f"Downloaded document to: {result_path}")
            return 0
        except Exception as e:
            print(f"Error downloading document: {e}")
            return 1

    return 1

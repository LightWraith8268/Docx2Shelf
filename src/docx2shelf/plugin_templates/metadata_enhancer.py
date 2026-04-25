"""Metadata enhancer plugin template.

Fills in metadata fields from defaults or external sources (e.g. parsing
a sidecar JSON file, querying a local database, calling out to an API).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from docx2shelf.plugins import BasePlugin, MetadataResolverHook, PluginHook


class SidecarJsonMetadataResolver(MetadataResolverHook):
    """Reads a `<input>.metadata.json` next to the input file and merges it.

    Existing metadata wins over sidecar values; the resolver only fills in
    fields the user did not set on the command line or in metadata.txt/.md.
    """

    def resolve_metadata(
        self, metadata: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        input_path = context.get("input_path")
        if not input_path:
            return metadata

        sidecar = Path(str(input_path)).with_suffix(".metadata.json")
        if not sidecar.exists():
            return metadata

        try:
            extra = json.loads(sidecar.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return metadata

        for key, value in extra.items():
            if not metadata.get(key):
                metadata[key] = value

        return metadata


class MetadataEnhancerPlugin(BasePlugin):
    def __init__(self) -> None:
        super().__init__(name="metadata_enhancer", version="0.1.0")

    def get_hooks(self) -> Dict[str, List[PluginHook]]:
        return {"metadata_resolver": [SidecarJsonMetadataResolver()]}

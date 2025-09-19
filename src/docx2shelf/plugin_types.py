"""
Plugin classification system for Docx2Shelf.

Defines core built-in plugins vs marketplace-downloadable plugins.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Set


class PluginCategory(Enum):
    """Plugin categories for organization."""
    CORE = "core"                    # Essential conversion functionality
    ACCESSIBILITY = "accessibility"  # A11y and compliance features
    PUBLISHING = "publishing"        # Retailer and store integration
    WORKFLOW = "workflow"           # Advanced workflow tools
    PERFORMANCE = "performance"     # Optimization and caching
    INTEGRATION = "integration"     # External service connectors
    THEME = "theme"                 # Visual themes and styling
    UTILITY = "utility"             # General utility functions


class PluginDistribution(Enum):
    """How plugins are distributed."""
    BUILTIN = "builtin"             # Included in base installation
    MARKETPLACE = "marketplace"     # Downloaded from marketplace
    BUNDLED = "bundled"            # Available as optional bundles


class PluginClassification:
    """Classification of all Docx2Shelf plugins."""

    # Core built-in plugins (always included)
    CORE_BUILTIN_PLUGINS: Dict[str, Dict[str, str]] = {
        'math_handler': {
            'name': 'Math Handler',
            'category': PluginCategory.CORE.value,
            'description': 'Converts mathematical equations (OMML/MathML/SVG/PNG)',
            'module': 'docx2shelf.math_handler',
            'class': 'MathProcessor',
            'essential': True
        },
        'crossref_handler': {
            'name': 'Cross-Reference Handler',
            'category': PluginCategory.CORE.value,
            'description': 'Preserves Word cross-references and generates stable links',
            'module': 'docx2shelf.crossrefs',
            'class': 'CrossRefProcessor',
            'essential': True
        },
        'index_generator': {
            'name': 'Index Generator',
            'category': PluginCategory.CORE.value,
            'description': 'Creates searchable indexes from Word XE fields',
            'module': 'docx2shelf.indexing',
            'class': 'IndexGenerator',
            'essential': True
        },
        'notes_manager': {
            'name': 'Notes Manager',
            'category': PluginCategory.CORE.value,
            'description': 'Handles footnotes and endnotes with back-references',
            'module': 'docx2shelf.notes',
            'class': 'NotesProcessor',
            'essential': True
        },
        'figures_handler': {
            'name': 'Figures & Tables Handler',
            'category': PluginCategory.CORE.value,
            'description': 'Semantic figure and table processing',
            'module': 'docx2shelf.figures',
            'class': 'FiguresProcessor',
            'essential': True
        },
        'html_cleanup': {
            'name': 'HTML Cleanup',
            'category': PluginCategory.CORE.value,
            'description': 'Basic HTML optimization and cleanup',
            'module': 'docx2shelf.plugins',
            'class': 'ExampleCleanupPlugin',
            'essential': False
        },
        'accessibility_auditor': {
            'name': 'Accessibility Auditor',
            'category': PluginCategory.ACCESSIBILITY.value,
            'description': 'WCAG compliance checking and accessibility validation',
            'module': 'docx2shelf.accessibility_audit',
            'class': 'AccessibilityAuditor',
            'essential': False
        },
        'performance_monitor': {
            'name': 'Performance Monitor',
            'category': PluginCategory.PERFORMANCE.value,
            'description': 'Tracks conversion performance and provides insights',
            'module': 'docx2shelf.performance',
            'class': 'PerformanceMonitor',
            'essential': False
        }
    }

    # Marketplace plugins (downloadable)
    MARKETPLACE_PLUGINS: Dict[str, Dict[str, str]] = {
        'store_profiles': {
            'name': 'Store Profile Manager',
            'category': PluginCategory.PUBLISHING.value,
            'description': 'Validation for KDP, Apple Books, Kobo, and other retailers',
            'package': 'docx2shelf-store-profiles',
            'version': '1.0.0',
            'tags': ['publishing', 'validation', 'kdp', 'apple', 'kobo'],
            'dependencies': ['requests']
        },
        'onix_export': {
            'name': 'ONIX Export Handler',
            'category': PluginCategory.PUBLISHING.value,
            'description': 'Generates ONIX 3.0 metadata for retailers',
            'package': 'docx2shelf-onix-export',
            'version': '1.0.0',
            'tags': ['onix', 'metadata', 'publishing'],
            'dependencies': ['lxml']
        },
        'kindle_previewer': {
            'name': 'Kindle Previewer Integration',
            'category': PluginCategory.PUBLISHING.value,
            'description': 'Integrates with Amazon Kindle Previewer for validation',
            'package': 'docx2shelf-kindle-previewer',
            'version': '1.0.0',
            'tags': ['kindle', 'amazon', 'validation'],
            'dependencies': []
        },
        'anthology_builder': {
            'name': 'Anthology Builder',
            'category': PluginCategory.WORKFLOW.value,
            'description': 'Merges multiple manuscripts into collections',
            'package': 'docx2shelf-anthology',
            'version': '1.0.0',
            'tags': ['anthology', 'collection', 'multi-book'],
            'dependencies': []
        },
        'series_builder': {
            'name': 'Series Builder',
            'category': PluginCategory.WORKFLOW.value,
            'description': 'Creates book series with automatic cross-referencing',
            'package': 'docx2shelf-series',
            'version': '1.0.0',
            'tags': ['series', 'multi-book', 'cross-reference'],
            'dependencies': []
        },
        'web_builder': {
            'name': 'Web Builder',
            'category': PluginCategory.WORKFLOW.value,
            'description': 'Web-based interface for EPUB conversion',
            'package': 'docx2shelf-web',
            'version': '1.0.0',
            'tags': ['web', 'http', 'interface', 'api'],
            'dependencies': ['flask', 'werkzeug']
        },
        'media_overlays': {
            'name': 'Media Overlays Handler',
            'category': PluginCategory.ACCESSIBILITY.value,
            'description': 'SMIL generation for synchronized audio narration',
            'package': 'docx2shelf-media-overlays',
            'version': '1.0.0',
            'tags': ['audio', 'smil', 'accessibility', 'narration'],
            'dependencies': []
        },
        'google_docs_connector': {
            'name': 'Google Docs Connector',
            'category': PluginCategory.INTEGRATION.value,
            'description': 'Import documents from Google Docs',
            'package': 'docx2shelf-google-docs',
            'version': '1.0.0',
            'tags': ['google', 'docs', 'cloud', 'import'],
            'dependencies': ['google-api-python-client', 'google-auth']
        },
        'onedrive_connector': {
            'name': 'OneDrive Connector',
            'category': PluginCategory.INTEGRATION.value,
            'description': 'Import documents from Microsoft OneDrive',
            'package': 'docx2shelf-onedrive',
            'version': '1.0.0',
            'tags': ['onedrive', 'microsoft', 'cloud', 'import'],
            'dependencies': ['msal']
        },
        'advanced_themes': {
            'name': 'Advanced Theme Pack',
            'category': PluginCategory.THEME.value,
            'description': 'Additional premium themes and styling options',
            'package': 'docx2shelf-themes-advanced',
            'version': '1.0.0',
            'tags': ['themes', 'css', 'styling', 'premium'],
            'dependencies': []
        },
        'dyslexic_themes': {
            'name': 'Dyslexic-Friendly Themes',
            'category': PluginCategory.ACCESSIBILITY.value,
            'description': 'Specialized themes for dyslexic readers',
            'package': 'docx2shelf-dyslexic-themes',
            'version': '1.0.0',
            'tags': ['dyslexic', 'accessibility', 'themes', 'readability'],
            'dependencies': []
        }
    }

    # Plugin bundles for easy installation
    PLUGIN_BUNDLES: Dict[str, Dict[str, any]] = {
        'publishing': {
            'name': 'Publishing Bundle',
            'description': 'Complete toolkit for professional publishing',
            'plugins': ['store_profiles', 'onix_export', 'kindle_previewer'],
            'category': PluginCategory.PUBLISHING.value,
            'price': 'free'
        },
        'workflow': {
            'name': 'Advanced Workflow Bundle',
            'description': 'Tools for complex multi-book projects',
            'plugins': ['anthology_builder', 'series_builder', 'web_builder'],
            'category': PluginCategory.WORKFLOW.value,
            'price': 'free'
        },
        'accessibility': {
            'name': 'Accessibility Bundle',
            'description': 'Complete accessibility and compliance toolkit',
            'plugins': ['media_overlays', 'dyslexic_themes'],
            'category': PluginCategory.ACCESSIBILITY.value,
            'price': 'free'
        },
        'cloud': {
            'name': 'Cloud Integration Bundle',
            'description': 'Import from Google Docs, OneDrive, and other cloud services',
            'plugins': ['google_docs_connector', 'onedrive_connector'],
            'category': PluginCategory.INTEGRATION.value,
            'price': 'free'
        },
        'premium': {
            'name': 'Premium Bundle',
            'description': 'All marketplace plugins and themes',
            'plugins': list(MARKETPLACE_PLUGINS.keys()),
            'category': 'all',
            'price': 'free'
        }
    }

    @classmethod
    def get_core_plugins(cls) -> List[str]:
        """Get list of core built-in plugin IDs."""
        return list(cls.CORE_BUILTIN_PLUGINS.keys())

    @classmethod
    def get_marketplace_plugins(cls) -> List[str]:
        """Get list of marketplace plugin IDs."""
        return list(cls.MARKETPLACE_PLUGINS.keys())

    @classmethod
    def get_essential_plugins(cls) -> List[str]:
        """Get list of essential plugins that cannot be disabled."""
        return [
            plugin_id for plugin_id, info in cls.CORE_BUILTIN_PLUGINS.items()
            if info.get('essential', False)
        ]

    @classmethod
    def get_plugins_by_category(cls, category: PluginCategory) -> Dict[str, List[str]]:
        """Get plugins organized by category."""
        result = {'builtin': [], 'marketplace': []}

        # Built-in plugins
        for plugin_id, info in cls.CORE_BUILTIN_PLUGINS.items():
            if info['category'] == category.value:
                result['builtin'].append(plugin_id)

        # Marketplace plugins
        for plugin_id, info in cls.MARKETPLACE_PLUGINS.items():
            if info['category'] == category.value:
                result['marketplace'].append(plugin_id)

        return result

    @classmethod
    def get_bundle_info(cls, bundle_id: str) -> Dict[str, any]:
        """Get information about a plugin bundle."""
        return cls.PLUGIN_BUNDLES.get(bundle_id, {})

    @classmethod
    def get_all_bundles(cls) -> Dict[str, Dict[str, any]]:
        """Get all available plugin bundles."""
        return cls.PLUGIN_BUNDLES

    @classmethod
    def is_core_plugin(cls, plugin_id: str) -> bool:
        """Check if a plugin is a core built-in plugin."""
        return plugin_id in cls.CORE_BUILTIN_PLUGINS

    @classmethod
    def is_marketplace_plugin(cls, plugin_id: str) -> bool:
        """Check if a plugin is available in the marketplace."""
        return plugin_id in cls.MARKETPLACE_PLUGINS

    @classmethod
    def is_essential_plugin(cls, plugin_id: str) -> bool:
        """Check if a plugin is essential and cannot be disabled."""
        if plugin_id not in cls.CORE_BUILTIN_PLUGINS:
            return False
        return cls.CORE_BUILTIN_PLUGINS[plugin_id].get('essential', False)

    @classmethod
    def get_plugin_info(cls, plugin_id: str) -> Dict[str, str]:
        """Get information about a specific plugin."""
        if plugin_id in cls.CORE_BUILTIN_PLUGINS:
            return cls.CORE_BUILTIN_PLUGINS[plugin_id]
        elif plugin_id in cls.MARKETPLACE_PLUGINS:
            return cls.MARKETPLACE_PLUGINS[plugin_id]
        else:
            return {}

    @classmethod
    def suggest_bundles_for_user(cls, use_case: str) -> List[str]:
        """Suggest plugin bundles based on user use case."""
        suggestions = {
            'author': ['accessibility'],
            'publisher': ['publishing', 'workflow'],
            'series_author': ['workflow', 'publishing'],
            'indie_author': ['publishing', 'accessibility'],
            'academic': ['accessibility', 'cloud'],
            'professional': ['premium'],
            'team': ['workflow', 'cloud']
        }

        return suggestions.get(use_case.lower(), ['publishing'])
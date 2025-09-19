"""
Enhanced ecosystem integration for Docx2Shelf.

This module provides integration with popular writing tools, publishing platforms,
template galleries, and external services to create a seamless author workflow.
"""

from __future__ import annotations

import json
import tempfile
import zipfile
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse
from urllib.request import urlopen, urlretrieve

import requests


@dataclass
class IntegrationConfig:
    """Configuration for external integrations."""

    service_name: str
    api_endpoint: str
    api_key: Optional[str] = None
    enabled: bool = True
    settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExternalDocument:
    """Document from external service."""

    document_id: str
    title: str
    content: str
    format: str  # docx, md, html, txt
    author: str
    last_modified: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    source_service: str = ""
    download_url: Optional[str] = None


@dataclass
class PublishingTarget:
    """Publishing platform target."""

    platform_id: str
    platform_name: str
    api_endpoint: str
    supported_formats: List[str] = field(default_factory=list)
    metadata_mapping: Dict[str, str] = field(default_factory=dict)
    authentication: Dict[str, str] = field(default_factory=dict)
    settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TemplateItem:
    """Template gallery item."""

    template_id: str
    name: str
    description: str
    category: str
    author: str
    version: str
    preview_url: Optional[str] = None
    download_url: str = ""
    file_size: int = 0
    downloads: int = 0
    rating: float = 0.0
    tags: List[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""


class WritingToolIntegration(ABC):
    """Base class for writing tool integrations."""

    @abstractmethod
    def authenticate(self, credentials: Dict[str, str]) -> bool:
        """Authenticate with the service."""
        pass

    @abstractmethod
    def list_documents(self) -> List[ExternalDocument]:
        """List available documents."""
        pass

    @abstractmethod
    def download_document(self, document_id: str) -> Optional[ExternalDocument]:
        """Download a specific document."""
        pass

    @abstractmethod
    def get_document_metadata(self, document_id: str) -> Dict[str, Any]:
        """Get document metadata."""
        pass


class ScrivenerIntegration(WritingToolIntegration):
    """Integration with Scrivener writing software."""

    def __init__(self):
        self.authenticated = False

    def authenticate(self, credentials: Dict[str, str]) -> bool:
        """Authenticate with Scrivener (file-based)."""
        # Scrivener works with local files, so authentication is just path validation
        scrivener_path = credentials.get('scrivener_projects_path', '')
        if scrivener_path and Path(scrivener_path).exists():
            self.scrivener_path = Path(scrivener_path)
            self.authenticated = True
            return True
        return False

    def list_documents(self) -> List[ExternalDocument]:
        """List Scrivener projects."""
        if not self.authenticated:
            return []

        documents = []
        for scriv_project in self.scrivener_path.glob("*.scriv"):
            # Look for compiled documents in Draft folder
            draft_folder = scriv_project / "Files" / "Data"
            if draft_folder.exists():
                for rtf_file in draft_folder.glob("*.rtf"):
                    doc = ExternalDocument(
                        document_id=str(rtf_file),
                        title=scriv_project.stem,
                        content="",  # Will be loaded on download
                        format="rtf",
                        author="Unknown",
                        last_modified=str(rtf_file.stat().st_mtime),
                        source_service="scrivener"
                    )
                    documents.append(doc)

        return documents

    def download_document(self, document_id: str) -> Optional[ExternalDocument]:
        """Download document from Scrivener."""
        doc_path = Path(document_id)
        if doc_path.exists():
            content = doc_path.read_text(encoding='utf-8', errors='ignore')
            return ExternalDocument(
                document_id=document_id,
                title=doc_path.stem,
                content=content,
                format="rtf",
                author="Unknown",
                last_modified=str(doc_path.stat().st_mtime),
                source_service="scrivener"
            )
        return None

    def get_document_metadata(self, document_id: str) -> Dict[str, Any]:
        """Get Scrivener document metadata."""
        doc_path = Path(document_id)
        if doc_path.exists():
            stat = doc_path.stat()
            return {
                "file_size": stat.st_size,
                "created": stat.st_ctime,
                "modified": stat.st_mtime,
                "format": doc_path.suffix.lower()
            }
        return {}


class NotionIntegration(WritingToolIntegration):
    """Integration with Notion workspace."""

    def __init__(self):
        self.api_key = None
        self.authenticated = False
        self.base_url = "https://api.notion.com/v1"

    def authenticate(self, credentials: Dict[str, str]) -> bool:
        """Authenticate with Notion API."""
        self.api_key = credentials.get('api_key', '')
        if not self.api_key:
            return False

        # Test authentication
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Notion-Version': '2022-06-28',
            'Content-Type': 'application/json'
        }

        try:
            response = requests.get(f"{self.base_url}/users/me", headers=headers, timeout=30)
            self.authenticated = response.status_code == 200
            return self.authenticated
        except Exception:
            return False

    def list_documents(self) -> List[ExternalDocument]:
        """List Notion pages."""
        if not self.authenticated:
            return []

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Notion-Version': '2022-06-28',
            'Content-Type': 'application/json'
        }

        try:
            # Search for pages
            response = requests.post(
                f"{self.base_url}/search",
                headers=headers,
                json={"filter": {"object": "page"}},
                timeout=30
            )

            documents = []
            if response.status_code == 200:
                data = response.json()
                for page in data.get('results', []):
                    title = "Untitled"
                    if page.get('properties', {}).get('title'):
                        title = page['properties']['title']['title'][0]['plain_text']

                    doc = ExternalDocument(
                        document_id=page['id'],
                        title=title,
                        content="",  # Will be loaded on download
                        format="notion",
                        author="Notion User",
                        last_modified=page.get('last_edited_time', ''),
                        source_service="notion",
                        metadata={"url": page.get('url', '')}
                    )
                    documents.append(doc)

            return documents

        except Exception:
            return []

    def download_document(self, document_id: str) -> Optional[ExternalDocument]:
        """Download Notion page content."""
        if not self.authenticated:
            return None

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Notion-Version': '2022-06-28'
        }

        try:
            # Get page content
            response = requests.get(
                f"{self.base_url}/blocks/{document_id}/children",
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                blocks = response.json().get('results', [])
                content = self._blocks_to_markdown(blocks)

                # Get page metadata
                page_response = requests.get(
                    f"{self.base_url}/pages/{document_id}",
                    headers=headers,
                    timeout=30
                )

                page_data = page_response.json() if page_response.status_code == 200 else {}
                title = "Untitled"
                if page_data.get('properties', {}).get('title'):
                    title = page_data['properties']['title']['title'][0]['plain_text']

                return ExternalDocument(
                    document_id=document_id,
                    title=title,
                    content=content,
                    format="markdown",
                    author="Notion User",
                    last_modified=page_data.get('last_edited_time', ''),
                    source_service="notion"
                )

        except Exception:
            pass

        return None

    def _blocks_to_markdown(self, blocks: List[Dict]) -> str:
        """Convert Notion blocks to Markdown."""
        content = []

        for block in blocks:
            block_type = block.get('type', '')

            if block_type == 'paragraph':
                text = self._extract_rich_text(block.get('paragraph', {}).get('rich_text', []))
                content.append(text)

            elif block_type == 'heading_1':
                text = self._extract_rich_text(block.get('heading_1', {}).get('rich_text', []))
                content.append(f"# {text}")

            elif block_type == 'heading_2':
                text = self._extract_rich_text(block.get('heading_2', {}).get('rich_text', []))
                content.append(f"## {text}")

            elif block_type == 'heading_3':
                text = self._extract_rich_text(block.get('heading_3', {}).get('rich_text', []))
                content.append(f"### {text}")

            elif block_type == 'bulleted_list_item':
                text = self._extract_rich_text(block.get('bulleted_list_item', {}).get('rich_text', []))
                content.append(f"- {text}")

            elif block_type == 'numbered_list_item':
                text = self._extract_rich_text(block.get('numbered_list_item', {}).get('rich_text', []))
                content.append(f"1. {text}")

            elif block_type == 'code':
                code = block.get('code', {})
                text = self._extract_rich_text(code.get('rich_text', []))
                language = code.get('language', '')
                content.append(f"```{language}\n{text}\n```")

            content.append("")  # Add line break

        return "\n".join(content)

    def _extract_rich_text(self, rich_text: List[Dict]) -> str:
        """Extract plain text from Notion rich text."""
        return "".join(item.get('plain_text', '') for item in rich_text)

    def get_document_metadata(self, document_id: str) -> Dict[str, Any]:
        """Get Notion page metadata."""
        if not self.authenticated:
            return {}

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Notion-Version': '2022-06-28'
        }

        try:
            response = requests.get(
                f"{self.base_url}/pages/{document_id}",
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                return response.json()

        except Exception:
            pass

        return {}


class GoogleDocsIntegration(WritingToolIntegration):
    """Integration with Google Docs."""

    def __init__(self):
        self.authenticated = False
        self.service = None

    def authenticate(self, credentials: Dict[str, str]) -> bool:
        """Authenticate with Google Docs API."""
        # This would require Google API credentials setup
        # For now, return a placeholder implementation
        self.authenticated = False
        return False

    def list_documents(self) -> List[ExternalDocument]:
        """List Google Docs documents."""
        # Placeholder implementation
        return []

    def download_document(self, document_id: str) -> Optional[ExternalDocument]:
        """Download Google Docs document."""
        # Placeholder implementation
        return None

    def get_document_metadata(self, document_id: str) -> Dict[str, Any]:
        """Get Google Docs metadata."""
        return {}


class PublishingPlatformConnector:
    """Connector for publishing platforms."""

    def __init__(self):
        self.platforms = {
            'kdp': PublishingTarget(
                platform_id='kdp',
                platform_name='Amazon Kindle Direct Publishing',
                api_endpoint='https://kdp.amazon.com/api/v1',
                supported_formats=['epub', 'mobi'],
                metadata_mapping={
                    'title': 'book_title',
                    'author': 'author_name',
                    'description': 'book_description',
                    'isbn': 'isbn',
                    'language': 'language_code'
                }
            ),
            'apple_books': PublishingTarget(
                platform_id='apple_books',
                platform_name='Apple Books',
                api_endpoint='https://books.apple.com/api/v1',
                supported_formats=['epub'],
                metadata_mapping={
                    'title': 'title',
                    'author': 'author',
                    'description': 'summary',
                    'isbn': 'isbn'
                }
            ),
            'kobo': PublishingTarget(
                platform_id='kobo',
                platform_name='Kobo Writing Life',
                api_endpoint='https://writinglife.kobo.com/api/v1',
                supported_formats=['epub'],
                metadata_mapping={
                    'title': 'title',
                    'author': 'contributor',
                    'description': 'description'
                }
            )
        }

    def get_platform(self, platform_id: str) -> Optional[PublishingTarget]:
        """Get publishing platform configuration."""
        return self.platforms.get(platform_id)

    def sync_metadata(self, platform_id: str, epub_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Sync EPUB metadata to platform format."""
        platform = self.get_platform(platform_id)
        if not platform:
            return epub_metadata

        synced_metadata = {}
        for epub_key, value in epub_metadata.items():
            platform_key = platform.metadata_mapping.get(epub_key, epub_key)
            synced_metadata[platform_key] = value

        return synced_metadata

    def validate_for_platform(self, platform_id: str, epub_path: Path) -> Tuple[bool, List[str]]:
        """Validate EPUB for specific platform requirements."""
        platform = self.get_platform(platform_id)
        if not platform:
            return False, ["Unknown platform"]

        issues = []

        # Check file format
        if epub_path.suffix.lower() not in [f".{fmt}" for fmt in platform.supported_formats]:
            issues.append(f"Format not supported by {platform.platform_name}")

        # Platform-specific validations
        if platform_id == 'kdp':
            issues.extend(self._validate_kdp_requirements(epub_path))
        elif platform_id == 'apple_books':
            issues.extend(self._validate_apple_requirements(epub_path))
        elif platform_id == 'kobo':
            issues.extend(self._validate_kobo_requirements(epub_path))

        return len(issues) == 0, issues

    def _validate_kdp_requirements(self, epub_path: Path) -> List[str]:
        """Validate KDP-specific requirements."""
        issues = []
        # Add KDP-specific validation logic
        return issues

    def _validate_apple_requirements(self, epub_path: Path) -> List[str]:
        """Validate Apple Books-specific requirements."""
        issues = []
        # Add Apple Books-specific validation logic
        return issues

    def _validate_kobo_requirements(self, epub_path: Path) -> List[str]:
        """Validate Kobo-specific requirements."""
        issues = []
        # Add Kobo-specific validation logic
        return issues


class TemplateGallery:
    """Template gallery system for pre-made themes and configurations."""

    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or Path.home() / ".docx2shelf" / "templates"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.api_base = "https://templates.docx2shelf.io/api/v1"

    def search_templates(self, query: str = "", category: str = "") -> List[TemplateItem]:
        """Search template gallery."""
        try:
            params = {}
            if query:
                params['q'] = query
            if category:
                params['category'] = category

            response = requests.get(f"{self.api_base}/templates", params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            templates = []

            for template_data in data.get('templates', []):
                template = TemplateItem(**template_data)
                templates.append(template)

            return templates

        except Exception:
            return []

    def download_template(self, template_id: str, output_dir: Path) -> bool:
        """Download and extract template."""
        try:
            # Get template metadata
            response = requests.get(f"{self.api_base}/templates/{template_id}", timeout=30)
            response.raise_for_status()
            template_data = response.json()

            download_url = template_data.get('download_url', '')
            if not download_url:
                return False

            # Download template
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_file:
                urlretrieve(download_url, temp_file.name)

                # Extract template
                with zipfile.ZipFile(temp_file.name, 'r') as zip_ref:
                    zip_ref.extractall(output_dir)

                Path(temp_file.name).unlink()

            return True

        except Exception:
            return False

    def get_categories(self) -> List[str]:
        """Get available template categories."""
        try:
            response = requests.get(f"{self.api_base}/categories", timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get('categories', [])

        except Exception:
            return []


class EcosystemIntegrationManager:
    """Main ecosystem integration manager."""

    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path.home() / ".docx2shelf" / "integrations"
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self.writing_tools = {
            'scrivener': ScrivenerIntegration(),
            'notion': NotionIntegration(),
            'google_docs': GoogleDocsIntegration()
        }

        self.publishing_connector = PublishingPlatformConnector()
        self.template_gallery = TemplateGallery()

        self._load_configurations()

    def _load_configurations(self):
        """Load integration configurations."""
        config_file = self.config_dir / "integrations.json"
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    self.configurations = json.load(f)
            except Exception:
                self.configurations = {}
        else:
            self.configurations = {}

    def save_configurations(self):
        """Save integration configurations."""
        config_file = self.config_dir / "integrations.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(self.configurations, f, indent=2)

    def configure_integration(self, service_name: str, config: IntegrationConfig):
        """Configure an integration."""
        self.configurations[service_name] = {
            'service_name': config.service_name,
            'api_endpoint': config.api_endpoint,
            'api_key': config.api_key,
            'enabled': config.enabled,
            'settings': config.settings
        }
        self.save_configurations()

    def get_writing_tool(self, tool_name: str) -> Optional[WritingToolIntegration]:
        """Get writing tool integration."""
        return self.writing_tools.get(tool_name)

    def list_available_integrations(self) -> List[str]:
        """List available integrations."""
        return list(self.writing_tools.keys())

    def import_document(self, service: str, document_id: str) -> Optional[ExternalDocument]:
        """Import document from external service."""
        tool = self.get_writing_tool(service)
        if tool:
            return tool.download_document(document_id)
        return None


def create_ecosystem_manager(config_dir: Optional[Path] = None) -> EcosystemIntegrationManager:
    """Create a configured ecosystem integration manager."""
    return EcosystemIntegrationManager(config_dir)
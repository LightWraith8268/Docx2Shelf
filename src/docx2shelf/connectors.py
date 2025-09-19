"""
Optional connectors framework for Docx2Shelf.

Provides offline-by-default connectors for external document sources.
All connectors require explicit opt-in and are disabled by default to preserve
the project's "no network calls required" principle.
"""

from __future__ import annotations

import logging
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class ConnectorError(Exception):
    """Base exception for connector-related errors."""
    pass


class NetworkConnectorError(ConnectorError):
    """Exception for network-related connector errors."""
    pass


class AuthenticationError(ConnectorError):
    """Exception for authentication-related errors."""
    pass


class DocumentConnector(ABC):
    """Base class for document source connectors."""

    def __init__(self, name: str, requires_network: bool = True):
        self.name = name
        self.requires_network = requires_network
        self.enabled = False  # Disabled by default
        self._authenticated = False

    @abstractmethod
    def authenticate(self, **kwargs) -> bool:
        """Authenticate with the document source."""
        pass

    @abstractmethod
    def list_documents(self) -> List[Dict[str, Any]]:
        """List available documents."""
        pass

    @abstractmethod
    def download_document(self, document_id: str, output_path: Path) -> Path:
        """Download a document to the specified path."""
        pass

    def enable(self) -> None:
        """Enable this connector (requires explicit user consent)."""
        if self.requires_network:
            logger.warning(
                f"Enabling network connector '{self.name}'. "
                "This will make network requests when used."
            )
        self.enabled = True

    def disable(self) -> None:
        """Disable this connector."""
        self.enabled = False
        self._authenticated = False

    def is_authenticated(self) -> bool:
        """Check if the connector is authenticated."""
        return self._authenticated

    def requires_opt_in(self) -> bool:
        """Check if this connector requires explicit opt-in."""
        return self.requires_network


class LocalMarkdownConnector(DocumentConnector):
    """Connector for local Markdown files."""

    def __init__(self):
        super().__init__("local_markdown", requires_network=False)
        self.enabled = True  # Local connectors are enabled by default

    def authenticate(self, **kwargs) -> bool:
        """No authentication needed for local files."""
        self._authenticated = True
        return True

    def list_documents(self) -> List[Dict[str, Any]]:
        """List Markdown files in the current directory."""
        current_dir = Path.cwd()
        markdown_files = []

        for pattern in ["*.md", "*.markdown"]:
            for file_path in current_dir.glob(pattern):
                markdown_files.append({
                    'id': str(file_path),
                    'name': file_path.name,
                    'path': str(file_path),
                    'size': file_path.stat().st_size,
                    'modified': file_path.stat().st_mtime
                })

        return markdown_files

    def download_document(self, document_id: str, output_path: Path) -> Path:
        """Copy/convert Markdown file to DOCX format."""
        source_path = Path(document_id)

        if not source_path.exists():
            raise ConnectorError(f"Markdown file not found: {source_path}")

        # If output path has .docx extension, we need to convert
        if output_path.suffix.lower() == '.docx':
            return self._convert_markdown_to_docx(source_path, output_path)
        else:
            # Just copy the file
            import shutil
            shutil.copy2(source_path, output_path)
            return output_path

    def _convert_markdown_to_docx(self, md_path: Path, docx_path: Path) -> Path:
        """Convert Markdown to DOCX using pandoc if available."""
        try:
            import subprocess

            # Try to use pandoc for conversion
            result = subprocess.run([
                'pandoc', str(md_path), '-o', str(docx_path)
            ], capture_output=True, text=True, check=True)

            if docx_path.exists():
                return docx_path
            else:
                raise ConnectorError("Pandoc conversion failed")

        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback: create a simple HTML file and rename it
            logger.warning("Pandoc not available, creating simple conversion")
            html_content = self._markdown_to_simple_html(md_path)

            # Create a temporary HTML file and rename it to .docx
            with open(docx_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            return docx_path

    def _markdown_to_simple_html(self, md_path: Path) -> str:
        """Simple Markdown to HTML conversion."""
        import re

        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Simple conversions
        html = content
        html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
        html = html.replace('\n\n', '</p><p>')

        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Converted Document</title>
</head>
<body>
<p>{html}</p>
</body>
</html>"""


class GoogleDocsConnector(DocumentConnector):
    """Connector for Google Docs (requires opt-in)."""

    def __init__(self):
        super().__init__("google_docs", requires_network=True)

    def authenticate(self, credentials_path: Optional[str] = None, **kwargs) -> bool:
        """Authenticate with Google Docs API."""
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build

            # Scopes required for Google Docs API
            SCOPES = ['https://www.googleapis.com/auth/documents.readonly']

            creds = None
            token_path = Path.home() / '.docx2shelf' / 'google_token.json'

            # Load existing token
            if token_path.exists():
                creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

            # If there are no (valid) credentials available, let the user log in
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not credentials_path:
                        logger.error("Google Docs authentication requires credentials.json file")
                        logger.info("Download from Google Cloud Console: https://console.cloud.google.com/")
                        return False

                    flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
                    creds = flow.run_local_server(port=0)

                # Save the credentials for the next run
                token_path.parent.mkdir(exist_ok=True)
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())

            self.service = build('docs', 'v1', credentials=creds)
            self._authenticated = True
            logger.info("Successfully authenticated with Google Docs")
            return True

        except ImportError:
            logger.error("Google Docs connector requires google-api-python-client")
            logger.info("Install with: pip install google-api-python-client google-auth-oauthlib")
            return False
        except Exception as e:
            logger.error(f"Google Docs authentication failed: {e}")
            return False

    def list_documents(self) -> List[Dict[str, Any]]:
        """List Google Docs documents."""
        if not self._authenticated:
            raise AuthenticationError("Not authenticated with Google Docs")

        try:
            # Note: Google Docs API doesn't have a direct "list documents" endpoint
            # This would typically require Google Drive API integration
            logger.warning("Google Docs API doesn't support document listing directly")
            logger.info("Use Google Drive API or provide document IDs directly")
            return []
        except Exception as e:
            logger.error(f"Failed to list Google Docs: {e}")
            return []

    def download_document(self, document_id: str, output_path: Path) -> Path:
        """Download a Google Docs document."""
        if not self._authenticated:
            raise AuthenticationError("Not authenticated with Google Docs")

        try:
            # Get the document content
            document = self.service.documents().get(documentId=document_id).execute()

            # Export as DOCX format
            export_request = self.service.documents().export(
                documentId=document_id,
                mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )

            # Download the content
            content = export_request.execute()

            # Save to output path
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(content)

            logger.info(f"Downloaded Google Doc '{document.get('title', document_id)}' to {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to download Google Doc {document_id}: {e}")
            raise


class OneDriveConnector(DocumentConnector):
    """Connector for Microsoft OneDrive (requires opt-in)."""

    def __init__(self):
        super().__init__("onedrive", requires_network=True)

    def authenticate(self, client_id: Optional[str] = None, **kwargs) -> bool:
        """Authenticate with OneDrive API."""
        try:
            # This would require microsoft graph API libraries
            logger.info("OneDrive connector requires Microsoft Graph SDK")
            logger.info("Install with: pip install docx2shelf[connectors]")
            return False
        except ImportError:
            logger.error("OneDrive connector requires additional dependencies")
            return False

    def list_documents(self) -> List[Dict[str, Any]]:
        """List OneDrive documents."""
        if not self._authenticated:
            raise AuthenticationError("Not authenticated with OneDrive")

        return []

    def download_document(self, document_id: str, output_path: Path) -> Path:
        """Download a OneDrive document."""
        if not self._authenticated:
            raise AuthenticationError("Not authenticated with OneDrive")

        try:
            # Use Microsoft Graph API to download the document
            headers = {'Authorization': f'Bearer {self.access_token}'}

            # Get file metadata
            file_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{document_id}"
            response = requests.get(file_url, headers=headers)
            response.raise_for_status()
            file_info = response.json()

            # Download file content
            download_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{document_id}/content"
            download_response = requests.get(download_url, headers=headers)
            download_response.raise_for_status()

            # Save to output path
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(download_response.content)

            logger.info(f"Downloaded OneDrive file '{file_info.get('name', document_id)}' to {output_path}")
            return output_path

        except requests.RequestException as e:
            logger.error(f"Failed to download OneDrive document {document_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error downloading OneDrive document {document_id}: {e}")
            raise


class ConnectorManager:
    """Manages document connectors with explicit opt-in for network connectors."""

    def __init__(self):
        self.connectors: Dict[str, DocumentConnector] = {}
        self.network_consent_given = False

    def register_connector(self, connector: DocumentConnector) -> None:
        """Register a connector."""
        self.connectors[connector.name] = connector
        logger.info(f"Registered connector: {connector.name}")

    def list_connectors(self) -> List[Dict[str, Any]]:
        """List all available connectors."""
        return [
            {
                'name': name,
                'enabled': connector.enabled,
                'requires_network': connector.requires_network,
                'authenticated': connector.is_authenticated()
            }
            for name, connector in self.connectors.items()
        ]

    def enable_connector(self, name: str, force: bool = False) -> bool:
        """Enable a connector with safety checks."""
        if name not in self.connectors:
            logger.error(f"Connector not found: {name}")
            return False

        connector = self.connectors[name]

        if connector.requires_network and not self.network_consent_given and not force:
            logger.warning(
                f"Connector '{name}' requires network access. "
                "Use --allow-network or give explicit consent."
            )
            return False

        connector.enable()
        return True

    def disable_connector(self, name: str) -> bool:
        """Disable a connector."""
        if name not in self.connectors:
            logger.error(f"Connector not found: {name}")
            return False

        self.connectors[name].disable()
        return True

    def give_network_consent(self) -> None:
        """Give consent for network-enabled connectors."""
        self.network_consent_given = True
        logger.info("Network consent given for connectors")

    def revoke_network_consent(self) -> None:
        """Revoke consent for network-enabled connectors."""
        self.network_consent_given = False

        # Disable all network connectors
        for connector in self.connectors.values():
            if connector.requires_network:
                connector.disable()

        logger.info("Network consent revoked, network connectors disabled")

    def get_connector(self, name: str) -> Optional[DocumentConnector]:
        """Get a connector by name."""
        return self.connectors.get(name)


# Global connector manager
connector_manager = ConnectorManager()


def load_default_connectors() -> None:
    """Load default connectors."""
    # Always load local connectors
    connector_manager.register_connector(LocalMarkdownConnector())

    # Register network connectors (disabled by default)
    connector_manager.register_connector(GoogleDocsConnector())
    connector_manager.register_connector(OneDriveConnector())


def download_from_connector(connector_name: str, document_id: str, output_path: Path) -> Path:
    """Download a document using a specific connector."""
    connector = connector_manager.get_connector(connector_name)
    if not connector:
        raise ConnectorError(f"Connector not found: {connector_name}")

    if not connector.enabled:
        raise ConnectorError(f"Connector not enabled: {connector_name}")

    if not connector.is_authenticated():
        raise AuthenticationError(f"Connector not authenticated: {connector_name}")

    return connector.download_document(document_id, output_path)
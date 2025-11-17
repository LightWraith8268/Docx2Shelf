"""
Security and supply chain management for Docx2Shelf.

Implements Sigstore signing, SLSA provenance, SBOM generation,
and security vulnerability scanning.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class SecurityConfig:
    """Configuration for security features."""

    enable_sigstore: bool = True
    enable_slsa_provenance: bool = True
    enable_sbom: bool = True
    enable_vulnerability_scan: bool = True
    trusted_signers: List[str] = field(default_factory=list)
    sigstore_identity: Optional[str] = None
    github_token: Optional[str] = None


@dataclass
class Artifact:
    """Represents a build artifact for security tracking."""

    name: str
    path: Path
    hash_sha256: str
    hash_sha512: str
    size_bytes: int
    mime_type: str
    created_at: datetime

    @classmethod
    def from_file(cls, file_path: Path, name: Optional[str] = None) -> "Artifact":
        """Create artifact from file."""
        if not file_path.exists():
            raise FileNotFoundError(f"Artifact file not found: {file_path}")

        # Calculate hashes
        sha256_hash = hashlib.sha256()
        sha512_hash = hashlib.sha512()

        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
                sha512_hash.update(chunk)

        # Determine MIME type
        mime_type = cls._get_mime_type(file_path)

        return cls(
            name=name or file_path.name,
            path=file_path,
            hash_sha256=sha256_hash.hexdigest(),
            hash_sha512=sha512_hash.hexdigest(),
            size_bytes=file_path.stat().st_size,
            mime_type=mime_type,
            created_at=datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc),
        )

    @staticmethod
    def _get_mime_type(file_path: Path) -> str:
        """Determine MIME type from file extension."""
        suffix = file_path.suffix.lower()
        mime_types = {
            ".whl": "application/x-wheel+zip",
            ".tar.gz": "application/gzip",
            ".zip": "application/zip",
            ".exe": "application/x-executable",
            ".dmg": "application/x-apple-diskimage",
            ".deb": "application/vnd.debian.binary-package",
            ".rpm": "application/x-rpm",
            ".json": "application/json",
            ".sig": "application/pgp-signature",
            ".pem": "application/x-pem-file",
        }
        return mime_types.get(suffix, "application/octet-stream")


class SigstoreManager:
    """Manages Sigstore signing and verification."""

    def __init__(self, config: SecurityConfig):
        self.config = config

    def sign_artifact(self, artifact: Artifact, output_dir: Path) -> Tuple[Path, Path]:
        """Sign artifact with Sigstore.

        Returns:
            Tuple of (signature_path, certificate_path)
        """
        if not self.config.enable_sigstore:
            raise ValueError("Sigstore signing is disabled")

        # Ensure cosign is available
        if not self._check_cosign_available():
            raise RuntimeError(
                "cosign CLI tool not found. Install from https://docs.sigstore.dev/cosign/installation/"
            )

        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate signature and certificate
        sig_path = output_dir / f"{artifact.name}.sig"
        cert_path = output_dir / f"{artifact.name}.pem"

        try:
            # Sign with cosign
            cmd = [
                "cosign",
                "sign-blob",
                "--output-signature",
                str(sig_path),
                "--output-certificate",
                str(cert_path),
                str(artifact.path),
            ]

            if self.config.sigstore_identity:
                cmd.extend(["--identity", self.config.sigstore_identity])

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            print(f"Successfully signed {artifact.name}")
            print(f"Signature: {sig_path}")
            print(f"Certificate: {cert_path}")

            return sig_path, cert_path

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Sigstore signing failed: {e.stderr}")

    def verify_artifact(
        self, artifact: Artifact, signature_path: Path, certificate_path: Path
    ) -> bool:
        """Verify artifact signature with Sigstore."""
        if not self._check_cosign_available():
            raise RuntimeError("cosign CLI tool not found")

        try:
            cmd = [
                "cosign",
                "verify-blob",
                "--signature",
                str(signature_path),
                "--certificate",
                str(certificate_path),
                "--certificate-identity-regexp",
                ".*",
                "--certificate-oidc-issuer-regexp",
                ".*",
                str(artifact.path),
            ]

            subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True

        except subprocess.CalledProcessError:
            return False

    def _check_cosign_available(self) -> bool:
        """Check if cosign CLI is available."""
        try:
            subprocess.run(["cosign", "version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False


class SLSAProvenanceGenerator:
    """Generates SLSA (Supply-chain Levels for Software Artifacts) provenance."""

    def __init__(self, config: SecurityConfig):
        self.config = config

    def generate_provenance(
        self, artifacts: List[Artifact], build_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate SLSA provenance document."""
        if not self.config.enable_slsa_provenance:
            raise ValueError("SLSA provenance generation is disabled")

        # SLSA provenance format v1.0
        provenance = {
            "_type": "https://in-toto.io/Statement/v1",
            "subject": self._create_subjects(artifacts),
            "predicateType": "https://slsa.dev/provenance/v1",
            "predicate": {
                "buildDefinition": {
                    "buildType": "https://github.com/Attestations/GitHubActionsWorkflow@v1",
                    "externalParameters": build_metadata.get("external_parameters", {}),
                    "internalParameters": build_metadata.get("internal_parameters", {}),
                    "resolvedDependencies": self._get_resolved_dependencies(),
                },
                "runDetails": {
                    "builder": {
                        "id": build_metadata.get("builder_id", "https://github.com/actions/runner"),
                        "version": build_metadata.get("builder_version", {}),
                    },
                    "metadata": {
                        "invocationId": build_metadata.get("invocation_id", ""),
                        "startedOn": build_metadata.get(
                            "started_on", datetime.now(timezone.utc).isoformat()
                        ),
                        "finishedOn": build_metadata.get(
                            "finished_on", datetime.now(timezone.utc).isoformat()
                        ),
                    },
                },
            },
        }

        return provenance

    def _create_subjects(self, artifacts: List[Artifact]) -> List[Dict[str, Any]]:
        """Create subject entries for artifacts."""
        subjects = []

        for artifact in artifacts:
            subject = {
                "name": artifact.name,
                "digest": {"sha256": artifact.hash_sha256, "sha512": artifact.hash_sha512},
            }
            subjects.append(subject)

        return subjects

    def _get_resolved_dependencies(self) -> List[Dict[str, Any]]:
        """Get resolved dependencies for provenance."""
        dependencies = []

        try:
            # Get Python dependencies
            result = subprocess.run(["pip", "freeze"], capture_output=True, text=True, check=True)

            for line in result.stdout.strip().split("\n"):
                if "==" in line:
                    name, version = line.split("==", 1)
                    dependencies.append(
                        {
                            "uri": f"pkg:pypi/{name}@{version}",
                            "digest": {"sha256": ""},  # Would need to fetch from PyPI
                            "name": name,
                            "downloadLocation": f"https://pypi.org/project/{name}/{version}/",
                            "mediaType": "application/vnd.pypi.simple.v1+json",
                        }
                    )

        except subprocess.CalledProcessError:
            pass

        return dependencies


class SBOMGenerator:
    """Generates Software Bill of Materials (SBOM) in CycloneDX format."""

    def __init__(self, config: SecurityConfig):
        self.config = config

    def generate_sbom(
        self, project_info: Dict[str, Any], artifacts: List[Artifact]
    ) -> Dict[str, Any]:
        """Generate SBOM in CycloneDX format."""
        if not self.config.enable_sbom:
            raise ValueError("SBOM generation is disabled")

        sbom = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.5",
            "serialNumber": f"urn:uuid:{self._generate_uuid()}",
            "version": 1,
            "metadata": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tools": [
                    {
                        "vendor": "Docx2Shelf",
                        "name": "Docx2Shelf SBOM Generator",
                        "version": project_info.get("version", "1.0.0"),
                    }
                ],
                "component": {
                    "type": "application",
                    "bom-ref": project_info.get("name", "docx2shelf"),
                    "name": project_info.get("name", "docx2shelf"),
                    "version": project_info.get("version", "1.0.0"),
                    "description": project_info.get("description", ""),
                    "licenses": [{"license": {"id": project_info.get("license", "MIT")}}],
                },
            },
            "components": self._get_components(),
            "dependencies": self._get_dependencies(),
        }

        return sbom

    def _get_components(self) -> List[Dict[str, Any]]:
        """Get software components for SBOM."""
        components = []

        try:
            # Get installed packages
            result = subprocess.run(
                ["pip", "list", "--format=json"], capture_output=True, text=True, check=True
            )

            packages = json.loads(result.stdout)

            for package in packages:
                component = {
                    "type": "library",
                    "bom-ref": f"pkg:pypi/{package['name']}@{package['version']}",
                    "name": package["name"],
                    "version": package["version"],
                    "purl": f"pkg:pypi/{package['name']}@{package['version']}",
                    "externalReferences": [
                        {
                            "type": "distribution",
                            "url": f"https://pypi.org/project/{package['name']}/{package['version']}/",
                        }
                    ],
                }
                components.append(component)

        except (subprocess.CalledProcessError, json.JSONDecodeError):
            pass

        return components

    def _get_dependencies(self) -> List[Dict[str, Any]]:
        """Get dependency relationships."""
        # For a complete implementation, this would parse requirements.txt
        # or use tools like pipdeptree to get the full dependency graph
        return []

    def _generate_uuid(self) -> str:
        """Generate a UUID for the SBOM."""
        import uuid

        return str(uuid.uuid4())


class VulnerabilityScanner:
    """Scans for security vulnerabilities in dependencies."""

    def __init__(self, config: SecurityConfig):
        self.config = config

    def scan_dependencies(self) -> Dict[str, Any]:
        """Scan Python dependencies for known vulnerabilities."""
        if not self.config.enable_vulnerability_scan:
            return {"enabled": False, "message": "Vulnerability scanning is disabled"}

        try:
            # Use safety to scan for vulnerabilities
            result = subprocess.run(
                ["safety", "check", "--json"], capture_output=True, text=True, check=True
            )

            safety_report = json.loads(result.stdout)

            return {
                "enabled": True,
                "tool": "safety",
                "scan_time": datetime.now(timezone.utc).isoformat(),
                "vulnerabilities": safety_report,
                "total_vulnerabilities": len(safety_report),
            }

        except subprocess.CalledProcessError as e:
            # safety returns non-zero exit code when vulnerabilities are found
            try:
                safety_report = json.loads(e.stdout)
                return {
                    "enabled": True,
                    "tool": "safety",
                    "scan_time": datetime.now(timezone.utc).isoformat(),
                    "vulnerabilities": safety_report,
                    "total_vulnerabilities": len(safety_report),
                }
            except json.JSONDecodeError:
                return {
                    "enabled": True,
                    "tool": "safety",
                    "scan_time": datetime.now(timezone.utc).isoformat(),
                    "error": e.stderr,
                    "total_vulnerabilities": 0,
                }

        except FileNotFoundError:
            return {
                "enabled": True,
                "tool": "safety",
                "scan_time": datetime.now(timezone.utc).isoformat(),
                "error": "safety tool not found. Install with: pip install safety",
                "total_vulnerabilities": 0,
            }


class SecurityManager:
    """Main security management class."""

    def __init__(self, config: Optional[SecurityConfig] = None):
        self.config = config or SecurityConfig()
        self.sigstore = SigstoreManager(self.config)
        self.provenance = SLSAProvenanceGenerator(self.config)
        self.sbom = SBOMGenerator(self.config)
        self.vulnerability_scanner = VulnerabilityScanner(self.config)

    def secure_build(
        self,
        artifacts: List[Artifact],
        output_dir: Path,
        project_info: Dict[str, Any],
        build_metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Perform complete security build process."""
        output_dir.mkdir(parents=True, exist_ok=True)

        security_artifacts = {}

        # 1. Sign artifacts with Sigstore
        if self.config.enable_sigstore:
            try:
                signatures = []
                for artifact in artifacts:
                    sig_path, cert_path = self.sigstore.sign_artifact(artifact, output_dir)
                    signatures.append(
                        {
                            "artifact": artifact.name,
                            "signature": str(sig_path),
                            "certificate": str(cert_path),
                        }
                    )
                security_artifacts["signatures"] = signatures
            except Exception as e:
                security_artifacts["signature_error"] = str(e)

        # 2. Generate SLSA provenance
        if self.config.enable_slsa_provenance:
            try:
                provenance = self.provenance.generate_provenance(artifacts, build_metadata)
                provenance_path = output_dir / "provenance.json"
                with open(provenance_path, "w") as f:
                    json.dump(provenance, f, indent=2)
                security_artifacts["provenance"] = str(provenance_path)
            except Exception as e:
                security_artifacts["provenance_error"] = str(e)

        # 3. Generate SBOM
        if self.config.enable_sbom:
            try:
                sbom = self.sbom.generate_sbom(project_info, artifacts)
                sbom_path = output_dir / "sbom.json"
                with open(sbom_path, "w") as f:
                    json.dump(sbom, f, indent=2)
                security_artifacts["sbom"] = str(sbom_path)
            except Exception as e:
                security_artifacts["sbom_error"] = str(e)

        # 4. Scan for vulnerabilities
        if self.config.enable_vulnerability_scan:
            try:
                vuln_report = self.vulnerability_scanner.scan_dependencies()
                vuln_path = output_dir / "vulnerability_report.json"
                with open(vuln_path, "w") as f:
                    json.dump(vuln_report, f, indent=2)
                security_artifacts["vulnerability_report"] = str(vuln_path)
            except Exception as e:
                security_artifacts["vulnerability_error"] = str(e)

        # 5. Create security summary
        summary = {
            "security_build_time": datetime.now(timezone.utc).isoformat(),
            "artifacts_processed": len(artifacts),
            "security_features": {
                "sigstore_signing": self.config.enable_sigstore,
                "slsa_provenance": self.config.enable_slsa_provenance,
                "sbom_generation": self.config.enable_sbom,
                "vulnerability_scanning": self.config.enable_vulnerability_scan,
            },
            "artifacts": security_artifacts,
        }

        summary_path = output_dir / "security_summary.json"
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=2)

        return summary

    def verify_build(self, artifacts_dir: Path) -> Dict[str, Any]:
        """Verify security artifacts."""
        verification_results = {}

        # Find all artifacts
        artifacts = []
        for file_path in artifacts_dir.glob("*"):
            if file_path.suffix not in [".sig", ".pem", ".json"]:
                try:
                    artifact = Artifact.from_file(file_path)
                    artifacts.append(artifact)
                except Exception as e:
                    verification_results[f"artifact_error_{file_path.name}"] = str(e)

        # Verify signatures
        for artifact in artifacts:
            sig_path = artifacts_dir / f"{artifact.name}.sig"
            cert_path = artifacts_dir / f"{artifact.name}.pem"

            if sig_path.exists() and cert_path.exists():
                try:
                    is_valid = self.sigstore.verify_artifact(artifact, sig_path, cert_path)
                    verification_results[f"signature_{artifact.name}"] = (
                        "valid" if is_valid else "invalid"
                    )
                except Exception as e:
                    verification_results[f"signature_error_{artifact.name}"] = str(e)

        # Verify provenance
        provenance_path = artifacts_dir / "provenance.json"
        if provenance_path.exists():
            try:
                with open(provenance_path) as f:
                    provenance = json.load(f)
                # Basic provenance validation
                required_fields = ["_type", "subject", "predicateType", "predicate"]
                is_valid = all(field in provenance for field in required_fields)
                verification_results["provenance"] = "valid" if is_valid else "invalid"
            except Exception as e:
                verification_results["provenance_error"] = str(e)

        return verification_results

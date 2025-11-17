"""
Comprehensive documentation platform for Docx2Shelf.

Provides interactive tutorials, troubleshooting wizard, and learning resources
for developers and users.
"""

from __future__ import annotations

import subprocess
import webbrowser
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Optional


@dataclass
class TutorialStep:
    """Single step in an interactive tutorial."""

    id: str
    title: str
    description: str
    code_example: Optional[str] = None
    expected_output: Optional[str] = None
    validation_func: Optional[Callable] = None
    hints: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)


@dataclass
class Tutorial:
    """Interactive tutorial with multiple steps."""

    id: str
    title: str
    description: str
    category: str
    difficulty: str  # beginner, intermediate, advanced
    estimated_time: str
    steps: List[TutorialStep] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


@dataclass
class TroubleshootingCase:
    """Troubleshooting case with symptoms and solutions."""

    id: str
    title: str
    symptoms: List[str]
    common_causes: List[str]
    solutions: List[str]
    related_cases: List[str] = field(default_factory=list)
    category: str = "general"
    severity: str = "medium"  # low, medium, high, critical


class InteractiveTutorial:
    """Manages interactive tutorial execution."""

    def __init__(self, tutorial: Tutorial):
        self.tutorial = tutorial
        self.current_step = 0
        self.completed_steps = set()
        self.user_progress = {}

    def start(self) -> bool:
        """Start the tutorial."""
        print(f"\n🎓 {self.tutorial.title}")
        print(f"📝 {self.tutorial.description}")
        print(f"⏱️  Estimated time: {self.tutorial.estimated_time}")
        print(f"📊 Difficulty: {self.tutorial.difficulty}")

        if self.tutorial.prerequisites:
            print("\n📋 Prerequisites:")
            for prereq in self.tutorial.prerequisites:
                print(f"  • {prereq}")

        print(f"\n📚 This tutorial has {len(self.tutorial.steps)} steps")
        response = input("Ready to start? (y/n): ").lower().strip()
        return response in ["y", "yes"]

    def run_step(self, step_index: int) -> bool:
        """Run a specific tutorial step."""
        if step_index >= len(self.tutorial.steps):
            return False

        step = self.tutorial.steps[step_index]
        print(f"\n📌 Step {step_index + 1}: {step.title}")
        print(f"   {step.description}")

        if step.code_example:
            print("\n💻 Code Example:")
            print(f"```bash\n{step.code_example}\n```")

        if step.expected_output:
            print("\n✅ Expected Output:")
            print(f"```\n{step.expected_output}\n```")

        # Wait for user to complete step
        while True:
            response = input("\nCompleted this step? (y/n/hint/skip): ").lower().strip()

            if response in ["y", "yes"]:
                if step.validation_func:
                    if step.validation_func():
                        self.completed_steps.add(step.id)
                        return True
                    else:
                        print("❌ Validation failed. Please try again.")
                        continue
                else:
                    self.completed_steps.add(step.id)
                    return True

            elif response in ["n", "no"]:
                return False

            elif response == "hint":
                if step.hints:
                    print(f"\n💡 Hint: {step.hints[0]}")
                else:
                    print("💭 No hints available for this step.")

            elif response == "skip":
                print("⏭️  Skipping step...")
                return True

    def complete_tutorial(self):
        """Complete the tutorial and show summary."""
        completed_count = len(self.completed_steps)
        total_steps = len(self.tutorial.steps)
        completion_rate = (completed_count / total_steps) * 100

        print("\n🎉 Tutorial Complete!")
        print(f"📊 Completion: {completed_count}/{total_steps} steps ({completion_rate:.1f}%)")

        if completion_rate >= 80:
            print("🌟 Excellent work! You've mastered this tutorial.")
        elif completion_rate >= 60:
            print("👍 Good job! Consider reviewing the skipped steps.")
        else:
            print("📚 You might want to retry this tutorial for better understanding.")


class TroubleshootingWizard:
    """Interactive troubleshooting wizard."""

    def __init__(self):
        self.cases = self._load_troubleshooting_cases()
        self.current_symptoms = []

    def start(self):
        """Start the troubleshooting wizard."""
        print("🔧 Docx2Shelf Troubleshooting Wizard")
        print("Answer a few questions to diagnose your issue.")

        while True:
            print("\nWhat type of issue are you experiencing?")
            print("1. Installation problems")
            print("2. Conversion errors")
            print("3. Output quality issues")
            print("4. Performance problems")
            print("5. Plugin issues")
            print("6. Enterprise/API issues")
            print("7. Other")
            print("0. Exit")

            choice = input("Enter your choice (0-7): ").strip()

            if choice == "0":
                break
            elif choice in ["1", "2", "3", "4", "5", "6", "7"]:
                self._handle_category(choice)
            else:
                print("❌ Invalid choice. Please try again.")

    def _handle_category(self, category: str):
        """Handle specific troubleshooting category."""
        category_map = {
            "1": "installation",
            "2": "conversion",
            "3": "output_quality",
            "4": "performance",
            "5": "plugins",
            "6": "enterprise",
            "7": "other",
        }

        category_name = category_map[category]
        relevant_cases = [case for case in self.cases if case.category == category_name]

        if not relevant_cases:
            print(f"🤔 No specific troubleshooting cases found for {category_name}.")
            print("Try checking the general documentation or community forums.")
            return

        print(f"\n🔍 Found {len(relevant_cases)} potential solutions for {category_name} issues.")

        # Collect symptoms
        symptoms = self._collect_symptoms(relevant_cases)

        # Find matching cases
        matching_cases = self._find_matching_cases(relevant_cases, symptoms)

        if matching_cases:
            self._present_solutions(matching_cases)
        else:
            print("🤔 No exact matches found. Here are some general suggestions:")
            self._present_general_solutions(relevant_cases[:3])

    def _collect_symptoms(self, cases: List[TroubleshootingCase]) -> List[str]:
        """Collect symptoms from user."""
        all_symptoms = set()
        for case in cases:
            all_symptoms.update(case.symptoms)

        print("\nWhich of these symptoms match your issue? (Enter numbers separated by commas)")
        symptoms_list = list(all_symptoms)
        for i, symptom in enumerate(symptoms_list, 1):
            print(f"{i}. {symptom}")

        while True:
            response = input("Symptoms (e.g., 1,3,5): ").strip()
            if not response:
                return []

            try:
                indices = [int(x.strip()) - 1 for x in response.split(",")]
                return [symptoms_list[i] for i in indices if 0 <= i < len(symptoms_list)]
            except (ValueError, IndexError):
                print("❌ Invalid input. Please enter valid numbers separated by commas.")

    def _find_matching_cases(
        self, cases: List[TroubleshootingCase], symptoms: List[str]
    ) -> List[TroubleshootingCase]:
        """Find cases that match the symptoms."""
        if not symptoms:
            return []

        matching_cases = []
        for case in cases:
            symptom_matches = sum(1 for symptom in symptoms if symptom in case.symptoms)
            if symptom_matches > 0:
                matching_cases.append((case, symptom_matches))

        # Sort by number of matching symptoms
        matching_cases.sort(key=lambda x: x[1], reverse=True)
        return [case for case, _ in matching_cases[:5]]

    def _present_solutions(self, cases: List[TroubleshootingCase]):
        """Present solutions for matching cases."""
        for i, case in enumerate(cases, 1):
            print(f"\n🎯 Solution {i}: {case.title}")
            print("📋 Common causes:")
            for cause in case.common_causes:
                print(f"  • {cause}")

            print("🔧 Solutions:")
            for solution in case.solutions:
                print(f"  • {solution}")

            if i < len(cases):
                input("Press Enter to see next solution...")

    def _present_general_solutions(self, cases: List[TroubleshootingCase]):
        """Present general solutions when no specific match."""
        for case in cases:
            print(f"\n💡 {case.title}")
            for solution in case.solutions[:2]:  # Show first 2 solutions
                print(f"  • {solution}")

    def _load_troubleshooting_cases(self) -> List[TroubleshootingCase]:
        """Load troubleshooting cases."""
        return [
            TroubleshootingCase(
                id="install_python_missing",
                title="Python not found or version too old",
                symptoms=[
                    "Command 'python' not found",
                    "Python version is too old",
                    "pipx not working",
                ],
                common_causes=["Python not installed", "Old Python version", "PATH not configured"],
                solutions=[
                    "Install Python 3.11 or newer from python.org",
                    "Add Python to your system PATH",
                    "Use 'py' command on Windows instead of 'python'",
                    "Restart your terminal after installation",
                ],
                category="installation",
                severity="high",
            ),
            TroubleshootingCase(
                id="conversion_docx_corrupt",
                title="DOCX file appears corrupted or invalid",
                symptoms=[
                    "Error reading DOCX file",
                    "ZIP file is corrupted",
                    "Invalid DOCX structure",
                ],
                common_causes=["Corrupted file", "Invalid DOCX format", "Unsupported Word version"],
                solutions=[
                    "Try opening the file in Microsoft Word to verify it's valid",
                    "Save the file as a new DOCX from Word",
                    "Use pandoc conversion method: --converter pandoc",
                    "Check if file was completely downloaded/copied",
                ],
                category="conversion",
                severity="medium",
            ),
            TroubleshootingCase(
                id="output_poor_formatting",
                title="EPUB has poor formatting or layout issues",
                symptoms=[
                    "Text not formatted properly",
                    "Images not displaying",
                    "CSS not applied",
                ],
                common_causes=["Theme issues", "CSS conflicts", "Image processing problems"],
                solutions=[
                    "Try a different theme: --theme serif/sans/printlike",
                    "Use --inspect to examine the generated HTML",
                    "Check image file formats (JPG/PNG work best)",
                    "Validate with EPUBCheck: docx2shelf tools install epubcheck",
                ],
                category="output_quality",
                severity="medium",
            ),
            TroubleshootingCase(
                id="performance_slow_conversion",
                title="Conversion is very slow",
                symptoms=[
                    "Takes much longer than expected",
                    "High CPU usage",
                    "Large memory usage",
                ],
                common_causes=["Large images", "Complex document", "Insufficient resources"],
                solutions=[
                    "Optimize images before conversion",
                    "Split large documents into smaller files",
                    "Increase available memory",
                    "Use --max-image-width to limit image sizes",
                ],
                category="performance",
                severity="low",
            ),
            TroubleshootingCase(
                id="plugin_not_loading",
                title="Plugin fails to load or execute",
                symptoms=["Plugin not found", "Import errors", "Plugin execution fails"],
                common_causes=[
                    "Missing dependencies",
                    "Plugin compatibility",
                    "Installation issues",
                ],
                solutions=[
                    "Check plugin dependencies: docx2shelf plugins info plugin-name",
                    "Reinstall plugin: docx2shelf plugins marketplace install plugin-name",
                    "Check plugin compatibility with current version",
                    "Review plugin logs for specific errors",
                ],
                category="plugins",
                severity="medium",
            ),
        ]


class DocumentationManager:
    """Manages the comprehensive documentation platform."""

    def __init__(self, docs_root: Path):
        self.docs_root = docs_root
        self.tutorials = self._load_tutorials()
        self.wizard = TroubleshootingWizard()

    def build_docs(self) -> bool:
        """Build the documentation site."""
        try:
            result = subprocess.run(
                ["mkdocs", "build", "--clean"],
                cwd=self.docs_root.parent,
                capture_output=True,
                text=True,
                check=True,
            )
            print("📚 Documentation built successfully!")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Documentation build failed: {e.stderr}")
            return False
        except FileNotFoundError:
            print("❌ MkDocs not found. Install with: pip install mkdocs mkdocs-material")
            return False

    def serve_docs(self, port: int = 8000) -> bool:
        """Serve the documentation site locally."""
        try:
            print(f"🌐 Starting documentation server on http://localhost:{port}")
            subprocess.run(
                ["mkdocs", "serve", "--dev-addr", f"localhost:{port}"],
                cwd=self.docs_root.parent,
                check=True,
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Documentation server failed: {e.stderr}")
            return False
        except KeyboardInterrupt:
            print("\n📚 Documentation server stopped.")
            return True

    def open_docs_browser(self, path: str = ""):
        """Open documentation in browser."""
        url = f"http://localhost:8000/{path}"
        webbrowser.open(url)
        print(f"🌐 Opening documentation: {url}")

    def run_tutorial(self, tutorial_id: str) -> bool:
        """Run an interactive tutorial."""
        tutorial = next((t for t in self.tutorials if t.id == tutorial_id), None)
        if not tutorial:
            print(f"❌ Tutorial '{tutorial_id}' not found.")
            self.list_tutorials()
            return False

        interactive_tutorial = InteractiveTutorial(tutorial)
        if not interactive_tutorial.start():
            print("📚 Tutorial cancelled.")
            return False

        # Run through all steps
        for i in range(len(tutorial.steps)):
            if not interactive_tutorial.run_step(i):
                print("📚 Tutorial stopped.")
                break

        interactive_tutorial.complete_tutorial()
        return True

    def list_tutorials(self):
        """List available tutorials."""
        print("📚 Available Tutorials:")

        categories = {}
        for tutorial in self.tutorials:
            if tutorial.category not in categories:
                categories[tutorial.category] = []
            categories[tutorial.category].append(tutorial)

        for category, tutorials in categories.items():
            print(f"\n{category.title()}:")
            for tutorial in tutorials:
                difficulty_icon = {"beginner": "🟢", "intermediate": "🟡", "advanced": "🔴"}
                icon = difficulty_icon.get(tutorial.difficulty, "⚪")
                print(f"  {icon} {tutorial.id}: {tutorial.title} ({tutorial.estimated_time})")

    def run_troubleshooting_wizard(self):
        """Run the interactive troubleshooting wizard."""
        self.wizard.start()

    def _load_tutorials(self) -> List[Tutorial]:
        """Load built-in tutorials."""
        return [
            Tutorial(
                id="getting-started",
                title="Getting Started with Docx2Shelf",
                description="Learn the basics of converting DOCX files to EPUB",
                category="basics",
                difficulty="beginner",
                estimated_time="15 minutes",
                steps=[
                    TutorialStep(
                        id="install",
                        title="Install Docx2Shelf",
                        description="Install Docx2Shelf using pipx for best isolation",
                        code_example="pipx install docx2shelf",
                        expected_output="✅ Installed docx2shelf",
                        hints=[
                            "If pipx is not installed: pip install pipx",
                            "Windows users can use install.bat",
                        ],
                    ),
                    TutorialStep(
                        id="first-conversion",
                        title="Convert your first document",
                        description="Convert a simple DOCX file to EPUB",
                        code_example='docx2shelf build --input sample.docx --title "My First Book" --author "Your Name"',
                        expected_output="📖 EPUB created successfully",
                        hints=[
                            "Make sure you have a DOCX file ready",
                            "Use quotes around titles with spaces",
                        ],
                    ),
                    TutorialStep(
                        id="customize-theme",
                        title="Customize the appearance",
                        description="Try different themes and styling options",
                        code_example="docx2shelf build --input sample.docx --theme serif --justify on",
                        hints=[
                            "Available themes: serif, sans, printlike",
                            "Use --css to add custom styles",
                        ],
                    ),
                ],
                tags=["beginner", "conversion", "setup"],
            ),
            Tutorial(
                id="plugin-development",
                title="Creating Your First Plugin",
                description="Learn how to develop custom plugins for Docx2Shelf",
                category="development",
                difficulty="intermediate",
                estimated_time="30 minutes",
                prerequisites=["Basic Python knowledge", "Familiarity with Docx2Shelf"],
                steps=[
                    TutorialStep(
                        id="plugin-template",
                        title="Create plugin template",
                        description="Generate a new plugin template",
                        code_example="docx2shelf plugins create-template my-first-plugin",
                        expected_output="📦 Plugin template created in ./my-first-plugin/",
                    ),
                    TutorialStep(
                        id="implement-hook",
                        title="Implement a processing hook",
                        description="Add functionality to process content",
                        code_example="# Edit plugin.py to add your processing logic",
                        hints=[
                            "Use PreConvertHook for input processing",
                            "Use PostConvertHook for output processing",
                        ],
                    ),
                    TutorialStep(
                        id="test-plugin",
                        title="Test your plugin",
                        description="Load and test the plugin",
                        code_example="docx2shelf plugins load my-first-plugin",
                        hints=["Use --verbose to see detailed plugin loading information"],
                    ),
                ],
                tags=["development", "plugins", "intermediate"],
            ),
            Tutorial(
                id="enterprise-deployment",
                title="Enterprise Deployment with Kubernetes",
                description="Deploy Docx2Shelf in production with Kubernetes",
                category="deployment",
                difficulty="advanced",
                estimated_time="45 minutes",
                prerequisites=[
                    "Kubernetes knowledge",
                    "Docker experience",
                    "Production environment",
                ],
                steps=[
                    TutorialStep(
                        id="prepare-manifests",
                        title="Prepare Kubernetes manifests",
                        description="Review and customize the provided manifests",
                        code_example="kubectl apply -f k8s/",
                        hints=[
                            "Check resource limits in deployment.yaml",
                            "Configure persistent storage if needed",
                        ],
                    ),
                    TutorialStep(
                        id="setup-monitoring",
                        title="Setup monitoring",
                        description="Configure Prometheus monitoring",
                        code_example="kubectl apply -f k8s/servicemonitor.yaml",
                        hints=[
                            "Ensure Prometheus operator is installed",
                            "Check metrics endpoint accessibility",
                        ],
                    ),
                    TutorialStep(
                        id="test-api",
                        title="Test the API",
                        description="Verify the enterprise API is working",
                        code_example="curl http://your-cluster/health",
                        expected_output='{"status": "healthy"}',
                        hints=[
                            "Use port-forward for local testing: kubectl port-forward svc/docx2shelf 8080:80"
                        ],
                    ),
                ],
                tags=["deployment", "kubernetes", "enterprise", "advanced"],
            ),
        ]


def create_interactive_cookbook():
    """Create an interactive cookbook with common workflows."""
    cookbook_entries = [
        {
            "title": "Perfect KDP Formatting",
            "description": "Optimize your EPUB for Amazon Kindle Direct Publishing",
            "steps": [
                "Use --profile kdp for KDP-specific optimizations",
                "Set appropriate metadata with --isbn and --publisher",
                "Include print ISBN and other required fields",
                "Run validation: docx2shelf checklist --epub book.epub --store kdp",
            ],
            "tips": [
                "KDP prefers certain CSS properties - use built-in themes",
                "Include proper copyright and metadata information",
                "Test with Kindle Previewer if available",
            ],
        },
        {
            "title": "Multi-Book Series Management",
            "description": "Create and manage book series with cross-references",
            "steps": [
                "Build individual books: docx2shelf build --series 'Series Name' --series-index 1",
                "Use series builder: docx2shelf series build --auto-also-by",
                "Generate series metadata and navigation",
                "Cross-reference between books in the series",
            ],
            "tips": [
                "Maintain consistent metadata across series",
                "Use --output-pattern for consistent naming",
                "Consider anthology format for collections",
            ],
        },
        {
            "title": "High-Quality Image Processing",
            "description": "Optimize images for better EPUB quality and size",
            "steps": [
                "Use high-resolution source images (300 DPI minimum)",
                "Set appropriate max width: --max-image-width 1200",
                "Enable image optimization: --optimize-images",
                "Consider WebP format for modern readers",
            ],
            "tips": [
                "Balance quality vs file size",
                "Include alt text for accessibility",
                "Test images on target devices",
            ],
        },
    ]
    return cookbook_entries

#!/usr/bin/env python3
"""
AppImage Validation Module
Provides comprehensive validation and testing of created AppImages
"""

import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

# Configure module-level logger
logger = logging.getLogger(__name__)


class AppImageValidator:
    """Comprehensive AppImage validation and testing"""

    def __init__(self, appimage_path: str, timeout: int = 30):
        self.appimage_path: Path = Path(appimage_path)
        self.timeout: int = timeout
        self.temp_dir: Optional[str] = None
        self.results: Dict[str, Any] = {
            "file_validation": {},
            "runtime_validation": {},
            "integration_tests": {},
            "overall_status": "unknown",
        }

    def validate_file(self) -> Dict[str, Any]:
        """Validate AppImage file properties"""
        logger.info(f"Starting file validation for: {self.appimage_path}")
        print("🔍 Validating AppImage file properties...")

        results: Dict[str, Any] = {}

        # Check if file exists
        results["exists"] = self.appimage_path.exists()
        if not results["exists"]:
            logger.error(f"AppImage not found: {self.appimage_path}")
            print(f"❌ AppImage not found: {self.appimage_path}")
            return results

        # Check file size
        if results["exists"]:
            size = self.appimage_path.stat().st_size
            results["has_size"] = size > 0
            results["size_mb"] = round(size / (1024 * 1024), 2)
            logger.info(f"AppImage size: {results['size_mb']} MB")
            print(f"📦 AppImage size: {results['size_mb']} MB")

        # Check if executable
        if results["exists"]:
            results["is_executable"] = os.access(self.appimage_path, os.X_OK)
            if not results["is_executable"]:
                logger.warning("AppImage is not executable, fixing permissions...")
                print("⚠️  AppImage is not executable, fixing permissions...")
                self.appimage_path.chmod(0o755)
                results["is_executable"] = os.access(self.appimage_path, os.X_OK)

        # Check file format (basic ELF check)
        if results["exists"]:
            try:
                with open(self.appimage_path, "rb") as f:
                    magic = f.read(4)
                    results["is_elf"] = magic == b"\x7fELF"
                    results["is_appimage"] = magic[
                        :2
                    ] == b"\x7fELF" and ".AppImage" in str(self.appimage_path)
            except Exception as e:
                results["is_elf"] = False
                results["is_appimage"] = False
                logger.error(f"Error reading file header: {e}")
                print(f"❌ Error reading file header: {e}")

        # Check for AppImage signature
        if results["exists"]:
            try:
                result = subprocess.run(
                    ["file", os.path.abspath(str(self.appimage_path))],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                output = result.stdout.lower()
                results["file_type"] = result.stdout.strip()
                results["is_recognized"] = any(
                    keyword in output for keyword in ["appimage", "elf", "executable"]
                )
            except Exception:
                results["is_recognized"] = False
                results["file_type"] = "Unknown"

        return results

    def extract_and_validate_structure(self) -> Dict[str, Any]:
        """Extract AppImage and validate internal structure"""
        print("🔧 Extracting and validating AppImage structure...")

        # Create temporary directory
        self.temp_dir = tempfile.mkdtemp(prefix="appimage_validation_")

        results: Dict[str, Any] = {}

        try:
            # Make AppImage executable if not already
            if not os.access(self.appimage_path, os.X_OK):
                self.appimage_path.chmod(0o755)

            # Extract AppImage
            result = subprocess.run(
                [os.path.abspath(str(self.appimage_path)), "--appimage-extract"],
                cwd=self.temp_dir,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )

            results["extraction_success"] = result.returncode == 0
            results["extraction_output"] = result.stdout.strip()

            if not results["extraction_success"]:
                print(f"❌ Extraction failed: {result.stderr}")
                return results

            extracted_dir = Path(self.temp_dir) / "squashfs-root"
            results["extracted_dir_exists"] = extracted_dir.exists()

            if results["extracted_dir_exists"]:
                # Check essential files and directories
                essential_paths = [
                    "AppRun",
                    "usr",
                    "usr/bin",
                    "usr/lib",
                    "usr/share/applications",
                ]

                for path in essential_paths:
                    full_path = extracted_dir / path
                    results[f"has_{path.replace('/', '_')}"] = full_path.exists()

                # Check for Java files
                java_files = list(extracted_dir.rglob("*.jar"))
                results["jar_files_found"] = len(java_files) > 0
                results["jar_file_count"] = len(java_files)

                # Check for bundled Java
                bundled_java = list(extracted_dir.rglob("java")) + list(
                    extracted_dir.rglob("jre")
                )
                results["bundled_java_found"] = len(bundled_java) > 0

                # Check for AppRun content
                apprun_path = extracted_dir / "AppRun"
                if apprun_path.exists():
                    apprun_content = apprun_path.read_text()
                    results["apprun_has_java_execution"] = "java" in apprun_content
                    results["apprun_has_error_handling"] = (
                        "error" in apprun_content.lower()
                    )

        except Exception as e:
            logger.error(f"Structure validation error: {e}")
            print(f"❌ Structure validation error: {e}")
            results["extraction_error"] = str(e)

        return results

    def test_runtime_execution(self) -> Dict[str, Any]:
        """Test AppImage runtime execution"""
        print("🚀 Testing AppImage runtime execution...")

        results: Dict[str, Any] = {}

        try:
            # Test --help flag (should work for most Java apps)
            print("  Testing --help flag...")
            result = subprocess.run(
                [os.path.abspath(str(self.appimage_path)), "--help"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            results["help_flag_works"] = result.returncode in [
                0,
                1,
            ]  # Both 0 and 1 can be normal
            results["help_output_length"] = len(result.stdout + result.stderr)

            # Test --version flag (common in Java apps)
            print("  Testing --version flag...")
            result = subprocess.run(
                [os.path.abspath(str(self.appimage_path)), "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            results["version_flag_works"] = result.returncode in [0, 1]
            results["version_output_length"] = len(result.stdout + result.stderr)

            # Test basic execution (short timeout to avoid hanging)
            print("  Testing basic execution...")
            result = subprocess.run(
                [os.path.abspath(str(self.appimage_path))],
                capture_output=True,
                text=True,
                timeout=5,
            )

            results["basic_execution_attempted"] = True
            results["basic_execution_returncode"] = result.returncode
            results["has_any_output"] = len(result.stdout + result.stderr) > 0

            # Check for common Java error patterns
            combined_output = result.stdout + result.stderr
            results["no_java_errors"] = not any(
                pattern in combined_output.lower()
                for pattern in [
                    "java.lang.classnotfoundexception",
                    "could not find or load main class",
                    "error: could not find main class",
                    "noclassdeffounderror",
                ]
            )

        except subprocess.TimeoutExpired:
            results["execution_timeout"] = True
            print("  ⏰ Execution timed out (might be normal for GUI apps)")
        except Exception as e:
            results["execution_error"] = str(e)
            print(f"  ❌ Runtime test error: {e}")

        return results

    def validate_desktop_integration(self) -> Dict[str, Any]:
        """Validate desktop integration files"""
        print("📋 Validating desktop integration...")

        results: Dict[str, Any] = {}

        if not self.temp_dir:
            results["skipped"] = True
            return results

        try:
            extracted_dir = Path(self.temp_dir) / "squashfs-root"
            desktop_dir = extracted_dir / "usr" / "share" / "applications"

            if desktop_dir.exists():
                desktop_files = list(desktop_dir.glob("*.desktop"))
                results["has_desktop_files"] = len(desktop_files) > 0
                results["desktop_file_count"] = len(desktop_files)

                if desktop_files:
                    # Validate first desktop file
                    desktop_file = desktop_files[0]
                    content = desktop_file.read_text()

                    results["has_desktop_entry"] = "[Desktop Entry]" in content
                    results["has_exec_line"] = "Exec=" in content
                    results["has_name_line"] = "Name=" in content
                    results["has_categories"] = "Categories=" in content
                    results["has_terminal_spec"] = "Terminal=" in content

                    # Check if terminal setting makes sense for app type
                    terminal_setting = "Terminal=true" in content
                    gui_indicators = ["Type=Application", "Icon="] + [
                        category in content
                        for category in ["Development", "Utility", "Office"]
                    ]

                    results["terminal_setting_appropriate"] = not (
                        terminal_setting and any(gui_indicators)
                    )

            # Check for icon files
            icon_dir = extracted_dir / "usr" / "share" / "icons"
            if icon_dir.exists():
                icon_files = list(icon_dir.rglob("*"))
                results["has_icon_files"] = len(icon_files) > 0

        except Exception as e:
            results["desktop_validation_error"] = str(e)
            logger.error(f"Desktop validation error: {e}")
            print(f"  ❌ Desktop validation error: {e}")

        return results

    def generate_validation_report(self) -> str:  # noqa: C901
        """Generate comprehensive validation report"""
        print("📊 Generating validation report...")

        # Run all validations
        self.results["file_validation"] = self.validate_file()
        self.results["runtime_validation"] = self.test_runtime_execution()

        if self.results["file_validation"].get("is_appimage", False):
            self.results["structure_validation"] = self.extract_and_validate_structure()
            self.results["integration_tests"] = self.validate_desktop_integration()

        # Calculate overall status
        file_ok = (
            self.results["file_validation"].get("is_executable", False)
            and self.results["file_validation"].get("is_elf", False)
            and ".AppImage" in str(self.appimage_path)
        )
        runtime_ok = (
            self.results["runtime_validation"].get("help_flag_works", False)
            or self.results["runtime_validation"].get("version_flag_works", False)
            or (
                self.results["runtime_validation"].get("has_any_output", False)
                and self.results["runtime_validation"].get("no_java_errors", False)
            )
        )

        if file_ok and runtime_ok:
            self.results["overall_status"] = "passed"
        elif file_ok:
            self.results["overall_status"] = "warning"
        else:
            self.results["overall_status"] = "failed"

        # Generate report
        report_lines = [
            "=" * 60,
            "🎯 APPIMAGE VALIDATION REPORT",
            "=" * 60,
            f"📁 AppImage: {self.appimage_path}",
            f"📊 Overall Status: {self.results['overall_status'].upper()}",
            "",
            "📋 FILE VALIDATION:",
            "-" * 30,
        ]

        for key, value in self.results["file_validation"].items():
            status = "✅" if value else "❌"
            report_lines.append(f"  {status} {key.replace('_', ' ').title()}: {value}")

        if "structure_validation" in self.results:
            report_lines.extend(["", "🔧 STRUCTURE VALIDATION:", "-" * 30])

            for key, value in self.results["structure_validation"].items():
                if key != "extraction_output":
                    status = "✅" if value else "❌"
                    report_lines.append(
                        f"  {status} {key.replace('_', ' ').title()}: {value}"
                    )

        report_lines.extend(["", "🚀 RUNTIME VALIDATION:", "-" * 30])

        for key, value in self.results["runtime_validation"].items():
            if isinstance(value, bool):
                status = "✅" if value else "❌"
                report_lines.append(
                    f"  {status} {key.replace('_', ' ').title()}: {value}"
                )
            else:
                report_lines.append(f"  📝 {key.replace('_', ' ').title()}: {value}")

        if "integration_tests" in self.results:
            report_lines.extend(["", "📋 DESKTOP INTEGRATION:", "-" * 30])

            for key, value in self.results["integration_tests"].items():
                if isinstance(value, bool):
                    status = "✅" if value else "❌"
                    report_lines.append(
                        f"  {status} {key.replace('_', ' ').title()}: {value}"
                    )
                else:
                    report_lines.append(
                        f"  📝 {key.replace('_', ' ').title()}: {value}"
                    )

        # Add recommendations
        report_lines.extend(["", "💡 RECOMMENDATIONS:", "-" * 30])

        if self.results["overall_status"] == "passed":
            report_lines.append("🎉 AppImage is ready for distribution!")
        elif self.results["overall_status"] == "warning":
            report_lines.append("⚠️  AppImage works but may have minor issues")
        else:
            report_lines.append("❌ AppImage needs attention before distribution")

        # Save report
        report_path = (
            self.appimage_path.parent
            / f"{self.appimage_path.stem}_validation_report.txt"
        )
        report_content = "\n".join(report_lines)

        with open(report_path, "w") as f:
            f.write(report_content)

        print(f"📄 Validation report saved: {report_path}")

        return report_content

    def cleanup(self) -> None:
        """Clean up temporary files"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            import shutil

            shutil.rmtree(self.temp_dir, ignore_errors=True)


def validate_appimage(appimage_path: str, timeout: int = 30) -> bool:
    """Quick validation function"""
    validator = AppImageValidator(appimage_path, timeout)
    try:
        report = validator.generate_validation_report()
        print("\n" + "=" * 60)
        print(report)
        status = validator.results.get("overall_status") == "passed"
        return bool(status)
    finally:
        validator.cleanup()


if __name__ == "__main__":
    # Setup logging for CLI mode
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    if len(sys.argv) != 2:
        print("Usage: python appimage_validator.py <path_to_appimage>")
        sys.exit(1)

    appimage_path = sys.argv[1]
    logger.info(f"Starting AppImage validation for: {appimage_path}")

    success = validate_appimage(appimage_path)

    if success:
        logger.info("AppImage validation passed successfully")
    else:
        logger.warning("AppImage validation failed")

    sys.exit(0 if success else 1)

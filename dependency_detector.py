#!/usr/bin/env python3
"""
Automatic Dependency Detection for JAR files
Analyzes JAR files and detects external dependencies automatically
"""

import os
import sys
import re
import json
import zipfile
import subprocess
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class DependencyInfo:
    """Information about a detected dependency"""

    group_id: str
    artifact_id: str
    version: Optional[str] = None
    scope: str = "compile"
    file_path: Optional[str] = None
    is_optional: bool = False
    detected_by: Optional[List[str]] = None

    def __post_init__(self):
        if self.detected_by is None:
            self.detected_by = []


class DependencyDetector:
    """Automatic dependency detection for Java applications"""

    def __init__(self):
        self.maven_central_cache = {}
        self.known_patterns = {
            "spring": {
                "group_id": "org.springframework",
                "patterns": [r"spring-(\w+)", r"spring-boot-(\w+)"],
            },
            "apache": {"group_id": "org.apache", "patterns": [r"(\w+)-(\d+)"]},
            "google": {
                "group_id": "com.google",
                "patterns": [r"guava", r"gson", r"protobuf"],
            },
            "junit": {"group_id": "junit", "patterns": [r"junit-(\w+)"]},
        }

    def analyze_jar_dependencies(self, jar_path: str) -> Dict[str, any]:
        """Comprehensive dependency analysis for a JAR file"""
        print(f"🔍 Analyzing dependencies in: {Path(jar_path).name}")

        jar_path = Path(jar_path)
        analysis_result = {
            "jar_path": str(jar_path),
            "manifest_info": self._analyze_manifest(jar_path),
            "class_dependencies": self._analyze_class_dependencies(jar_path),
            "maven_dependencies": self._detect_maven_dependencies(jar_path),
            "library_dependencies": self._detect_library_jars(jar_path),
            "summary": {},
        }

        # Generate summary
        analysis_result["summary"] = self._generate_dependency_summary(analysis_result)

        print(
            f"  📦 Found {len(analysis_result['maven_dependencies'])} Maven dependencies"
        )
        print(
            f"  📚 Found {len(analysis_result['library_dependencies'])} library dependencies"
        )

        return analysis_result

    def _analyze_manifest(self, jar_path: Path) -> Dict[str, str]:
        """Extract and analyze JAR manifest file"""
        manifest_info = {}

        try:
            with zipfile.ZipFile(jar_path, "r") as zf:
                if "META-INF/MANIFEST.MF" in zf.namelist():
                    manifest_content = zf.read("META-INF/MANIFEST.MF").decode(
                        "utf-8", errors="ignore"
                    )

                    # Parse manifest entries
                    for line in manifest_content.split("\n"):
                        if ":" in line:
                            key, value = line.split(":", 1)
                            manifest_info[key.strip().lower()] = value.strip()

                    # Extract Class-Path entries
                    if "class-path" in manifest_info:
                        classpath_entries = manifest_info["class-path"].split()
                        manifest_info["classpath_entries"] = classpath_entries
        except Exception as e:
            print(f"    ⚠️  Error reading manifest: {e}")

        return manifest_info

    def _analyze_class_dependencies(self, jar_path: Path) -> List[str]:
        """Analyze class files to detect imported packages"""
        class_dependencies = set()

        try:
            with zipfile.ZipFile(jar_path, "r") as zf:
                for file_info in zf.infolist():
                    if file_info.filename.endswith(
                        ".class"
                    ) and not file_info.filename.startswith("META-INF/"):
                        try:
                            class_content = zf.read(file_info.filename)
                            dependencies = self._extract_imports_from_class(
                                class_content
                            )
                            class_dependencies.update(dependencies)
                        except Exception:
                            continue
        except Exception as e:
            print(f"    ⚠️  Error analyzing class dependencies: {e}")

        return list(class_dependencies)

    def _extract_imports_from_class(self, class_bytes: bytes) -> List[str]:
        """Extract package imports from compiled class file"""
        # This is a simplified version - in reality, you'd need a proper Java bytecode parser
        # For now, we'll look for common patterns in the bytecode

        dependencies = []
        class_text = class_bytes.decode("utf-8", errors="ignore")

        # Common Java package patterns (simplified)
        common_packages = [
            r"java/(\w+)",
            r"javax/(\w+)",
            r"org/(\w+)/(\w+)",
            r"com/(\w+)/(\w+)",
        ]

        for pattern in common_packages:
            matches = re.findall(pattern, class_text)
            for match in matches:
                if isinstance(match, tuple):
                    dependencies.append("/".join(match))
                else:
                    dependencies.append(match)

        return list(set(dependencies))

    def _detect_maven_dependencies(self, jar_path: Path) -> List[DependencyInfo]:
        """Detect Maven-style dependencies from JAR contents"""
        dependencies = []

        try:
            with zipfile.ZipFile(jar_path, "r") as zf:
                # Look for pom.properties files
                for file_info in zf.infolist():
                    if file_info.filename.endswith("pom.properties"):
                        try:
                            pom_content = zf.read(file_info.filename).decode("utf-8")
                            dep_info = self._parse_pom_properties(
                                pom_content, file_info.filename
                            )
                            if dep_info:
                                dependencies.append(dep_info)
                        except Exception:
                            continue

                # Look for dependency manifests
                for file_info in zf.infolist():
                    if "dependencies.txt" in file_info.filename.lower():
                        try:
                            deps_content = zf.read(file_info.filename).decode("utf-8")
                            more_deps = self._parse_dependencies_list(deps_content)
                            dependencies.extend(more_deps)
                        except Exception:
                            continue

        except Exception as e:
            print(f"    ⚠️  Error detecting Maven dependencies: {e}")

        # Also detect from jar filename patterns
        filename_deps = self._detect_from_filename(jar_path)
        dependencies.extend(filename_deps)

        return dependencies

    def _parse_pom_properties(
        self, content: str, file_path: str
    ) -> Optional[DependencyInfo]:
        """Parse Maven pom.properties file"""
        props = {}
        for line in content.split("\n"):
            if "=" in line and not line.strip().startswith("#"):
                key, value = line.split("=", 1)
                props[key.strip()] = value.strip()

        if "groupId" in props and "artifactId" in props:
            return DependencyInfo(
                group_id=props["groupId"],
                artifact_id=props["artifactId"],
                version=props.get("version"),
                file_path=file_path,
                detected_by=["pom.properties"],
            )

        return None

    def _parse_dependencies_list(self, content: str) -> List[DependencyInfo]:
        """Parse a dependencies list file"""
        dependencies = []

        for line in content.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Try to parse Maven coordinates: groupId:artifactId:version
            if ":" in line:
                parts = line.split(":")
                if len(parts) >= 2:
                    group_id = parts[0]
                    artifact_id = parts[1]
                    version = parts[2] if len(parts) > 2 else None

                    dependencies.append(
                        DependencyInfo(
                            group_id=group_id,
                            artifact_id=artifact_id,
                            version=version,
                            detected_by=["dependencies.list"],
                        )
                    )

        return dependencies

    def _detect_from_filename(self, jar_path: Path) -> List[DependencyInfo]:
        """Detect dependencies based on JAR filename patterns"""
        dependencies = []
        filename = jar_path.stem

        # Check known patterns
        for vendor, info in self.known_patterns.items():
            for pattern in info["patterns"]:
                match = re.search(pattern, filename, re.IGNORECASE)
                if match:
                    artifact_id = match.group(0) if match else filename
                    dependencies.append(
                        DependencyInfo(
                            group_id=info["group_id"],
                            artifact_id=artifact_id,
                            detected_by=["filename.pattern"],
                        )
                    )

        return dependencies

    def _detect_library_jars(self, jar_path: Path) -> List[str]:
        """Detect library JARs embedded in the main JAR"""
        library_jars = []

        try:
            with zipfile.ZipFile(jar_path, "r") as zf:
                for file_info in zf.infolist():
                    if file_info.filename.endswith(".jar") and file_info.filename != "":
                        library_jars.append(file_info.filename)

        except Exception as e:
            print(f"    ⚠️  Error detecting library JARs: {e}")

        return library_jars

    def _generate_dependency_summary(self, analysis_result: Dict) -> Dict[str, any]:
        """Generate a summary of the dependency analysis"""
        summary = {
            "main_class": analysis_result["manifest_info"].get("main-class"),
            "manifest_classpath": analysis_result["manifest_info"].get(
                "classpath_entries", []
            ),
            "total_maven_deps": len(analysis_result["maven_dependencies"]),
            "total_library_deps": len(analysis_result["library_dependencies"]),
            "total_class_deps": len(analysis_result["class_dependencies"]),
            "suggested_classpath": self._generate_suggested_classpath(analysis_result),
            "missing_dependencies": self._detect_missing_dependencies(analysis_result),
        }

        return summary

    def _generate_suggested_classpath(self, analysis_result: Dict) -> List[str]:
        """Generate suggested classpath entries"""
        classpath_suggestions = []

        # Add manifest classpath entries
        classpath_suggestions.extend(
            analysis_result["manifest_info"].get("classpath_entries", [])
        )

        # Add detected library JARs
        classpath_suggestions.extend(analysis_result["library_dependencies"])

        # Add Maven dependencies (convert to potential JAR names)
        for dep in analysis_result["maven_dependencies"]:
            jar_name = f"{dep.artifact_id}-{dep.version or ''}.jar"
            classpath_suggestions.append(jar_name)

        return list(set(classpath_suggestions))  # Remove duplicates

    def _detect_missing_dependencies(self, analysis_result: Dict) -> List[str]:
        """Detect potentially missing dependencies based on class analysis"""
        missing = []
        class_deps = set(analysis_result["class_dependencies"])

        # Common Java packages that should be available
        standard_packages = {
            "java/lang",
            "java/util",
            "java/io",
            "java/net",
            "javax/swing",
            "javax/xml",
            "org/w3c/dom",
        }

        # Look for non-standard packages
        for dep in class_deps:
            if not any(dep.startswith(std_pkg) for std_pkg in standard_packages):
                if not dep.startswith(
                    analysis_result["manifest_info"]
                    .get("main-class", "")
                    .rsplit(".", 1)[0]
                ):
                    missing.append(dep.replace("/", "."))

        return missing

    def suggest_dependency_jars(
        self, jar_path: str, search_paths: Optional[List[str]] = None
    ) -> List[str]:
        """Suggest dependency JAR files that might be needed"""
        analysis = self.analyze_jar_dependencies(jar_path)
        suggestions = []

        if search_paths is None:
            search_paths = [
                ".",
                "./lib",
                "./libs",
                "./target/lib",
                "./build/libs",
                "/usr/share/java",
                "/usr/local/share/java",
            ]

        # Search for potential dependency JARs
        for dep in analysis["maven_dependencies"]:
            jar_pattern = f"*{dep.artifact_id}*.jar"

            for search_path in search_paths:
                search_dir = Path(search_path)
                if search_dir.exists():
                    matching_jars = list(search_dir.glob(jar_pattern))
                    suggestions.extend([str(jar) for jar in matching_jars])

        return list(set(suggestions))

    def generate_dependency_report(
        self, jar_path: str, output_format: str = "text"
    ) -> str:
        """Generate a comprehensive dependency report"""
        analysis = self.analyze_jar_dependencies(jar_path)

        if output_format.lower() == "json":
            return json.dumps(analysis, indent=2)

        # Text format
        report_lines = [
            f"🔍 Dependency Analysis Report",
            f"📁 JAR: {analysis['jar_path']}",
            f"",
            f"📋 MANIFEST INFORMATION:",
            f"  Main Class: {analysis['manifest_info'].get('main-class', 'Not found')}",
            f"  Class-Path entries: {len(analysis['manifest_info'].get('classpath_entries', []))}",
            f"",
            f"📦 MAVEN DEPENDENCIES ({len(analysis['maven_dependencies'])}):",
        ]

        for dep in analysis["maven_dependencies"]:
            version_info = f":{dep.version}" if dep.version else ""
            report_lines.append(
                f"  • {dep.group_id}:{dep.artifact_id}{version_info} (detected by: {', '.join(dep.detected_by)})"
            )

        report_lines.extend(
            [f"", f"📚 EMBEDDED LIBRARIES ({len(analysis['library_dependencies'])}):"]
        )

        for lib in analysis["library_dependencies"]:
            report_lines.append(f"  • {lib}")

        report_lines.extend(
            [
                f"",
                f"🎯 SUMMARY:",
                f"  Total Maven dependencies: {analysis['summary']['total_maven_deps']}",
                f"  Total embedded libraries: {analysis['summary']['total_library_deps']}",
                f"  Total class dependencies: {analysis['summary']['total_class_deps']}",
                f"  Missing dependencies detected: {len(analysis['summary']['missing_dependencies'])}",
                f"",
                f"💡 SUGGESTED CLASSPATH:",
            ]
        )

        for cp_entry in analysis["summary"]["suggested_classpath"][
            :10
        ]:  # Limit to first 10
            report_lines.append(f"  • {cp_entry}")

        if analysis["summary"]["missing_dependencies"]:
            report_lines.extend([f"", f"⚠️  POTENTIALLY MISSING DEPENDENCIES:"])
            for missing in analysis["summary"]["missing_dependencies"][
                :5
            ]:  # Limit to first 5
                report_lines.append(f"  • {missing}")

        return "\n".join(report_lines)


# Utility functions for common dependency detection tasks
def detect_dependencies(jar_path: str) -> Dict[str, any]:
    """Quick dependency detection"""
    detector = DependencyDetector()
    return detector.analyze_jar_dependencies(jar_path)


def suggest_classpath(jar_path: str, search_paths: List[str] = None) -> List[str]:
    """Get suggested classpath for a JAR"""
    detector = DependencyDetector()
    analysis = detector.analyze_jar_dependencies(jar_path)
    return analysis["summary"]["suggested_classpath"]


def generate_dependency_report(jar_path: str) -> str:
    """Generate text dependency report"""
    detector = DependencyDetector()
    return detector.generate_dependency_report(jar_path, "text")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python dependency_detector.py <jar_file>")
        sys.exit(1)

    jar_file = sys.argv[1]
    detector = DependencyDetector()
    report = detector.generate_dependency_report(jar_file)
    print(report)

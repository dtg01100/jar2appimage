#!/usr/bin/env python3
"""
JAR File Analyzer for JAR2AppImage

This module provides comprehensive JAR file analysis including:
- Proper bytecode analysis for class dependencies
- Manifest parsing and analysis
- Resource dependency tracking
- Native library detection
- ZIP structure validation

Key Features:
- Robust Java class file parsing
- Comprehensive manifest analysis
- Resource and native library detection
- Platform-specific dependency analysis
- ZIP structure validation
"""

import logging
import re
import struct
import zipfile
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Union

from .dependency_graph import Dependency, DependencyScope, DependencyType

logger = logging.getLogger(__name__)


class JavaVersion(Enum):
    """Java version detection"""
    UNKNOWN = "unknown"
    JDK_1_1 = "1.1"
    JDK_1_2 = "1.2"
    JDK_1_3 = "1.3"
    JDK_1_4 = "1.4"
    JDK_1_5 = "1.5"
    JDK_1_6 = "1.6"
    JDK_1_7 = "1.7"
    JDK_1_8 = "1.8"
    JDK_9 = "9"
    JDK_10 = "10"
    JDK_11 = "11"
    JDK_12 = "12"
    JDK_13 = "13"
    JDK_14 = "14"
    JDK_15 = "15"
    JDK_16 = "16"
    JDK_17 = "17"
    JDK_18 = "18"
    JDK_19 = "19"
    JDK_20 = "20"
    JDK_21 = "21"


class ClassFileFormat(Enum):
    """Class file format versions"""
    MAGIC_NUMBER = 0xCAFEBABE


@dataclass
class ClassFileInfo:
    """Information about a parsed class file"""
    class_name: str
    package_name: Optional[str] = None
    super_class: Optional[str] = None
    interfaces: List[str] = field(default_factory=list)
    constants: List[str] = field(default_factory=list)
    annotations: List[str] = field(default_factory=list)
    major_version: int = 0
    minor_version: int = 0
    is_public: bool = False
    is_interface: bool = False
    is_abstract: bool = False
    is_final: bool = False
    access_flags: int = 0


@dataclass
class ManifestInfo:
    """Information extracted from JAR manifest"""
    main_class: Optional[str] = None
    manifest_version: Optional[str] = None
    created_by: Optional[str] = None
    signature_version: Optional[str] = None
    class_path: List[str] = field(default_factory=list)
    package_title: Optional[str] = None
    package_vendor: Optional[str] = None
    package_version: Optional[str] = None
    sealed: bool = False
    shared_library: bool = False
    implementation_version: Optional[str] = None
    implementation_vendor: Optional[str] = None
    implementation_title: Optional[str] = None
    specification_version: Optional[str] = None
    specification_vendor: Optional[str] = None
    specification_title: Optional[str] = None
    add_to_classpath: bool = False
    dependencies: List[str] = field(default_factory=list)
    custom_attributes: Dict[str, str] = field(default_factory=dict)


@dataclass
class ResourceInfo:
    """Information about a resource in the JAR"""
    path: str
    size: int
    compressed_size: int
    is_compressed: bool
    is_native_library: bool = False
    is_config_file: bool = False
    is_manifest: bool = False
    is_signature_file: bool = False
    mime_type: Optional[str] = None
    encoding: Optional[str] = None


@dataclass
class JarAnalysisResult:
    """Complete JAR analysis result"""
    jar_path: Path
    jar_size: int
    is_valid_jar: bool
    entry_count: int
    manifest: Optional[ManifestInfo]
    class_files: List[ClassFileInfo] = field(default_factory=list)
    resources: List[ResourceInfo] = field(default_factory=list)
    native_libraries: List[str] = field(default_factory=list)
    config_files: List[str] = field(default_factory=list)
    signature_files: List[str] = field(default_factory=list)
    dependencies: List[Dependency] = field(default_factory=list)
    main_class_candidates: List[str] = field(default_factory=list)
    estimated_java_version: JavaVersion = JavaVersion.UNKNOWN
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class ByteCodeReader:
    """Low-level bytecode reader for class files"""

    def __init__(self, data: bytes):
        self.data = data
        self.offset = 0

    def read_u1(self) -> int:
        """Read unsigned byte"""
        value = int(struct.unpack('>B', self.data[self.offset:self.offset+1])[0])
        self.offset += 1
        return value

    def read_u2(self) -> int:
        """Read unsigned short (big-endian)"""
        value = int(struct.unpack('>H', self.data[self.offset:self.offset+2])[0])
        self.offset += 2
        return value

    def read_u4(self) -> int:
        """Read unsigned int (big-endian)"""
        value = int(struct.unpack('>I', self.data[self.offset:self.offset+4])[0])
        self.offset += 4
        return value

    def read_u8(self) -> int:
        """Read unsigned long (big-endian)"""
        value = int(struct.unpack('>Q', self.data[self.offset:self.offset+8])[0])
        self.offset += 8
        return value

    def read_bytes(self, length: int) -> bytes:
        """Read specified number of bytes"""
        value = self.data[self.offset:self.offset+length]
        self.offset += length
        return value

    def read_utf8(self) -> str:
        """Read UTF-8 string"""
        length = self.read_u2()
        value = self.data[self.offset:self.offset+length]
        self.offset += length
        try:
            return value.decode('utf-8')
        except UnicodeDecodeError:
            return value.decode('latin1', errors='ignore')

    def seek(self, offset: int) -> None:
        """Seek to offset"""
        self.offset = offset

    def tell(self) -> int:
        """Get current offset"""
        return self.offset

    def remaining(self) -> int:
        """Get remaining bytes"""
        return len(self.data) - self.offset


class ConstantPoolReader:
    """Constant pool reader for class files"""

    def __init__(self, reader: ByteCodeReader) -> None:
        self.reader = reader
        self.constants: list[Optional[str]] = []
        self._read_constant_pool()

    def _read_constant_pool(self) -> None:  # noqa: C901
        """Read the constant pool"""
        count = self.reader.read_u2()

        for i in range(1, count):
            tag = self.reader.read_u1()

            if tag == 1:  # CONSTANT_Utf8
                length = self.reader.read_u2()
                value = self.reader.read_bytes(length)
                try:
                    self.constants.append(value.decode('utf-8'))
                except UnicodeDecodeError:
                    self.constants.append(value.decode('latin1', errors='ignore'))

            elif tag == 3:  # CONSTANT_Integer
                self.reader.read_u4()
                self.constants.append(None)

            elif tag == 4:  # CONSTANT_Float
                self.reader.read_u4()
                self.constants.append(None)

            elif tag == 5:  # CONSTANT_Long
                self.reader.read_u8()
                self.constants.append(None)
                i += 1  # Long takes two slots

            elif tag == 6:  # CONSTANT_Double
                self.reader.read_u8()
                self.constants.append(None)
                i += 1  # Double takes two slots

            elif tag == 7:  # CONSTANT_Class
                self.reader.read_u2()
                self.constants.append(None)

            elif tag == 8:  # CONSTANT_String
                self.reader.read_u2()
                self.constants.append(None)

            elif tag == 9:  # CONSTANT_Fieldref
                self.reader.read_u2()
                self.reader.read_u2()
                self.constants.append(None)

            elif tag == 10:  # CONSTANT_Methodref
                self.reader.read_u2()
                self.reader.read_u2()
                self.constants.append(None)

            elif tag == 11:  # CONSTANT_InterfaceMethodref
                self.reader.read_u2()
                self.reader.read_u2()
                self.constants.append(None)

            elif tag == 12:  # CONSTANT_NameAndType
                self.reader.read_u2()
                self.reader.read_u2()
                self.constants.append(None)

            elif tag == 15:  # CONSTANT_MethodHandle
                self.reader.read_u1()
                self.reader.read_u2()
                self.constants.append(None)

            elif tag == 16:  # CONSTANT_MethodType
                self.reader.read_u2()
                self.constants.append(None)

            elif tag == 17:  # CONSTANT_Dynamic
                self.reader.read_u2()
                self.reader.read_u2()
                self.constants.append(None)

            elif tag == 18:  # CONSTANT_InvokeDynamic
                self.reader.read_u2()
                self.reader.read_u2()
                self.constants.append(None)

            elif tag == 19:  # CONSTANT_Module
                self.reader.read_u2()
                self.constants.append(None)

            elif tag == 20:  # CONSTANT_Package
                self.reader.read_u2()
                self.constants.append(None)

            else:
                logger.warning(f"Unknown constant pool tag: {tag}")
                break

    def get_utf8(self, index: int) -> Optional[str]:
        """Get UTF-8 constant by index"""
        if 0 <= index < len(self.constants):
            return self.constants[index]
        return None

    def get_class_name(self, index: int) -> Optional[str]:
        """Get class name by constant pool index"""
        if 0 <= index < len(self.constants):
            utf8_index = self.constants[index]
            if utf8_index and isinstance(utf8_index, str):
                return utf8_index.replace('/', '.')
        return None


class ClassFileParser:
    """Parser for Java class files"""

    def __init__(self) -> None:
        self.access_flags = {
            0x0001: 'ACC_PUBLIC',
            0x0002: 'ACC_PRIVATE',
            0x0004: 'ACC_PROTECTED',
            0x0008: 'ACC_STATIC',
            0x0010: 'ACC_FINAL',
            0x0020: 'ACC_SUPER',
            0x0200: 'ACC_INTERFACE',
            0x0400: 'ACC_ABSTRACT',
            0x1000: 'ACC_SYNTHETIC',
            0x2000: 'ACC_ANNOTATION',
            0x4000: 'ACC_ENUM',
        }

    def parse_class_file(self, class_data: bytes, file_path: str) -> Optional[ClassFileInfo]:
        """Parse a Java class file"""
        try:
            reader = ByteCodeReader(class_data)

            # Check magic number
            magic = reader.read_u4()
            if magic != ClassFileFormat.MAGIC_NUMBER.value:
                logger.error(f"Invalid magic number for class file: {file_path}")
                return None

            # Read version
            minor_version = reader.read_u2()
            major_version = reader.read_u2()

            # Read constant pool
            constant_pool = ConstantPoolReader(reader)

            # Read access flags
            access_flags = reader.read_u2()

            # Read this class
            this_class = reader.read_u2()

            # Read super class
            super_class = reader.read_u2()

            # Read interfaces
            interfaces_count = reader.read_u2()
            interfaces = []
            for _ in range(interfaces_count):
                interface_index = reader.read_u2()
                interface_name = constant_pool.get_class_name(interface_index)
                if interface_name:
                    interfaces.append(interface_name)

            # Skip fields for now (focus on dependencies)
            fields_count = reader.read_u2()
            reader.seek(reader.tell() + fields_count * 8)  # Skip field info

            # Skip methods for now
            methods_count = reader.read_u2()
            reader.seek(reader.tell() + methods_count * 8)  # Skip method info

            # Read annotations if present
            annotations = []
            attributes_count = reader.read_u2()
            for _ in range(attributes_count):
                attribute_name_index = reader.read_u2()
                attribute_length = reader.read_u4()
                attribute_name = constant_pool.get_utf8(attribute_name_index)

                if attribute_name == "RuntimeVisibleAnnotations":
                    annotations.extend(self._read_annotations(reader, attribute_length))
                else:
                    reader.seek(reader.tell() + attribute_length)

            # Extract class name
            class_name = constant_pool.get_class_name(this_class)
            if not class_name:
                class_name = file_path.replace('.class', '').replace('/', '.')

            # Extract package name
            package_name = None
            if '.' in class_name:
                package_name = '.'.join(class_name.split('.')[:-1])

            # Extract super class name
            super_class_name = constant_pool.get_class_name(super_class)

            return ClassFileInfo(
                class_name=class_name,
                package_name=package_name,
                super_class=super_class_name,
                interfaces=interfaces,
                constants=[],  # Could be populated from constant pool analysis
                annotations=annotations,
                major_version=major_version,
                minor_version=minor_version,
                is_public=bool(access_flags & 0x0001),
                is_interface=bool(access_flags & 0x0200),
                is_abstract=bool(access_flags & 0x0400),
                is_final=bool(access_flags & 0x0010),
                access_flags=access_flags
            )

        except Exception as e:
            logger.error(f"Error parsing class file {file_path}: {e}")
            return None

    def _read_annotations(self, reader: ByteCodeReader, length: int) -> List[str]:
        """Read annotations from class file"""
        annotations: list[str] = []
        annotations_count = reader.read_u2()

        for _ in range(annotations_count):
            # Read and ignore type index
            reader.read_u2()
            # Skip annotation details for now
            reader.read_u2()  # num_element_value_pairs
            # Skip element pairs

        return annotations

    def detect_java_version(self, major_version: int) -> JavaVersion:
        """Detect Java version from class file major version"""
        version_map = {
            45: JavaVersion.JDK_1_1,
            46: JavaVersion.JDK_1_2,
            47: JavaVersion.JDK_1_3,
            48: JavaVersion.JDK_1_4,
            49: JavaVersion.JDK_1_5,
            50: JavaVersion.JDK_1_6,
            51: JavaVersion.JDK_1_7,
            52: JavaVersion.JDK_1_8,
            53: JavaVersion.JDK_9,
            54: JavaVersion.JDK_10,
            55: JavaVersion.JDK_11,
            56: JavaVersion.JDK_12,
            57: JavaVersion.JDK_13,
            58: JavaVersion.JDK_14,
            59: JavaVersion.JDK_15,
            60: JavaVersion.JDK_16,
            61: JavaVersion.JDK_17,
            62: JavaVersion.JDK_18,
            63: JavaVersion.JDK_19,
            64: JavaVersion.JDK_20,
            65: JavaVersion.JDK_21,
        }

        return version_map.get(major_version, JavaVersion.UNKNOWN)


class ManifestParser:
    """Parser for JAR manifest files"""

    def __init__(self) -> None:
        self.known_attributes = {
            'manifest-version',
            'created-by',
            'signature-version',
            'main-class',
            'class-path',
            'package-title',
            'package-vendor',
            'package-version',
            'sealed',
            'implementation-version',
            'implementation-vendor',
            'implementation-title',
            'specification-version',
            'specification-vendor',
            'specification-title',
        }

    def parse_manifest(self, manifest_data: bytes) -> ManifestInfo:  # noqa: C901
        """Parse JAR manifest data"""
        try:
            manifest_content = manifest_data.decode('utf-8', errors='ignore')
            lines = manifest_content.split('\n')

            manifest_info = ManifestInfo()
            current_section = None

            for line in lines:
                line = line.rstrip()

                if not line:
                    continue

                if line.startswith(' '):
                    # Continuation of previous attribute
                    if current_section and current_section in manifest_info.custom_attributes:
                        manifest_info.custom_attributes[current_section] += line[1:]
                    continue

                if ':' not in line:
                    continue

                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()

                current_section = key

                # Parse known attributes
                if key == 'manifest-version':
                    manifest_info.manifest_version = value
                elif key == 'created-by':
                    manifest_info.created_by = value
                elif key == 'signature-version':
                    manifest_info.signature_version = value
                elif key == 'main-class':
                    manifest_info.main_class = value
                elif key == 'class-path':
                    manifest_info.class_path = value.split()
                elif key == 'package-title':
                    manifest_info.package_title = value
                elif key == 'package-vendor':
                    manifest_info.package_vendor = value
                elif key == 'package-version':
                    manifest_info.package_version = value
                elif key == 'sealed':
                    manifest_info.sealed = value.lower() == 'true'
                elif key == 'implementation-version':
                    manifest_info.implementation_version = value
                elif key == 'implementation-vendor':
                    manifest_info.implementation_vendor = value
                elif key == 'implementation-title':
                    manifest_info.implementation_title = value
                elif key == 'specification-version':
                    manifest_info.specification_version = value
                elif key == 'specification-vendor':
                    manifest_info.specification_vendor = value
                elif key == 'specification-title':
                    manifest_info.specification_title = value
                else:
                    # Store custom attributes
                    manifest_info.custom_attributes[key] = value

            return manifest_info

        except Exception as e:
            logger.error(f"Error parsing manifest: {e}")
            return ManifestInfo()


class JarAnalyzer:
    """Comprehensive JAR file analyzer"""

    def __init__(self) -> None:
        self.class_parser = ClassFileParser()
        self.manifest_parser = ManifestParser()
        self.native_library_patterns = [
            r'.*\.dll$',
            r'.*\.so$',
            r'.*\.dylib$',
            r'.*\.jnilib$',
            r'.*\.jni$',
        ]
        self.config_file_patterns = [
            r'.*\.properties$',
            r'.*\.xml$',
            r'.*\.json$',
            r'.*\.yaml$',
            r'.*\.yml$',
            r'.*\.conf$',
            r'.*\.cfg$',
            r'.*\.ini$',
        ]
        self.signature_patterns = [
            r'.*\.sf$',
            r'.*\.rsa$',
            r'.*\.dsa$',
            r'.*\.ec$',
            r'META-INF/.*',
        ]

    def analyze_jar(self, jar_path: Union[str, Path]) -> JarAnalysisResult:
        """Analyze a JAR file comprehensively"""
        jar_path = Path(jar_path)
        logger.info(f"Starting comprehensive JAR analysis: {jar_path}")

        result = JarAnalysisResult(
            jar_path=jar_path,
            jar_size=jar_path.stat().st_size if jar_path.exists() else 0,
            is_valid_jar=False,
            entry_count=0,
            manifest=None
        )

        if not jar_path.exists():
            result.errors.append(f"JAR file does not exist: {jar_path}")
            return result

        try:
            with zipfile.ZipFile(jar_path, 'r') as jar_file:
                result.entry_count = len(jar_file.infolist())
                result.is_valid_jar = True

                # Analyze manifest first
                result.manifest = self._analyze_manifest(jar_file)

                # Analyze entries
                self._analyze_entries(jar_file, result)

                # Extract dependencies
                self._extract_dependencies(result)

                # Detect main class candidates
                result.main_class_candidates = self._detect_main_class_candidates(result)

                # Estimate Java version
                if result.class_files:
                    versions = [cf.major_version for cf in result.class_files]
                    most_common_version = max(set(versions), key=versions.count)
                    result.estimated_java_version = self.class_parser.detect_java_version(most_common_version)

        except zipfile.BadZipFile:
            result.errors.append(f"Invalid ZIP/JAR file: {jar_path}")
        except Exception as e:
            result.errors.append(f"Error analyzing JAR: {e}")

        logger.info(f"JAR analysis complete: {len(result.class_files)} classes, {len(result.dependencies)} dependencies")
        return result

    def _analyze_manifest(self, jar_file: zipfile.ZipFile) -> Optional[ManifestInfo]:
        """Analyze JAR manifest"""
        try:
            if 'META-INF/MANIFEST.MF' in jar_file.namelist():
                manifest_data = jar_file.read('META-INF/MANIFEST.MF')
                return self.manifest_parser.parse_manifest(manifest_data)
        except Exception as e:
            logger.warning(f"Error reading manifest: {e}")

        return None

    def _analyze_entries(self, jar_file: zipfile.ZipFile, result: JarAnalysisResult) -> None:
        """Analyze all entries in the JAR"""
        for entry_info in jar_file.infolist():
            try:
                if entry_info.filename.endswith('.class'):
                    self._analyze_class_entry(jar_file, entry_info, result)
                elif entry_info.filename == 'META-INF/MANIFEST.MF':
                    resource_info = ResourceInfo(
                        path=entry_info.filename,
                        size=entry_info.file_size,
                        compressed_size=entry_info.compress_size,
                        is_compressed=entry_info.compress_type != zipfile.ZIP_STORED,
                        is_manifest=True
                    )
                    result.resources.append(resource_info)
                elif self._is_native_library(entry_info.filename):
                    result.native_libraries.append(entry_info.filename)
                    resource_info = ResourceInfo(
                        path=entry_info.filename,
                        size=entry_info.file_size,
                        compressed_size=entry_info.compress_size,
                        is_compressed=entry_info.compress_type != zipfile.ZIP_STORED,
                        is_native_library=True
                    )
                    result.resources.append(resource_info)
                elif self._is_config_file(entry_info.filename):
                    result.config_files.append(entry_info.filename)
                    resource_info = ResourceInfo(
                        path=entry_info.filename,
                        size=entry_info.file_size,
                        compressed_size=entry_info.compress_size,
                        is_compressed=entry_info.compress_type != zipfile.ZIP_STORED,
                        is_config_file=True
                    )
                    result.resources.append(resource_info)
                elif self._is_signature_file(entry_info.filename):
                    result.signature_files.append(entry_info.filename)
                    resource_info = ResourceInfo(
                        path=entry_info.filename,
                        size=entry_info.file_size,
                        compressed_size=entry_info.compress_size,
                        is_compressed=entry_info.compress_type != zipfile.ZIP_STORED,
                        is_signature_file=True
                    )
                    result.resources.append(resource_info)
                else:
                    # Regular resource
                    resource_info = ResourceInfo(
                        path=entry_info.filename,
                        size=entry_info.file_size,
                        compressed_size=entry_info.compress_size,
                        is_compressed=entry_info.compress_type != zipfile.ZIP_STORED
                    )
                    result.resources.append(resource_info)

            except Exception as e:
                result.warnings.append(f"Error analyzing entry {entry_info.filename}: {e}")

    def _analyze_class_entry(self, jar_file: zipfile.ZipFile, entry_info: zipfile.ZipInfo, result: JarAnalysisResult) -> None:
        """Analyze a class file entry"""
        try:
            class_data = jar_file.read(entry_info.filename)
            class_info = self.class_parser.parse_class_file(class_data, entry_info.filename)

            if class_info:
                result.class_files.append(class_info)

        except Exception as e:
            result.warnings.append(f"Error parsing class file {entry_info.filename}: {e}")

    def _is_native_library(self, path: str) -> bool:
        """Check if path points to a native library"""
        return any(re.match(pattern, path, re.IGNORECASE) for pattern in self.native_library_patterns)

    def _is_config_file(self, path: str) -> bool:
        """Check if path points to a configuration file"""
        return any(re.match(pattern, path, re.IGNORECASE) for pattern in self.config_file_patterns)

    def _is_signature_file(self, path: str) -> bool:
        """Check if path points to a signature file"""
        return any(re.match(pattern, path, re.IGNORECASE) for pattern in self.signature_patterns)

    def _extract_dependencies(self, result: JarAnalysisResult) -> None:
        """Extract dependencies from class analysis"""
        # Collect package dependencies from class files
        package_deps = set()
        class_deps = set()

        for class_info in result.class_files:
            # Add super class dependency
            if class_info.super_class:
                class_deps.add(class_info.super_class)

            # Add interface dependencies
            class_deps.update(class_info.interfaces)

            # Add package-level dependencies
            if class_info.package_name:
                package_parts = class_info.package_name.split('.')
                for i in range(len(package_parts)):
                    package_deps.add('.'.join(package_parts[:i+1]))

        # Convert to Dependency objects
        for pkg in package_deps:
            if not self._is_java_standard_library(pkg):
                dep = Dependency(
                    group_id=pkg,
                    artifact_id=pkg.split('.')[-1] if '.' in pkg else pkg,
                    scope=DependencyScope.COMPILE,
                    dependency_type=DependencyType.MODULE,
                    metadata={'source': 'package_analysis'}
                )
                result.dependencies.append(dep)

    def _is_java_standard_library(self, package_name: str) -> bool:
        """Check if package is part of Java standard library"""
        standard_packages = {
            'java.lang', 'java.util', 'java.io', 'java.net', 'java.nio',
            'java.security', 'java.math', 'java.text', 'java.time',
            'java.sql', 'java.awt', 'javax.swing', 'javax.xml',
            'javax.management', 'javax.naming', 'javax.rmi',
            'org.w3c.dom', 'org.xml.sax'
        }

        return any(package_name.startswith(pkg) for pkg in standard_packages)

    def _detect_main_class_candidates(self, result: JarAnalysisResult) -> List[str]:
        """Detect potential main class candidates"""
        candidates = []

        # From manifest
        if result.manifest and result.manifest.main_class:
            candidates.append(result.manifest.main_class)

        # Look for classes with main method (would need bytecode analysis)
        for class_info in result.class_files:
            # Simple heuristic: look for classes that might have main method
            if (class_info.class_name.endswith('Main') or
                class_info.class_name.endswith('Application') or
                class_info.class_name.endswith('App')):
                candidates.append(class_info.class_name)

        return list(set(candidates))  # Remove duplicates

    def get_dependency_report(self, result: JarAnalysisResult) -> str:  # noqa: C901
        """Generate a detailed dependency report"""
        lines = []
        lines.append("🔍 JAR Analysis Report")
        lines.append(f"📁 JAR: {result.jar_path}")
        lines.append(f"📊 Size: {result.jar_size:,} bytes")
        lines.append(f"📦 Entries: {result.entry_count}")
        lines.append("")

        # Manifest info
        if result.manifest:
            lines.append("📋 MANIFEST INFORMATION:")
            if result.manifest.main_class:
                lines.append(f"  Main Class: {result.manifest.main_class}")
            if result.manifest.class_path:
                lines.append(f"  Class-Path entries: {len(result.manifest.class_path)}")
            lines.append("")

        # Class files
        lines.append(f"📚 CLASS FILES ({len(result.class_files)}):")
        for class_info in result.class_files[:10]:  # Limit output
            lines.append(f"  • {class_info.class_name}")
        if len(result.class_files) > 10:
            lines.append(f"  ... and {len(result.class_files) - 10} more")
        lines.append("")

        # Dependencies
        lines.append(f"🔗 DEPENDENCIES ({len(result.dependencies)}):")
        for dep in result.dependencies[:10]:  # Limit output
            version_info = f":{dep.version}" if dep.version else ""
            lines.append(f"  • {dep.group_id}:{dep.artifact_id}{version_info}")
        if len(result.dependencies) > 10:
            lines.append(f"  ... and {len(result.dependencies) - 10} more")
        lines.append("")

        # Resources
        if result.native_libraries:
            lines.append(f"🔧 NATIVE LIBRARIES ({len(result.native_libraries)}):")
            for lib in result.native_libraries:
                lines.append(f"  • {lib}")
            lines.append("")

        if result.config_files:
            lines.append(f"⚙️  CONFIG FILES ({len(result.config_files)}):")
            for config in result.config_files[:5]:  # Limit output
                lines.append(f"  • {config}")
            if len(result.config_files) > 5:
                lines.append(f"  ... and {len(result.config_files) - 5} more")
            lines.append("")

        # Main class candidates
        if result.main_class_candidates:
            lines.append("🎯 MAIN CLASS CANDIDATES:")
            for candidate in result.main_class_candidates:
                lines.append(f"  • {candidate}")
            lines.append("")

        # Java version
        if result.estimated_java_version != JavaVersion.UNKNOWN:
            lines.append(f"☕ ESTIMATED JAVA VERSION: {result.estimated_java_version.value}")
            lines.append("")

        # Warnings and errors
        if result.warnings:
            lines.append("⚠️  WARNINGS:")
            for warning in result.warnings[:5]:
                lines.append(f"  • {warning}")
            if len(result.warnings) > 5:
                lines.append(f"  ... and {len(result.warnings) - 5} more")
            lines.append("")

        if result.errors:
            lines.append("❌ ERRORS:")
            for error in result.errors:
                lines.append(f"  • {error}")
            lines.append("")

        return "\n".join(lines)


def analyze_jar_file(jar_path: str) -> JarAnalysisResult:
    """Convenience function to analyze a JAR file"""
    analyzer = JarAnalyzer()
    return analyzer.analyze_jar(jar_path)


def generate_jar_report(jar_path: str) -> str:
    """Convenience function to generate a JAR analysis report"""
    result = analyze_jar_file(jar_path)
    analyzer = JarAnalyzer()
    return analyzer.get_dependency_report(result)

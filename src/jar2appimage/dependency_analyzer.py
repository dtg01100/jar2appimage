#!/usr/bin/env python3
"""
Comprehensive Dependency Analyzer for JAR2AppImage

This is the main orchestrator that ties together all dependency analysis components:
- JAR analysis and bytecode parsing
- Dependency graph management
- Conflict resolution and bundling decisions
- Integration with the AppImage bundling process

Key Features:
- End-to-end dependency analysis workflow
- Integration with existing JAR2AppImage bundling
- CLI support for dependency analysis
- Comprehensive reporting and visualization
- Configurable analysis options
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .dependency_graph import (
    Dependency,
    DependencyGraph,
    DependencyScope,
    DependencyType,
)
from .dependency_resolver import (
    ConflictResolutionStrategy,
    DependencyResolver,
    Platform,
    ResolutionContext,
    ResolutionResult,
)
from .jar_analyzer import JarAnalysisResult, JarAnalyzer

logger = logging.getLogger(__name__)


@dataclass
class AnalysisConfiguration:
    """Configuration for dependency analysis"""
    # Analysis options
    analyze_bytecode: bool = True
    analyze_manifest: bool = True
    analyze_resources: bool = True
    resolve_transitive: bool = True

    # Resolution options
    conflict_resolution_strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.PREFER_LATEST
    target_platform: Platform = Platform.ANY
    java_version: Optional[str] = None
    bundle_native_libraries: bool = True
    bundle_optional_deps: bool = False

    # Filtering options
    exclude_test_deps: bool = True
    exclude_provided_deps: bool = True
    exclude_optional_deps: bool = False
    max_dependency_depth: int = 10

    # Output options
    generate_reports: bool = True
    output_format: str = "text"  # text, json, html
    include_graphviz: bool = False
    verbose: bool = False


@dataclass
class ComprehensiveAnalysisResult:
    """Result of comprehensive dependency analysis"""
    jar_analysis: Optional[JarAnalysisResult] = None
    dependency_graph: Optional[DependencyGraph] = None
    resolution_result: Optional[ResolutionResult] = None
    bundling_decisions: Dict[str, Any] = field(default_factory=dict)
    classpath: List[str] = field(default_factory=list)
    analysis_metadata: Dict[str, Any] = field(default_factory=dict)
    reports: Dict[str, str] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class ComprehensiveDependencyAnalyzer:
    """Main dependency analysis orchestrator"""

    def __init__(self, config: Optional[AnalysisConfiguration] = None):
        self.config = config or AnalysisConfiguration()
        self.jar_analyzer = JarAnalyzer()
        self.dependency_resolver = DependencyResolver()

    def analyze_application(self, jar_paths: List[str],
                           main_class: Optional[str] = None) -> ComprehensiveAnalysisResult:
        """Perform comprehensive dependency analysis for one or more JAR files"""
        logger.info(f"Starting comprehensive analysis of {len(jar_paths)} JAR files")

        if not jar_paths:
            raise ValueError("No JAR files provided for analysis")

        result = ComprehensiveAnalysisResult()

        try:
            # Step 1: Analyze all JAR files
            jar_results = []
            for jar_path in jar_paths:
                try:
                    jar_result = self.jar_analyzer.analyze_jar(jar_path)
                    jar_results.append(jar_result)

                    if jar_result.errors:
                        result.errors.extend([f"{jar_path}: {error}" for error in jar_result.errors])

                    if jar_result.warnings:
                        result.warnings.extend([f"{jar_path}: {warning}" for warning in jar_result.warnings])

                except Exception as e:
                    error_msg = f"Failed to analyze JAR {jar_path}: {e}"
                    result.errors.append(error_msg)
                    logger.error(error_msg)

            if not jar_results:
                raise ValueError("No JAR files could be analyzed successfully")

            # Step 2: Merge analysis results
            merged_analysis = self._merge_jar_analyses(jar_results)
            result.jar_analysis = merged_analysis

            # Step 3: Build comprehensive dependency graph
            all_dependencies = self._extract_all_dependencies(jar_results)
            dependency_graph = self._build_comprehensive_graph(all_dependencies)
            result.dependency_graph = dependency_graph

            # Step 4: Resolve dependencies
            resolution_context = self._create_resolution_context()
            resolution_result = self.dependency_resolver.resolve_dependencies(
                all_dependencies, resolution_context
            )
            result.resolution_result = resolution_result

            # Step 5: Generate bundling decisions
            bundling_decisions = self._generate_bundling_strategy(resolution_result, merged_analysis)
            result.bundling_decisions = bundling_decisions

            # Step 6: Generate classpath
            result.classpath = self.dependency_resolver.generate_classpath(resolution_result.resolved_dependencies)

            # Step 7: Generate reports and recommendations
            result.reports = self._generate_reports(result)
            result.recommendations = self._generate_recommendations(result)

            # Step 8: Add metadata
            result.analysis_metadata = self._generate_metadata(result)

        except Exception as e:
            error_msg = f"Comprehensive analysis failed: {e}"
            result.errors.append(error_msg)
            logger.error(error_msg)

        logger.info(f"Comprehensive analysis complete: {len(result.recommendations)} recommendations generated")
        return result

    def _merge_jar_analyses(self, jar_results: List[JarAnalysisResult]) -> JarAnalysisResult:
        """Merge multiple JAR analysis results"""
        if len(jar_results) == 1:
            return jar_results[0]

        # Use the first result as base and merge others
        merged = jar_results[0]

        # Merge class files
        all_class_files = []
        for result in jar_results:
            all_class_files.extend(result.class_files)
        merged.class_files = all_class_files

        # Merge resources
        all_resources = []
        for result in jar_results:
            all_resources.extend(result.resources)
        merged.resources = all_resources

        # Merge native libraries
        all_native_libraries = []
        for result in jar_results:
            all_native_libraries.extend(result.native_libraries)
        merged.native_libraries = all_native_libraries

        # Merge config files
        all_config_files = []
        for result in jar_results:
            all_config_files.extend(result.config_files)
        merged.config_files = all_config_files

        # Merge dependencies
        all_dependencies = []
        for result in jar_results:
            all_dependencies.extend(result.dependencies)
        merged.dependencies = all_dependencies

        # Merge warnings and errors
        all_warnings = []
        all_errors = []
        for result in jar_results:
            all_warnings.extend(result.warnings)
            all_errors.extend(result.errors)
        merged.warnings = all_warnings
        merged.errors = all_errors

        return merged

    def _extract_all_dependencies(self, jar_results: List[JarAnalysisResult]) -> List[Dependency]:
        """Extract all dependencies from JAR analysis results"""
        all_deps = []

        for result in jar_results:
            all_deps.extend(result.dependencies)

        # Also check for embedded JARs
        for result in jar_results:
            for resource in result.resources:
                if resource.path.endswith('.jar'):
                    # Create dependency for embedded JAR
                    jar_name = Path(resource.path).stem
                    dep = Dependency(
                        group_id="embedded",
                        artifact_id=jar_name,
                        scope=DependencyScope.RUNTIME,
                        dependency_type=DependencyType.JAR,
                        file_path=resource.path,
                        metadata={'source': 'embedded_jar', 'size': resource.size}
                    )
                    all_deps.append(dep)

        return all_deps

    def _build_comprehensive_graph(self, dependencies: List[Dependency]) -> DependencyGraph:
        """Build comprehensive dependency graph"""
        graph = DependencyGraph()

        # Add all dependencies
        for dep in dependencies:
            graph.add_dependency(dep)

        # Try to resolve transitive dependencies
        if self.config.resolve_transitive:
            for dep in dependencies:
                self._resolve_transitive_dependencies(dep, graph)

        # Detect conflicts and cycles
        conflicts = graph.find_conflicts()
        cycles = graph.detect_cycles()

        if conflicts:
            logger.warning(f"Found {len(conflicts)} dependency conflicts")

        if cycles:
            logger.warning(f"Found {len(cycles)} circular dependencies")

        return graph

    def _resolve_transitive_dependencies(self, dependency: Dependency, graph: DependencyGraph) -> None:
        """Resolve transitive dependencies for a dependency"""
        # Use the dependency resolver's transitive resolution
        transitive_deps = self.dependency_resolver._find_transitive_dependencies(dependency)
        for trans_dep in transitive_deps:
            graph.add_dependency(trans_dep, parent=dependency.maven_coordinates)

    def _create_resolution_context(self) -> ResolutionContext:
        """Create resolution context from configuration"""
        exclude_scopes = set()
        include_scopes = {DependencyScope.COMPILE, DependencyScope.RUNTIME}

        if self.config.exclude_test_deps:
            exclude_scopes.add(DependencyScope.TEST)

        if self.config.exclude_provided_deps:
            exclude_scopes.add(DependencyScope.PROVIDED)

        return ResolutionContext(
            target_platform=self.config.target_platform,
            java_version=self.config.java_version,
            bundle_native_libraries=self.config.bundle_native_libraries,
            bundle_optional_deps=self.config.bundle_optional_deps,
            max_dependency_depth=self.config.max_dependency_depth,
            conflict_resolution_strategy=self.config.conflict_resolution_strategy,
            exclude_scopes=exclude_scopes,
            include_scopes=include_scopes
        )

    def _generate_bundling_strategy(self, resolution_result: ResolutionResult,
                                  jar_analysis: JarAnalysisResult) -> Dict[str, Any]:
        """Generate bundling strategy based on resolution and analysis"""
        bundle_list: list[Dict[str, Any]] = []
        external_list: list[Dict[str, Any]] = []
        optimization_suggestions: list[str] = []

        # Categorize dependencies for bundling
        for dep in resolution_result.resolved_dependencies:
            if dep.dependency_type == DependencyType.NATIVE:
                bundle_list.append({
                    'dependency': dep,
                    'reason': 'Native library required for platform compatibility',
                    'priority': 'high'
                })
            elif dep.scope == DependencyScope.COMPILE:
                bundle_list.append({
                    'dependency': dep,
                    'reason': 'Compile-time dependency',
                    'priority': 'high'
                })
            elif dep.scope == DependencyScope.RUNTIME:
                if dep.is_optional and not self.config.bundle_optional_deps:
                    external_list.append({
                        'dependency': dep,
                        'reason': 'Optional dependency (external loading recommended)',
                        'priority': 'low'
                    })
                else:
                    bundle_list.append({
                        'dependency': dep,
                        'reason': 'Runtime dependency',
                        'priority': 'medium'
                    })

        # Add optimization suggestions
        if len(bundle_list) > 50:
            optimization_suggestions.append(
                "Large number of dependencies detected - consider using fat JAR or modular approach"
            )

        native_lib_count = len([d for d in bundle_list if d['dependency'].dependency_type == DependencyType.NATIVE])
        if native_lib_count > 5:
            optimization_suggestions.append(
                f"Many native libraries ({native_lib_count}) detected - ensure platform compatibility"
            )

        strategy: Dict[str, Any] = {
            'total_dependencies': len(resolution_result.resolved_dependencies),
            'bundle_list': bundle_list,
            'external_list': external_list,
            'classpath_entries': resolution_result.resolved_dependencies,
            'native_libraries': jar_analysis.native_libraries,
            'config_files': jar_analysis.config_files,
            'estimated_total_size': 0,
            'optimization_suggestions': optimization_suggestions,
        }

        return strategy

    def _generate_reports(self, result: ComprehensiveAnalysisResult) -> Dict[str, str]:
        """Generate various reports"""
        reports: Dict[str, str] = {}

        if not self.config.generate_reports:
            return reports

        # Text report
        reports['text'] = self._generate_text_report(result)

        # JSON report
        if self.config.output_format == 'json':
            reports['json'] = self._generate_json_report(result)

        return reports

    def _generate_text_report(self, result: ComprehensiveAnalysisResult) -> str:  # noqa: C901
        """Generate detailed text report"""
        lines = []
        lines.append("🔍 COMPREHENSIVE DEPENDENCY ANALYSIS REPORT")
        lines.append("=" * 50)
        lines.append("")

        # JAR Analysis Summary
        if result.jar_analysis:
            lines.append("📦 JAR ANALYSIS SUMMARY:")
            lines.append("  • JAR Files: 1")
            lines.append(f"  • Total Size: {result.jar_analysis.jar_size:,} bytes")
            lines.append(f"  • Class Files: {len(result.jar_analysis.class_files)}")
            lines.append(f"  • Resources: {len(result.jar_analysis.resources)}")
            lines.append(f"  • Native Libraries: {len(result.jar_analysis.native_libraries)}")
            lines.append(f"  • Config Files: {len(result.jar_analysis.config_files)}")
            lines.append("")

        # Dependency Analysis
        lines.append("🔗 DEPENDENCY ANALYSIS:")
        if result.dependency_graph:
            lines.append(f"  • Total Dependencies: {len(result.dependency_graph.nodes)}")
        if result.resolution_result:
            lines.append(f"  • Resolved Dependencies: {len(result.resolution_result.resolved_dependencies)}")
            lines.append(f"  • Excluded Dependencies: {len(result.resolution_result.excluded_dependencies)}")
            lines.append(f"  • Conflicts Found: {len(result.resolution_result.conflicts)}")
        if result.dependency_graph:
            lines.append(f"  • Circular Dependencies: {len(result.dependency_graph.cycles)}")
        lines.append("")

        # Bundling Strategy
        if result.bundling_decisions:
            bundle_count = len([item for item in result.bundling_decisions.get('bundle_list', [])])
            external_count = len([item for item in result.bundling_decisions.get('external_list', [])])
            lines.append("📦 BUNDLING STRATEGY:")
            lines.append(f"  • Dependencies to Bundle: {bundle_count}")
            lines.append(f"  • Dependencies for External Loading: {external_count}")
            lines.append(f"  • Classpath Entries: {len(result.classpath)}")
            lines.append("")

        # Recommendations
        if result.recommendations:
            lines.append("💡 RECOMMENDATIONS:")
            for i, rec in enumerate(result.recommendations, 1):
                lines.append(f"  {i}. {rec}")
            lines.append("")

        # Warnings
        if result.warnings:
            lines.append("⚠️  WARNINGS:")
            for warning in result.warnings:
                lines.append(f"  • {warning}")
            lines.append("")

        # Errors
        if result.errors:
            lines.append("❌ ERRORS:")
            for error in result.errors:
                lines.append(f"  • {error}")
            lines.append("")

        return "\n".join(lines)

    def _generate_json_report(self, result: ComprehensiveAnalysisResult) -> str:
        """Generate JSON report"""
        report_data = {
            'jar_analysis': {
                'jar_path': str(result.jar_analysis.jar_path) if result.jar_analysis else None,
                'jar_size': result.jar_analysis.jar_size if result.jar_analysis else 0,
                'class_files_count': len(result.jar_analysis.class_files) if result.jar_analysis else 0,
                'resources_count': len(result.jar_analysis.resources) if result.jar_analysis else 0,
                'native_libraries': result.jar_analysis.native_libraries if result.jar_analysis else [],
                'config_files': result.jar_analysis.config_files if result.jar_analysis else [],
            },
            'dependency_analysis': {
                'total_dependencies': len(result.dependency_graph.nodes) if result.dependency_graph else 0,
                'resolved_dependencies': len(result.resolution_result.resolved_dependencies) if result.resolution_result else 0,
                'excluded_dependencies': len(result.resolution_result.excluded_dependencies) if result.resolution_result else 0,
                'conflicts': len(result.resolution_result.conflicts) if result.resolution_result else 0,
                'cycles': len(result.dependency_graph.cycles) if result.dependency_graph else 0,
            },
            'bundling_strategy': result.bundling_decisions,
            'classpath': result.classpath,
            'recommendations': result.recommendations,
            'warnings': result.warnings,
            'errors': result.errors,
            'metadata': result.analysis_metadata
        }

        return json.dumps(report_data, indent=2)

    def _generate_recommendations(self, result: ComprehensiveAnalysisResult) -> List[str]:
        """Generate analysis recommendations"""
        recommendations = []

        # Size recommendations
        if result.jar_analysis and result.jar_analysis.jar_size > 50 * 1024 * 1024:  # 50MB
            recommendations.append(
                f"Large JAR detected ({result.jar_analysis.jar_size / (1024*1024):.1f}MB) - consider dependency optimization"
            )

        # Dependency count recommendations
        total_deps = len(result.dependency_graph.nodes) if result.dependency_graph else 0
        if total_deps > 100:
            recommendations.append(
                f"High dependency count ({total_deps}) - consider using a more modular approach"
            )

        # Conflict recommendations
        if result.resolution_result and result.resolution_result.conflicts:
            recommendations.append(
                f"Dependency conflicts detected ({len(result.resolution_result.conflicts)}) - review resolution strategy"
            )

        # Native library recommendations
        if result.jar_analysis and len(result.jar_analysis.native_libraries) > 0:
            recommendations.append(
                f"Native libraries detected ({len(result.jar_analysis.native_libraries)}) - ensure cross-platform compatibility"
            )

        # Java version recommendations
        if result.jar_analysis and result.jar_analysis.estimated_java_version.value != "unknown":
            recommendations.append(
                f"Target Java version: {result.jar_analysis.estimated_java_version.value}"
            )

        return recommendations

    def _generate_metadata(self, result: ComprehensiveAnalysisResult) -> Dict[str, Any]:
        """Generate analysis metadata"""
        return {
            'analysis_timestamp': str(Path().cwd()),  # Could use actual timestamp
            'analyzer_version': '1.0.0',
            'configuration': {
                'analyze_bytecode': self.config.analyze_bytecode,
                'analyze_manifest': self.config.analyze_manifest,
                'resolve_transitive': self.config.resolve_transitive,
                'conflict_resolution_strategy': self.config.conflict_resolution_strategy.value,
                'target_platform': self.config.target_platform.value,
            },
            'statistics': {
                'total_jar_files_analyzed': 1,  # Would be actual count
                'total_classes_analyzed': len(result.jar_analysis.class_files) if result.jar_analysis else 0,
                'total_resources_analyzed': len(result.jar_analysis.resources) if result.jar_analysis else 0,
                'total_dependencies_resolved': len(result.resolution_result.resolved_dependencies) if result.resolution_result else 0,
                'total_conflicts_resolved': len(result.resolution_result.conflicts) if result.resolution_result else 0,
            }
        }


def analyze_application_dependencies(jar_paths: List[str],
                                   config: Optional[AnalysisConfiguration] = None) -> ComprehensiveAnalysisResult:
    """Convenience function for application dependency analysis"""
    analyzer = ComprehensiveDependencyAnalyzer(config)
    return analyzer.analyze_application(jar_paths)


def quick_dependency_check(jar_path: str) -> Dict[str, Any]:
    """Quick dependency check for a single JAR file"""
    config = AnalysisConfiguration(
        analyze_bytecode=True,
        resolve_transitive=False,
        generate_reports=False,
        verbose=False
    )

    result = analyze_application_dependencies([jar_path], config)

    return {
        'jar_path': jar_path,
        'is_valid': result.jar_analysis.is_valid_jar if result.jar_analysis else False,
        'main_class': result.jar_analysis.manifest.main_class if result.jar_analysis and result.jar_analysis.manifest else None,
        'dependency_count': len(result.dependency_graph.nodes) if result.dependency_graph else 0,
        'has_conflicts': len(result.resolution_result.conflicts) > 0 if result.resolution_result else False,
        'estimated_size_mb': (result.jar_analysis.jar_size / (1024 * 1024)) if result.jar_analysis else 0,
        'java_version': result.jar_analysis.estimated_java_version.value if result.jar_analysis else 'unknown',
        'warnings': result.warnings,
        'errors': result.errors
    }

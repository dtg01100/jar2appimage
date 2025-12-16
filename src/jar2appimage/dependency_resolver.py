#!/usr/bin/env python3
"""
Dependency Resolution Engine for JAR2AppImage

This module provides comprehensive dependency resolution including:
- Transitive dependency resolution
- Conflict resolution with multiple strategies
- Circular dependency detection and handling
- Optional dependency management
- Platform-specific dependency handling
- Bundling decision engine

Key Features:
- Intelligent dependency resolution strategies
- Conflict resolution with version management
- Platform-specific dependency filtering
- Bundling optimization recommendations
- Dependency caching and performance optimization
"""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from .dependency_graph import (
    Dependency,
    DependencyGraph,
    DependencyNode,
    DependencyScope,
    DependencyType,
)

logger = logging.getLogger(__name__)


class ConflictResolutionStrategy(Enum):
    """Strategies for resolving dependency conflicts"""
    PREFER_LATEST = "prefer_latest"
    PREFER_COMPILE_SCOPE = "prefer_compile_scope"
    PREFER_NON_OPTIONAL = "prefer_non_optional"
    PREFER_DIRECT = "prefer_direct"
    PREFER_SHORTEST_PATH = "prefer_shortest_path"
    MANUAL = "manual"


class Platform(Enum):
    """Supported platforms"""
    LINUX = "linux"
    WINDOWS = "windows"
    MACOS = "macos"
    ANY = "any"


@dataclass
class ResolutionContext:
    """Context for dependency resolution"""
    target_platform: Platform = Platform.ANY
    java_version: Optional[str] = None
    bundle_native_libraries: bool = True
    bundle_optional_deps: bool = False
    max_dependency_depth: int = 10
    conflict_resolution_strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.PREFER_LATEST
    exclude_scopes: Set[DependencyScope] = field(default_factory=lambda: {DependencyScope.TEST})
    include_scopes: Set[DependencyScope] = field(default_factory=lambda: {DependencyScope.COMPILE, DependencyScope.RUNTIME})
    excluded_dependencies: Set[str] = field(default_factory=set)
    included_dependencies: Set[str] = field(default_factory=set)


@dataclass
class ResolutionResult:
    """Result of dependency resolution"""
    resolved_dependencies: List[Dependency]
    excluded_dependencies: List[Dependency]
    conflicts: List[Tuple[Dependency, Dependency]]
    unresolved_dependencies: List[Dependency]
    bundling_recommendations: List[str]
    warnings: List[str]
    errors: List[str]
    resolution_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BundlingDecision:
    """Decision about dependency bundling"""
    dependency: Dependency
    should_bundle: bool
    reason: str
    priority: int
    estimated_size: Optional[int] = None
    alternatives: List[Dependency] = field(default_factory=list)


class DependencyResolver:
    """Comprehensive dependency resolution engine"""

    def __init__(self) -> None:
        self.known_patterns = self._initialize_known_patterns()
        self.platform_specific_deps = self._initialize_platform_specific_deps()
        self.conflict_history: Dict[str, Any] = {}
        self.resolution_cache: Dict[str, Any] = {}

    def resolve_dependencies(self,
                           dependencies: List[Dependency],
                           context: ResolutionContext) -> ResolutionResult:
        """Resolve dependencies with the given context"""
        logger.info(f"Resolving {len(dependencies)} dependencies with strategy: {context.conflict_resolution_strategy.value}")

        result = ResolutionResult(
            resolved_dependencies=[],
            excluded_dependencies=[],
            conflicts=[],
            unresolved_dependencies=[],
            bundling_recommendations=[],
            warnings=[],
            errors=[]
        )

        try:
            # Create dependency graph
            graph = self._build_dependency_graph(dependencies)

            # Apply filters based on context
            filtered_deps = self._apply_context_filters(graph, context)

            # Resolve conflicts
            conflicts = graph.find_conflicts()
            if conflicts:
                result.conflicts = self._resolve_conflicts(graph, conflicts, context)

            # Detect cycles
            cycles = graph.detect_cycles()
            if cycles:
                result.warnings.extend([f"Circular dependency detected: {[str(node.dependency) for node in cycle]}" for cycle in cycles])

            # Generate bundling decisions
            bundling_decisions = self._generate_bundling_decisions(filtered_deps, context)

            # Compile final result
            result.resolved_dependencies = [dep for dep, decision in bundling_decisions.items() if decision.should_bundle]
            result.excluded_dependencies = [dep for dep, decision in bundling_decisions.items() if not decision.should_bundle]
            result.bundling_recommendations = self._generate_bundling_recommendations(bundling_decisions)

            # Add metadata
            result.resolution_metadata = {
                'total_dependencies': len(dependencies),
                'resolved_count': len(result.resolved_dependencies),
                'excluded_count': len(result.excluded_dependencies),
                'conflict_count': len(result.conflicts),
                'resolution_strategy': context.conflict_resolution_strategy.value,
                'target_platform': context.target_platform.value,
            }

        except Exception as e:
            result.errors.append(f"Error during dependency resolution: {e}")
            logger.error(f"Dependency resolution failed: {e}")

        logger.info(f"Resolution complete: {len(result.resolved_dependencies)} resolved, {len(result.excluded_dependencies)} excluded")
        return result

    def _build_dependency_graph(self, dependencies: List[Dependency]) -> DependencyGraph:
        """Build dependency graph from dependency list"""
        graph = DependencyGraph()

        # Add all dependencies to graph
        for dep in dependencies:
            graph.add_dependency(dep)

        # Try to resolve transitive dependencies
        for dep in dependencies:
            self._resolve_transitive_dependencies(dep, graph)

        return graph

    def _resolve_transitive_dependencies(self, dependency: Dependency, graph: DependencyGraph) -> None:
        """Attempt to resolve transitive dependencies for a given dependency"""
        # This would typically involve:
        # 1. Looking up the dependency in Maven Central or other repositories
        # 2. Downloading and analyzing its POM file
        # 3. Adding its dependencies to the graph

        # For now, we'll use pattern-based resolution
        transitive_deps = self._find_transitive_dependencies(dependency)
        for trans_dep in transitive_deps:
            graph.add_dependency(trans_dep, parent=dependency.maven_coordinates)

    def _find_transitive_dependencies(self, dependency: Dependency) -> List[Dependency]:
        """Find transitive dependencies using known patterns and metadata"""
        transitive_deps = []

        # Check known dependency patterns
        for pattern, deps in self.known_patterns.items():
            if re.search(pattern, dependency.artifact_id, re.IGNORECASE):
                transitive_deps.extend(deps)

        # Add common transitive dependencies
        if dependency.artifact_id.lower() in ['spring-boot-starter', 'spring-boot-starter-web']:
            transitive_deps.extend([
                Dependency('org.springframework.boot', 'spring-boot'),
                Dependency('org.springframework', 'spring-web'),
                Dependency('org.springframework', 'spring-webmvc'),
                Dependency('com.fasterxml.jackson.core', 'jackson-databind'),
            ])

        return transitive_deps

    def _apply_context_filters(self, graph: DependencyGraph, context: ResolutionContext) -> List[Dependency]:
        """Apply context-based filters to dependencies"""
        filtered_deps = []

        for node in graph.nodes.values():
            dep = node.dependency

            # Skip excluded dependencies
            if dep.maven_coordinates in context.excluded_dependencies:
                continue

            # Include only explicitly included dependencies if list is not empty
            if context.included_dependencies and dep.maven_coordinates not in context.included_dependencies:
                continue

            # Filter by scope
            if dep.scope not in context.include_scopes or dep.scope in context.exclude_scopes:
                continue

            # Filter by platform
            if not self._is_platform_compatible(dep, context.target_platform):
                continue

            # Filter by Java version
            if context.java_version and not self._is_java_version_compatible(dep, context.java_version):
                continue

            filtered_deps.append(dep)

        return filtered_deps

    def _is_platform_compatible(self, dependency: Dependency, target_platform: Platform) -> bool:
        """Check if dependency is compatible with target platform"""
        if target_platform == Platform.ANY:
            return True

        platform_metadata = dependency.metadata.get('platform', {})
        supported_platforms = platform_metadata.get('supported', ['any'])

        return target_platform.value in supported_platforms or 'any' in supported_platforms

    def _is_java_version_compatible(self, dependency: Dependency, java_version: str) -> bool:
        """Check if dependency is compatible with Java version"""
        java_requirement = dependency.metadata.get('java_version')
        if not java_requirement:
            return True

        # Simple version comparison (could be more sophisticated)
        try:
            req_major = int(java_requirement.split('.')[0])
            target_major = int(java_version.split('.')[0])
            return target_major >= req_major
        except (ValueError, IndexError):
            return True

    def _resolve_conflicts(self,
                          graph: DependencyGraph,
                          conflicts: List[Tuple[DependencyNode, DependencyNode]],
                          context: ResolutionContext) -> List[Tuple[Dependency, Dependency]]:
        """Resolve dependency conflicts using the specified strategy"""
        resolved_conflicts = []

        for node1, node2 in conflicts:
            dep1, dep2 = node1.dependency, node2.dependency

            try:
                resolved_dep = self._resolve_conflict_pair(dep1, dep2, context)
                if resolved_dep:
                    # Update the dependency information
                    if resolved_dep != dep1:
                        dep1.conflict_resolution = resolved_dep.version
                        dep1.is_conflict = True
                    if resolved_dep != dep2:
                        dep2.conflict_resolution = resolved_dep.version
                        dep2.is_conflict = True

                    resolved_conflicts.append((dep1, dep2))

            except Exception as e:
                logger.error(f"Error resolving conflict between {dep1} and {dep2}: {e}")

        return resolved_conflicts

    def _resolve_conflict_pair(self, dep1: Dependency, dep2: Dependency, context: ResolutionContext) -> Optional[Dependency]:
        """Resolve a specific conflict pair"""
        strategy = context.conflict_resolution_strategy

        if strategy == ConflictResolutionStrategy.PREFER_LATEST:
            return self._prefer_latest(dep1, dep2)
        elif strategy == ConflictResolutionStrategy.PREFER_COMPILE_SCOPE:
            return self._prefer_compile_scope(dep1, dep2)
        elif strategy == ConflictResolutionStrategy.PREFER_NON_OPTIONAL:
            return self._prefer_non_optional(dep1, dep2)
        elif strategy == ConflictResolutionStrategy.PREFER_DIRECT:
            return self._prefer_direct(dep1, dep2)
        elif strategy == ConflictResolutionStrategy.PREFER_SHORTEST_PATH:
            return self._prefer_shortest_path(dep1, dep2)
        else:
            logger.warning(f"Unknown conflict resolution strategy: {strategy}")
            return dep1

    def _prefer_latest(self, dep1: Dependency, dep2: Dependency) -> Dependency:
        """Prefer the version that comes later alphabetically"""
        if dep1.version and dep2.version:
            return dep1 if dep1.version > dep2.version else dep2
        elif dep1.version:
            return dep1
        elif dep2.version:
            return dep2
        else:
            return dep1

    def _prefer_compile_scope(self, dep1: Dependency, dep2: Dependency) -> Dependency:
        """Prefer compile scope over other scopes"""
        if dep1.scope == DependencyScope.COMPILE and dep2.scope != DependencyScope.COMPILE:
            return dep1
        elif dep2.scope == DependencyScope.COMPILE and dep1.scope != DependencyScope.COMPILE:
            return dep2
        else:
            return dep1

    def _prefer_non_optional(self, dep1: Dependency, dep2: Dependency) -> Dependency:
        """Prefer non-optional over optional dependencies"""
        if not dep1.is_optional and dep2.is_optional:
            return dep1
        elif not dep2.is_optional and dep1.is_optional:
            return dep2
        else:
            return dep1

    def _prefer_direct(self, dep1: Dependency, dep2: Dependency) -> Dependency:
        """Prefer direct dependencies over transitive ones"""
        if not dep1.is_transitive and dep2.is_transitive:
            return dep1
        elif not dep2.is_transitive and dep1.is_transitive:
            return dep2
        else:
            return dep1

    def _prefer_shortest_path(self, dep1: Dependency, dep2: Dependency) -> Dependency:
        """Prefer dependencies with shorter dependency paths"""
        # This would require path length information in the dependency graph
        # For now, default to dep1
        return dep1

    def _generate_bundling_decisions(self, dependencies: List[Dependency], context: ResolutionContext) -> Dict[Dependency, BundlingDecision]:
        """Generate bundling decisions for dependencies"""
        decisions = {}

        for dep in dependencies:
            decision = self._make_bundling_decision(dep, context)
            decisions[dep] = decision

        return decisions

    def _make_bundling_decision(self, dependency: Dependency, context: ResolutionContext) -> BundlingDecision:
        """Make a bundling decision for a single dependency"""

        # Determine if dependency should be bundled
        should_bundle = True
        reason = ""
        priority = 0

        # Check if it's a platform-specific dependency
        if dependency.dependency_type == DependencyType.NATIVE:
            if context.bundle_native_libraries:
                should_bundle = True
                reason = "Native library required for platform compatibility"
                priority = 10
            else:
                should_bundle = False
                reason = "Native library bundling disabled"
                priority = 5

        # Check if it's optional
        elif dependency.is_optional:
            if context.bundle_optional_deps:
                should_bundle = True
                reason = "Optional dependency (included per configuration)"
                priority = 3
            else:
                should_bundle = False
                reason = "Optional dependency excluded"
                priority = 1

        # Check scope
        elif dependency.scope == DependencyScope.PROVIDED:
            should_bundle = False
            reason = "Provided scope - expected to be available at runtime"
            priority = 0

        elif dependency.scope == DependencyScope.TEST:
            should_bundle = False
            reason = "Test scope - not needed for runtime"
            priority = 0

        # Default decision
        else:
            should_bundle = True
            reason = "Required runtime dependency"
            priority = 8

        # Check for alternatives
        alternatives = self._find_alternatives(dependency)

        return BundlingDecision(
            dependency=dependency,
            should_bundle=should_bundle,
            reason=reason,
            priority=priority,
            alternatives=alternatives
        )

    def _find_alternatives(self, dependency: Dependency) -> List[Dependency]:
        """Find alternative dependencies that could replace this one"""
        alternatives = []

        # Look for platform-specific alternatives
        if dependency.dependency_type == DependencyType.NATIVE:
            # Could suggest platform-specific versions
            pass

        # Look for version alternatives
        if dependency.version:
            # Could suggest other versions of the same dependency
            alternatives.extend([
                Dependency(dependency.group_id, dependency.artifact_id, "latest"),
                Dependency(dependency.group_id, dependency.artifact_id, "latest.release"),
            ])

        return alternatives

    def _generate_bundling_recommendations(self, decisions: Dict[Dependency, BundlingDecision]) -> List[str]:
        """Generate bundling recommendations based on decisions"""
        recommendations = []

        # Group decisions by priority
        high_priority = [dep for dep, decision in decisions.items() if decision.priority >= 8 and decision.should_bundle]
        medium_priority = [dep for dep, decision in decisions.items() if 5 <= decision.priority < 8 and decision.should_bundle]
        low_priority = [dep for dep, decision in decisions.items() if 2 <= decision.priority < 5 and decision.should_bundle]

        if high_priority:
            recommendations.append(f"Bundle {len(high_priority)} high-priority dependencies (required for core functionality)")

        if medium_priority:
            recommendations.append(f"Bundle {len(medium_priority)} medium-priority dependencies (enhanced features)")

        if low_priority:
            recommendations.append(f"Consider bundling {len(low_priority)} low-priority dependencies (optional features)")

        # Platform-specific recommendations
        native_deps = [dep for dep, decision in decisions.items()
                      if dep.dependency_type == DependencyType.NATIVE and decision.should_bundle]
        if native_deps:
            recommendations.append(f"Include {len(native_deps)} native libraries for platform compatibility")

        # Size recommendations
        large_deps = [dep for dep, decision in decisions.items()
                     if decision.estimated_size and decision.estimated_size > 10 * 1024 * 1024]  # 10MB
        if large_deps:
            recommendations.append(f"Large dependencies detected: {len(large_deps)} > 10MB (consider external loading)")

        return recommendations

    def _initialize_known_patterns(self) -> Dict[str, List[Dependency]]:
        """Initialize known dependency patterns"""
        patterns = {
            r'spring-boot-starter.*': [
                Dependency('org.springframework.boot', 'spring-boot'),
                Dependency('org.springframework', 'spring-core'),
                Dependency('org.springframework', 'spring-context'),
            ],
            r'spring-web.*': [
                Dependency('org.springframework', 'spring-web'),
                Dependency('org.springframework', 'spring-webmvc'),
                Dependency('jakarta.servlet', 'jakarta.servlet-api'),
            ],
            r'spring-data.*': [
                Dependency('org.springframework.data', 'spring-data-commons'),
            ],
            r'hibernate.*': [
                Dependency('org.hibernate', 'hibernate-core'),
                Dependency('javax.persistence', 'javax.persistence-api'),
            ],
        }
        return patterns

    def _initialize_platform_specific_deps(self) -> Dict[str, List[str]]:
        """Initialize platform-specific dependencies"""
        return {
            'windows': ['.dll', '.exe'],
            'linux': ['.so'],
            'macos': ['.dylib', '.jnilib'],
        }

    def optimize_for_size(self, decisions: Dict[Dependency, BundlingDecision],
                         max_size_mb: int = 100) -> Dict[str, Any]:
        """Optimize bundling decisions for size constraints"""
        optimization_result: Dict[str, Any] = {
            'original_count': len(decisions),
            'optimized_count': 0,
            'estimated_size_mb': 0.0,
            'recommendations': [],
            'excluded_dependencies': [],
            'size_savings_mb': 0.0
        }

        # Calculate current estimated size
        current_size = float(sum(decision.estimated_size or 0 for decision in decisions.values()))
        current_size_mb = current_size / (1024 * 1024)
        optimization_result['estimated_size_mb'] = current_size_mb

        if current_size_mb <= max_size_mb:
            optimization_result['optimized_count'] = len(decisions)
            optimization_result['recommendations'].append(f"Size within limit ({current_size_mb:.1f}MB <= {max_size_mb}MB)")
            return optimization_result

        # Need optimization
        size_to_reduce_mb = current_size_mb - max_size_mb

        # Sort dependencies by priority (ascending) for potential exclusion
        sorted_deps = sorted(decisions.items(), key=lambda x: x[1].priority)

        excluded_count = 0
        excluded_size_mb = 0.0

        for _dep, decision in sorted_deps:
            if decision.priority <= 3 and decision.dependency.is_optional:  # Low priority optional deps
                decision.should_bundle = False
                excluded_count += 1
                if decision.estimated_size:
                    excluded_size_mb += float(decision.estimated_size) / (1024 * 1024)

                if excluded_size_mb >= size_to_reduce_mb:
                    break

        optimization_result['optimized_count'] = len([d for d in decisions.values() if d.should_bundle])
        optimization_result['excluded_dependencies'] = [dep.maven_coordinates for dep, decision in decisions.items() if not decision.should_bundle]
        optimization_result['size_savings_mb'] = excluded_size_mb
        optimization_result['estimated_size_mb'] = current_size_mb - excluded_size_mb
        optimization_result['recommendations'].append(f"Excluded {excluded_count} low-priority dependencies to meet size constraint")

        return optimization_result

    def generate_classpath(self, resolved_dependencies: List[Dependency]) -> List[str]:
        """Generate classpath entries for resolved dependencies"""
        classpath: List[str] = []

        for dep in resolved_dependencies:
            if dep.file_path:
                classpath.append(dep.file_path)
            else:
                # Generate expected JAR path
                jar_name = dep.jar_filename
                classpath.append(jar_name)

        return classpath


def resolve_dependencies(dependencies: List[Dependency],
                        context: Optional[ResolutionContext] = None) -> ResolutionResult:
    """Convenience function for dependency resolution"""
    if context is None:
        context = ResolutionContext()

    resolver = DependencyResolver()
    return resolver.resolve_dependencies(dependencies, context)

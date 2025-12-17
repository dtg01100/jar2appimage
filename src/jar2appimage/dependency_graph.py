#!/usr/bin/env python3
"""
Dependency Graph Management for JAR2AppImage

This module provides comprehensive dependency relationship modeling,
conflict detection, and dependency graph analysis for Java applications.

Key Features:
- Robust dependency relationship modeling
- Circular dependency detection
- Version conflict identification
- Dependency scope analysis
- Graph traversal and analysis utilities
"""

import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class DependencyScope(Enum):
    """Dependency scope classification"""
    COMPILE = "compile"
    RUNTIME = "runtime"
    TEST = "test"
    PROVIDED = "provided"
    OPTIONAL = "optional"
    SYSTEM = "system"


class DependencyType(Enum):
    """Type of dependency"""
    MAVEN = "maven"
    JAR = "jar"
    NATIVE = "native"
    RESOURCE = "resource"
    PLATFORM = "platform"
    MODULE = "module"


@dataclass
class Dependency:
    """Represents a dependency relationship"""
    group_id: str
    artifact_id: str
    version: Optional[str] = None
    scope: DependencyScope = DependencyScope.COMPILE
    dependency_type: DependencyType = DependencyType.MAVEN
    file_path: Optional[str] = None
    is_optional: bool = False
    is_transitive: bool = False
    is_conflict: bool = False
    conflict_resolution: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def maven_coordinates(self) -> str:
        """Get Maven coordinates string"""
        version_part = f":{self.version}" if self.version else ""
        return f"{self.group_id}:{self.artifact_id}{version_part}"

    @property
    def jar_filename(self) -> str:
        """Generate expected JAR filename"""
        version_part = f"-{self.version}" if self.version else ""
        return f"{self.artifact_id}{version_part}.jar"

    def matches_coordinates(self, coordinates: str) -> bool:
        """Check if this dependency matches given Maven coordinates"""
        try:
            parts = coordinates.split(":")
            if len(parts) >= 2:
                group_part = ":".join(parts[:-1])
                artifact_part = parts[-1]
                return self.group_id == group_part and self.artifact_id == artifact_part
            return False
        except Exception:
            return False

    def __hash__(self) -> int:
        """Make Dependency hashable for use in sets"""
        return hash((self.group_id, self.artifact_id, self.version))

    def __eq__(self, other: object) -> bool:
        """Equality comparison for Dependency"""
        if not isinstance(other, Dependency):
            return False
        return (self.group_id == other.group_id and
                self.artifact_id == other.artifact_id and
                self.version == other.version)


@dataclass
class DependencyNode:
    """Node in the dependency graph"""
    dependency: Dependency
    dependencies: Set['DependencyNode'] = field(default_factory=set)
    dependents: Set['DependencyNode'] = field(default_factory=set)
    level: int = 0  # Distance from root
    is_root: bool = False
    is_leaf: bool = False
    analysis_metadata: Dict[str, Any] = field(default_factory=dict)

    def add_dependency(self, node: 'DependencyNode') -> None:
        """Add a dependency relationship"""
        self.dependencies.add(node)
        node.dependents.add(self)

    def remove_dependency(self, node: 'DependencyNode') -> None:
        """Remove a dependency relationship"""
        self.dependencies.discard(node)
        node.dependents.discard(self)

    def get_all_dependents(self) -> Set['DependencyNode']:
        """Get all transitive dependents (reverse dependency tree)"""
        visited = set()
        queue = deque([self])

        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            for dependent in current.dependents:
                if dependent not in visited:
                    queue.append(dependent)

        return visited - {self}

    def get_all_dependencies(self) -> Set['DependencyNode']:
        """Get all transitive dependencies"""
        visited = set()
        queue = deque([self])

        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            for dep in current.dependencies:
                if dep not in visited:
                    queue.append(dep)

        return visited - {self}

    def find_conflicts(self) -> List[Tuple['DependencyNode', 'DependencyNode']]:
        """Find version conflicts in dependency tree"""
        conflicts: List[Tuple[DependencyNode, DependencyNode]] = []
        coord_map: Dict[str, DependencyNode] = {}

        def check_conflicts(
            node: 'DependencyNode', visited: Set['DependencyNode']
        ) -> None:
            if node in visited:
                return
            visited.add(node)

            coord = node.dependency.maven_coordinates
            if coord in coord_map:
                existing = coord_map[coord]
                if existing.dependency.version != node.dependency.version:
                    conflicts.append((existing, node))
            else:
                coord_map[coord] = node

            for dep in node.dependencies:
                check_conflicts(dep, visited)

        check_conflicts(self, set())
        return conflicts

    def __repr__(self) -> str:
        return f"DependencyNode({self.dependency.maven_coordinates})"

    def __eq__(self, other):
        if not isinstance(other, DependencyNode):
            return NotImplemented
        return self.dependency == other.dependency

    def __hash__(self):
        return hash(self.dependency)



class DependencyGraph:
    """Comprehensive dependency graph management"""

    def __init__(self) -> None:
        self.nodes: Dict[str, DependencyNode] = {}
        self.root_dependencies: Set[DependencyNode] = set()
        self.conflicts: List[Tuple[DependencyNode, DependencyNode]] = []
        self.cycles: List[List[DependencyNode]] = []
        self.metadata: Dict[str, Any] = {}

    def add_dependency(self, dependency: Dependency, parent: Optional[str] = None) -> DependencyNode:
        """Add a dependency to the graph"""
        node_key = dependency.maven_coordinates

        if node_key in self.nodes:
            # Update existing node with new information
            existing_node = self.nodes[node_key]
            self._merge_dependency_info(existing_node.dependency, dependency)
            return existing_node
        else:
            # Create new node
            node = DependencyNode(dependency)
            self.nodes[node_key] = node

            if parent:
                parent_node = self.nodes.get(parent)
                if parent_node:
                    parent_node.add_dependency(node)
            else:
                self.root_dependencies.add(node)
                node.is_root = True

            return node

    def _merge_dependency_info(self, existing: Dependency, new: Dependency) -> None:
        """Merge dependency information, handling conflicts"""
        # Keep the more specific version if there's a difference
        if new.version and not existing.version:
            existing.version = new.version

        # Merge metadata
        existing.metadata.update(new.metadata)

        # Mark as transitive if any occurrence is transitive
        existing.is_transitive = existing.is_transitive or new.is_transitive

        # Mark as optional if any occurrence is optional
        existing.is_optional = existing.is_optional or new.is_optional

    def get_node(self, coordinates: str) -> Optional[DependencyNode]:
        """Get a dependency node by coordinates"""
        return self.nodes.get(coordinates)

    def find_conflicts(self) -> List[Tuple[DependencyNode, DependencyNode]]:
        """Find all version conflicts in the graph"""
        conflicts = []

        # Group by coordinates
        coord_groups = defaultdict(list)
        for node in self.nodes.values():
            coord_groups[node.dependency.maven_coordinates].append(node)

        # Check for version conflicts within each group
        for _coord, nodes in coord_groups.items():
            if len(nodes) > 1:
                # Check for different versions
                versions = {node.dependency.version for node in nodes}
                if len(versions) > 1:
                    # Create conflicts between all pairs of different versions
                    for i, node1 in enumerate(nodes):
                        for node2 in nodes[i+1:]:
                            if (node1.dependency.version != node2.dependency.version and
                                not (node1.dependency.is_optional and node2.dependency.is_optional)):
                                conflicts.append((node1, node2))

        self.conflicts = conflicts
        return conflicts

    def detect_cycles(self) -> List[List[DependencyNode]]:
        """Detect circular dependencies in the graph"""
        cycles = []
        visited = set()
        rec_stack = set()

        def dfs(node: DependencyNode, path: List[DependencyNode]) -> bool:
            if node in rec_stack:
                # Found a cycle
                cycle_start = next(i for i, n in enumerate(path) if n == node)
                cycles.append(path[cycle_start:] + [node])
                return True

            if node in visited:
                return False

            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for dep in node.dependencies:
                if dfs(dep, path):
                    pass  # Continue to find all cycles

            rec_stack.remove(node)
            path.pop()
            return False

        for node in self.root_dependencies:
            if node not in visited:
                dfs(node, [])

        self.cycles = cycles
        return cycles

    def get_topological_order(self) -> List[DependencyNode]:
        """Get nodes in topological dependency order"""
        # Count incoming edges
        in_degree: Dict[DependencyNode, int] = defaultdict(int)
        for node in self.nodes.values():
            for dep in node.dependencies:
                in_degree[dep] += 1

        # Start with nodes that have no dependencies
        queue = deque([node for node in self.nodes.values() if in_degree[node] == 0])
        result = []

        while queue:
            node = queue.popleft()
            result.append(node)

            # Reduce in-degree for dependents
            for dependent in node.dependents:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        # Check for cycles (nodes not in result)
        if len(result) != len(self.nodes):
            remaining = set(self.nodes.values()) - set(result)
            logger.warning(f"Circular dependencies detected: {len(remaining)} nodes not in topological order")

        return result

    def resolve_conflicts(self, strategy: str = "prefer_latest") -> bool:
        """Resolve dependency conflicts using specified strategy"""
        if not self.conflicts:
            return True

        success = True

        for node1, node2 in self.conflicts:
            try:
                resolved_node = self._resolve_conflict_pair(node1, node2, strategy)
                if resolved_node:
                    # Update the dependency information
                    if resolved_node != node1:
                        node1.dependency.conflict_resolution = resolved_node.dependency.version
                        node1.dependency.is_conflict = True
                    if resolved_node != node2:
                        node2.dependency.conflict_resolution = resolved_node.dependency.version
                        node2.dependency.is_conflict = True
                else:
                    success = False
            except Exception as e:
                logger.error(f"Error resolving conflict between {node1} and {node2}: {e}")
                success = False

        return success

    def _resolve_conflict_pair(self, node1: DependencyNode, node2: DependencyNode, strategy: str) -> Optional[DependencyNode]:  # noqa: C901
        """Resolve a specific conflict pair"""
        _dep1, _dep2 = node1.dependency, node2.dependency  # noqa: F841 (used for type validation)

        def prefer_latest(n1: DependencyNode, n2: DependencyNode) -> DependencyNode:
            if n1.dependency.version and n2.dependency.version:
                return n1 if n1.dependency.version > n2.dependency.version else n2
            if n1.dependency.version:
                return n1
            if n2.dependency.version:
                return n2
            return n1

        def prefer_compile_scope(n1: DependencyNode, n2: DependencyNode) -> DependencyNode:
            if n1.dependency.scope == DependencyScope.COMPILE and n2.dependency.scope != DependencyScope.COMPILE:
                return n1
            if n2.dependency.scope == DependencyScope.COMPILE and n1.dependency.scope != DependencyScope.COMPILE:
                return n2
            return n1

        def prefer_non_optional(n1: DependencyNode, n2: DependencyNode) -> DependencyNode:
            if not n1.dependency.is_optional and n2.dependency.is_optional:
                return n1
            if not n2.dependency.is_optional and n1.dependency.is_optional:
                return n2
            return n1

        strategy_map = {
            "prefer_latest": prefer_latest,
            "prefer_compile_scope": prefer_compile_scope,
            "prefer_non_optional": prefer_non_optional,
        }

        if strategy in strategy_map:
            return strategy_map[strategy](node1, node2)

        logger.warning(f"Unknown conflict resolution strategy: {strategy}")
        return None

    def get_dependency_tree(self, root_coordinates: Optional[str] = None) -> List[DependencyNode]:
        """Get the complete dependency tree"""
        if root_coordinates:
            root_node = self.nodes.get(root_coordinates)
            if root_node:
                dependencies = root_node.get_all_dependencies()
                dependencies.add(root_node)
                return list(dependencies)
            else:
                return []
        else:
            # Return all nodes
            return list(self.nodes.values())

    def get_leaf_dependencies(self) -> List[DependencyNode]:
        """Get all leaf dependencies (no further dependencies)"""
        leaves: List[DependencyNode] = []
        for node in self.nodes.values():
            if not node.dependencies:
                leaves.append(node)
                node.is_leaf = True
        return leaves

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the dependency graph"""
        return {
            "total_dependencies": len(self.nodes),
            "root_dependencies": len(self.root_dependencies),
            "leaf_dependencies": len(self.get_leaf_dependencies()),
            "conflicts": len(self.conflicts),
            "cycles": len(self.cycles),
            "scopes": self._get_scope_distribution(),
            "types": self._get_type_distribution(),
            "optional_dependencies": sum(1 for node in self.nodes.values() if node.dependency.is_optional),
            "transitive_dependencies": sum(1 for node in self.nodes.values() if node.dependency.is_transitive),
        }

    def _get_scope_distribution(self) -> Dict[str, int]:
        """Get distribution of dependency scopes"""
        distribution: Dict[str, int] = defaultdict(int)
        for node in self.nodes.values():
            distribution[node.dependency.scope.value] += 1
        return dict(distribution)

    def _get_type_distribution(self) -> Dict[str, int]:
        """Get distribution of dependency types"""
        distribution: Dict[str, int] = defaultdict(int)
        for node in self.nodes.values():
            distribution[node.dependency.dependency_type.value] += 1
        return dict(distribution)

    def export_graphviz(self) -> str:
        """Export the dependency graph in Graphviz DOT format"""
        lines = ["digraph dependency_graph {"]
        lines.append("  rankdir=LR;")
        lines.append("  node [shape=box, style=filled];")

        # Add nodes
        for node in self.nodes.values():
            color = self._get_node_color(node)
            label = f"{node.dependency.artifact_id}"
            if node.dependency.version:
                label += f"\\n({node.dependency.version})"
            lines.append(f'  "{node.dependency.maven_coordinates}" [label="{label}", fillcolor="{color}"];')

        # Add edges
        for node in self.nodes.values():
            for dep in node.dependencies:
                lines.append(f'  "{node.dependency.maven_coordinates}" -> "{dep.dependency.maven_coordinates}";')

        lines.append("}")
        return "\n".join(lines)

    def _get_node_color(self, node: DependencyNode) -> str:
        """Get color for a dependency node based on its properties"""
        if node.dependency.is_conflict:
            return "red"
        elif node.dependency.is_optional:
            return "lightgray"
        elif node.dependency.is_transitive:
            return "lightblue"
        elif node.is_root:
            return "lightgreen"
        else:
            return "white"

    def __repr__(self) -> str:
        return f"DependencyGraph(nodes={len(self.nodes)}, conflicts={len(self.conflicts)}, cycles={len(self.cycles)})"


def create_dependency_from_coordinates(coordinates: str,
                                     scope: DependencyScope = DependencyScope.COMPILE,
                                     dependency_type: DependencyType = DependencyType.MAVEN) -> Dependency:
    """Create a Dependency object from Maven coordinates"""
    try:
        parts = coordinates.split(":")
        if len(parts) >= 2:
            group_id = ":".join(parts[:-1])
            artifact_id = parts[-1]
            version = parts[2] if len(parts) > 2 else None
            return Dependency(group_id, artifact_id, version, scope, dependency_type)
        else:
            raise ValueError(f"Invalid Maven coordinates: {coordinates}")
    except Exception as e:
        logger.error(f"Error creating dependency from coordinates {coordinates}: {e}")
        raise

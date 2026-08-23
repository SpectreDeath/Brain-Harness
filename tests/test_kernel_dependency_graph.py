"""Tests for kernel DependencyGraph, DAG engine, wave scheduling, and cycle detection."""

from __future__ import annotations

import pytest

from harness.kernel.graph import (
    DAG,
    CyclicDependencyError,
    DependencyGraph,
    GraphCycleError,
    GraphDependencyError,
    topological_sort,
)


@pytest.mark.unit
class TestKernelDependencyGraph:
    """Test suite for DependencyGraph data structures and topological algorithms."""

    def test_empty_graph(self) -> None:
        graph = DependencyGraph[str]()
        assert graph.nodes == []
        assert graph.node_count == 0
        assert graph.edge_count == 0
        assert graph.execution_waves() == []
        assert graph.topological_sort() == []
        assert graph.detect_cycle() is None

    def test_single_node(self) -> None:
        graph = DependencyGraph[str]()
        graph.add_node("alpha", data={"type": "root"})
        assert graph.has_node("alpha")
        assert graph.get_node_data("alpha") == {"type": "root"}
        assert graph.roots() == ["alpha"]
        assert graph.leaves() == ["alpha"]
        assert graph.execution_waves() == [["alpha"]]
        assert graph.topological_sort() == ["alpha"]

    def test_linear_chain(self) -> None:
        # A -> B -> C (B depends on A, C depends on B)
        graph = DependencyGraph[str]()
        graph.add_edge("A", "B")
        graph.add_edge("B", "C")

        assert graph.node_count == 3
        assert graph.edge_count == 2
        assert graph.roots() == ["A"]
        assert graph.leaves() == ["C"]
        assert graph.dependencies_of("B") == {"A"}
        assert graph.dependents_of("B") == {"C"}
        assert graph.transitive_dependencies("C") == {"A", "B"}
        assert graph.transitive_dependents("A") == {"B", "C"}

        waves = graph.execution_waves()
        assert waves == [["A"], ["B"], ["C"]]
        assert graph.topological_sort() == ["A", "B", "C"]

    def test_diamond_dag_and_waves(self) -> None:
        #       A
        #      / \
        #     B   C
        #      \ /
        #       D
        # B depends on A, C depends on A, D depends on B and C
        graph = DAG[str]()
        graph.add_edge("A", "B")
        graph.add_edge("A", "C")
        graph.add_edge("B", "D")
        graph.add_edge("C", "D")

        assert set(graph.roots()) == {"A"}
        assert set(graph.leaves()) == {"D"}

        waves = graph.execution_waves()
        assert len(waves) == 3
        assert waves[0] == ["A"]
        assert set(waves[1]) == {"B", "C"}
        assert waves[2] == ["D"]

        order = graph.topological_sort()
        assert order[0] == "A"
        assert set(order[1:3]) == {"B", "C"}
        assert order[3] == "D"

    def test_multi_root_multi_leaf_waves(self) -> None:
        # R1 -> M1 -> L1
        # R2 -> M2 -> L2
        # R1 -> M2
        graph = DependencyGraph[str]()
        graph.add_edge("R1", "M1")
        graph.add_edge("R2", "M2")
        graph.add_edge("R1", "M2")
        graph.add_edge("M1", "L1")
        graph.add_edge("M2", "L2")

        waves = graph.execution_waves()
        assert set(waves[0]) == {"R1", "R2"}
        assert set(waves[1]) == {"M1", "M2"}
        assert set(waves[2]) == {"L1", "L2"}

    def test_cycle_detection_and_error(self) -> None:
        # A -> B -> C -> A
        graph = DependencyGraph[str]()
        graph.add_edge("A", "B")
        graph.add_edge("B", "C")
        graph.add_edge("C", "A")

        cycle = graph.detect_cycle()
        assert cycle is not None
        assert len(cycle) >= 3

        with pytest.raises(GraphCycleError) as exc_info:
            graph.execution_waves()
        assert exc_info.value.cycle is not None

        with pytest.raises(GraphCycleError):
            graph.topological_sort()

    def test_direct_self_cycle(self) -> None:
        graph = DependencyGraph[str]()
        graph.add_edge("loop", "loop")

        assert graph.detect_cycle() is not None
        with pytest.raises(GraphCycleError):
            graph.topological_sort()

    def test_add_dependency_convenience(self) -> None:
        graph = DependencyGraph[str]()
        # service depends on database
        graph.add_dependency(node="service", depends_on="database")
        assert graph.dependencies_of("service") == {"database"}
        assert graph.dependents_of("database") == {"service"}
        assert graph.topological_sort() == ["database", "service"]

    def test_to_mermaid_export(self) -> None:
        graph = DependencyGraph[str]()
        graph.add_edge("core", "plugin_a")
        graph.add_edge("core", "plugin_b")

        mermaid = graph.to_mermaid(direction="LR")
        assert "graph LR" in mermaid
        assert '"core" --> "plugin_a"' in mermaid
        assert '"core" --> "plugin_b"' in mermaid

    def test_backward_compatible_procedural_topological_sort(self) -> None:
        nodes = ["a", "b", "c", "d"]
        edges = {
            "b": {"a"},
            "c": {"a"},
            "d": {"b", "c"},
        }
        res = topological_sort(nodes, edges)
        assert res[0] == "a"
        assert set(res[1:3]) == {"b", "c"}
        assert res[3] == "d"

    def test_backward_compatible_cycle_error_subclass(self) -> None:
        nodes = ["a", "b"]
        edges = {"a": {"b"}, "b": {"a"}}
        with pytest.raises(CyclicDependencyError) as exc_info:
            topological_sort(nodes, edges)
        assert isinstance(exc_info.value, GraphCycleError)

    def test_exception_instantiation(self) -> None:
        err1 = GraphDependencyError("my_node", ["dep1", "dep2"])
        assert "my_node" in str(err1)
        assert "dep1" in str(err1)

        err2 = GraphCycleError(["x", "y", "x"])
        assert "x → y → x" in str(err2)

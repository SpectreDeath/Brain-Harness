"""Mention phrase index, DAG graph builder, and topological query analytics."""

from __future__ import annotations

import collections
from typing import Any

from plugins.data_engineering.wiki_compiler.compiler_core.models import _WORD_RE, Entity


def _build_phrase_index(entities: dict[str, Entity]) -> dict[str, list[tuple[tuple[str, ...], str]]]:
    """Build first-word prefix lookup table sorted by phrase length for greedy mention detection."""
    index: dict[str, list[tuple[tuple[str, ...], str]]] = {}
    for eid, ent in entities.items():
        words = tuple(w.lower() for w in _WORD_RE.findall(ent.name))
        if words:
            index.setdefault(words[0], []).append((words, eid))
        for alias in ent.aliases:
            awords = tuple(w.lower() for w in _WORD_RE.findall(alias))
            if awords:
                index.setdefault(awords[0], []).append((awords, eid))

    for first_word in index:
        index[first_word].sort(key=lambda pair: -len(pair[0]))

    return index


def build_graph(entities: dict[str, Entity]) -> dict[str, dict[str, set[str]]]:
    """Scan bodies of all entities and build bidirectional mention graph."""
    graph: dict[str, dict[str, set[str]]] = {eid: {"outgoing": set(), "incoming": set()} for eid in entities}
    if not entities:
        return graph

    phrase_index = _build_phrase_index(entities)

    for eid, ent in entities.items():
        tokens = [w.lower() for w in _WORD_RE.findall(ent.body)]
        seen_targets = set()
        n = len(tokens)
        i = 0
        while i < n:
            candidates = phrase_index.get(tokens[i])
            if candidates:
                for words, target_id in candidates:
                    end = i + len(words)
                    if end <= n and tuple(tokens[i:end]) == words:
                        if target_id != eid:
                            seen_targets.add(target_id)
                        break
            i += 1

        for target_id in seen_targets:
            if target_id in graph:
                graph[eid]["outgoing"].add(target_id)
                graph[target_id]["incoming"].add(eid)

    return graph


def orphan_ids(graph: dict[str, dict[str, set[str]]]) -> list[str]:
    """Return entity IDs that have no incoming links."""
    return sorted(eid for eid, edges in graph.items() if not edges["incoming"])


class WikiGraphQuery:
    """Graph analytics engine for topological querying over the wiki mention graph."""

    def __init__(self, graph: dict[str, dict[str, set[str]]], entities: dict[str, Entity]) -> None:
        self.graph = graph
        self.entities = entities

    def get_backlinks(self, entity_id: str) -> list[dict[str, str]]:
        """Return incoming references linking to entity_id."""
        if entity_id not in self.graph:
            return []
        return [
            {"entity_id": inc_id, "name": self.entities[inc_id].name if inc_id in self.entities else inc_id}
            for inc_id in sorted(self.graph[entity_id]["incoming"])
        ]

    def get_neighborhood(self, entity_id: str, max_hops: int = 2) -> dict[str, Any]:
        """Compute BFS neighborhood subgraph up to max_hops from entity_id."""
        if entity_id not in self.graph:
            return {"root": entity_id, "nodes": [], "edges": []}

        visited = {entity_id: 0}
        queue = collections.deque([(entity_id, 0)])
        edges_out = []

        while queue:
            curr, depth = queue.popleft()
            if depth >= max_hops:
                continue

            # explore outgoing and incoming
            neighbors = sorted(self.graph[curr]["outgoing"] | self.graph[curr]["incoming"])
            for nbr in neighbors:
                if nbr not in visited:
                    visited[nbr] = depth + 1
                    queue.append((nbr, depth + 1))
                if (curr, nbr) not in edges_out:
                    edges_out.append((curr, nbr))

        nodes_out = [
            {"entity_id": node_id, "name": self.entities[node_id].name if node_id in self.entities else node_id, "hop": hop}
            for node_id, hop in sorted(visited.items(), key=lambda kv: kv[1])
        ]

        return {
            "root": entity_id,
            "max_hops": max_hops,
            "node_count": len(nodes_out),
            "nodes": nodes_out,
            "edges": [{"source": src, "target": tgt} for src, tgt in edges_out],
        }

    def find_path(self, source_id: str, target_id: str) -> list[str] | None:
        """Find the shortest directed reference path from source to target entity."""
        if source_id not in self.graph or target_id not in self.graph:
            return None
        if source_id == target_id:
            return [source_id]

        queue = collections.deque([[source_id]])
        visited = {source_id}

        while queue:
            path = queue.popleft()
            curr = path[-1]
            for nbr in sorted(self.graph[curr]["outgoing"]):
                if nbr == target_id:
                    return [*path, nbr]
                if nbr not in visited:
                    visited.add(nbr)
                    queue.append([*path, nbr])

        return None

    def get_clusters(self) -> list[list[str]]:
        """Compute weakly connected components of the wiki graph."""
        visited = set()
        clusters = []

        for eid in self.graph:
            if eid in visited:
                continue
            component = []
            queue = collections.deque([eid])
            visited.add(eid)

            while queue:
                curr = queue.popleft()
                component.append(curr)
                all_neighbors = self.graph[curr]["outgoing"] | self.graph[curr]["incoming"]
                for nbr in all_neighbors:
                    if nbr not in visited:
                        visited.add(nbr)
                        queue.append(nbr)

            clusters.append(sorted(component))

        clusters.sort(key=lambda c: -len(c))
        return clusters

"""Core algorithmic engine for knowledge graph clustering and capability synthesis."""

from __future__ import annotations

import collections
import math
import re
from typing import Any

import structlog

from harness.kernel.graph import DependencyGraph, GraphCycleError
from harness.services.skill_clustering.models import (
    CrossClusterBridge,
    EmergentCapability,
    SkillCluster,
    SkillSelectionPlan,
)
from harness.services.skill_clustering.patterns import CANONICAL_EMERGENT_PATTERNS

logger = structlog.get_logger()


class SkillClusteringEngine:
    """Core algorithmic engine for knowledge graph clustering and capability synthesis."""

    # Canonical high-order capability patterns recognized across the Brain Harness ecosystem
    CANONICAL_EMERGENT_PATTERNS = CANONICAL_EMERGENT_PATTERNS

    def __init__(
        self,
        skills_input: dict[str, Any] | list[Any] | None = None,
        registry: Any = None,
    ) -> None:
        """Initialize engine with a dictionary, list, or authoritative SkillRegistryService."""
        self._registry = registry
        if skills_input is None and registry is not None:
            if hasattr(registry, "_skills_cache") and registry._skills_cache:
                self._skills = dict(registry._skills_cache)
            elif hasattr(registry, "discover_all"):
                self._skills = {s.name: s for s in registry.discover_all()}
            else:
                self._skills = {}
        elif isinstance(skills_input, list):
            self._skills = {
                getattr(s, "name", str(s)): s for s in skills_input
            }
        elif isinstance(skills_input, dict):
            self._skills = dict(skills_input)
        else:
            self._skills = {}

        self._clusters_cache: list[SkillCluster] | None = None
        self._bridges_cache: list[CrossClusterBridge] | None = None

    @classmethod
    def _tokenize(cls, text: str) -> set[str]:
        """Tokenize string into normalized keyword set, filtering common English stopwords."""
        stopwords = {
            "and", "the", "for", "with", "from", "using", "that", "this", "into",
            "across", "not", "use", "when", "what", "which", "are", "you", "user",
            "will", "can", "how", "all", "each", "have", "more", "such", "than",
        }
        return {
            w.lower()
            for w in re.findall(r"[a-zA-Z]{3,}", text)
            if w.lower() not in stopwords
        }

    def compute_affinity_matrix(self) -> dict[str, dict[str, float]]:
        """Compute pairwise structural and semantic affinity weights between skills with degree normalization."""
        skill_tokens: dict[str, set[str]] = {}
        in_degrees: dict[str, int] = collections.defaultdict(int)

        for name, s in self._skills.items():
            category = getattr(s, "category", "") or ""
            target = getattr(s, "target", "") or ""
            description = getattr(s, "description", "") or ""
            triggers = getattr(s, "triggers", []) or []
            stages = getattr(s, "stages", []) or []
            stage_names = " ".join(getattr(st, "name", "") for st in stages)

            text = f"{name} {category} {description} {target} {' '.join(triggers)} {stage_names}"
            skill_tokens[name] = self._tokenize(text)

            deps = set(getattr(s, "dependencies", []) or getattr(s, "references", []) or [])
            for dep in deps:
                if dep in self._skills:
                    in_degrees[dep] += 1

        adj: dict[str, dict[str, float]] = collections.defaultdict(dict)

        for s1, node1 in self._skills.items():
            deps1 = set(getattr(node1, "dependencies", []) or getattr(node1, "references", []) or [])
            cat1 = (getattr(node1, "category", "") or "").lower()
            cat1_prefix = cat1.split("/")[0].strip()

            for s2, node2 in self._skills.items():
                if s1 == s2:
                    continue

                deps2 = set(getattr(node2, "dependencies", []) or getattr(node2, "references", []) or [])
                cat2 = (getattr(node2, "category", "") or "").lower()
                cat2_prefix = cat2.split("/")[0].strip()

                weight = 0.0

                # 1. Topological dependencies & references with degree dampening (Rule of specificity)
                if s2 in deps1:
                    deg2 = in_degrees.get(s2, 1)
                    dampener = 1.0 / math.log2(2.0 + deg2)
                    weight += 4.5 * dampener
                if s1 in deps2:
                    deg1 = in_degrees.get(s1, 1)
                    dampener = 1.0 / math.log2(2.0 + deg1)
                    weight += 4.5 * dampener

                # 1b. Authoritative typed edge affinity when registry is present
                if self._registry is not None and hasattr(self._registry, "_edge_keys"):
                    from harness.services.skill_graph import EdgeType
                    edge_keys = self._registry._edge_keys
                    if (s1, s2, EdgeType.PRECEDES) in edge_keys or (s2, s1, EdgeType.PRECEDES) in edge_keys:
                        weight += 1.2
                    if (s1, s2, EdgeType.COMPLEMENTS) in edge_keys or (s2, s1, EdgeType.COMPLEMENTS) in edge_keys:
                        weight += 1.5

                # 2. Shared dependencies (co-referencing)
                common_deps = deps1 & deps2
                if common_deps:
                    weight += min(len(common_deps) * 0.8, 2.0)

                # 3. Category hierarchy alignment
                if cat1 and cat2 and cat1 != "general" and cat2 != "general":
                    if cat1 == cat2:
                        weight += 2.5
                    elif cat1_prefix == cat2_prefix:
                        weight += 1.5

                # 4. Semantic token Jaccard similarity
                tok1 = skill_tokens[s1]
                tok2 = skill_tokens[s2]
                if tok1 and tok2:
                    jaccard = len(tok1 & tok2) / len(tok1 | tok2)
                    if jaccard > 0.07:
                        weight += jaccard * 5.0

                # Threshold to keep graph sparse and meaningful
                if weight >= 1.6:
                    adj[s1][s2] = weight

        return adj

    def build_clusters(self, min_cluster_size: int = 2) -> list[SkillCluster]:
        """Alias for cluster_skills."""
        return self.cluster_skills(min_cluster_size=min_cluster_size)

    def cluster_skills(self, min_cluster_size: int = 2) -> list[SkillCluster]:
        """Cluster skills into functional domains using modular community detection."""
        if self._clusters_cache is not None:
            return self._clusters_cache

        adj = self.compute_affinity_matrix()
        skills_list = sorted(self._skills.keys())

        # Seed initial labels
        labels: dict[str, str] = {s: s for s in skills_list}

        # Multi-pass Label Propagation with deterministic tie-breaking
        for _ in range(10):
            changed = False
            for s in skills_list:
                neighbor_weights: dict[str, float] = collections.defaultdict(float)
                # Self-reinforcement
                neighbor_weights[labels[s]] += 1.0

                for nbr, w in adj.get(s, {}).items():
                    neighbor_weights[labels[nbr]] += w

                best_label = max(
                    neighbor_weights.items(), key=lambda item: (item[1], -len(item[0]), item[0])
                )[0]

                if best_label != labels[s]:
                    labels[s] = best_label
                    changed = True

            if not changed:
                break

        # Group into raw clusters
        raw_clusters: dict[str, list[str]] = collections.defaultdict(list)
        for s, label in labels.items():
            raw_clusters[label].append(s)

        # Split mega-clusters (size > 14) along secondary category sub-partitions
        refined_clusters: list[list[str]] = []
        for members in raw_clusters.values():
            if len(members) <= 14:
                refined_clusters.append(sorted(members))
            else:
                # Sub-cluster by category / semantic prefix
                sub_groups: dict[str, list[str]] = collections.defaultdict(list)
                for m in members:
                    m_cat = getattr(self._skills[m], "category", "general")
                    clean_cat = m_cat.split("/")[0].strip()
                    sub_groups[clean_cat].append(m)

                for sub_members in sub_groups.values():
                    refined_clusters.append(sorted(sub_members))

        # Re-merge singletons into best matching clusters
        final_clusters_lists: list[list[str]] = []
        singletons: list[str] = []
        for c in refined_clusters:
            if len(c) >= min_cluster_size:
                final_clusters_lists.append(c)
            else:
                singletons.extend(c)

        for s in singletons:
            best_c: list[str] | None = None
            max_aff = -1.0
            for c in final_clusters_lists:
                aff = sum(adj.get(s, {}).get(m, 0.0) for m in c)
                if aff > max_aff:
                    max_aff = aff
                    best_c = c
            if best_c:
                best_c.append(s)
            elif final_clusters_lists:
                final_clusters_lists[0].append(s)
            else:
                final_clusters_lists.append([s])

        # Filter strictly by min_cluster_size
        final_clusters_lists = [c for c in final_clusters_lists if len(c) >= min_cluster_size]

        # Construct formal SkillCluster objects
        clusters: list[SkillCluster] = []
        for idx, members in enumerate(sorted(final_clusters_lists, key=lambda x: len(x), reverse=True), start=1):
            if not members:
                continue

            # Identify central hub skill (highest internal degree)
            hub_skill = max(
                members,
                key=lambda m: sum(1 for other in members if other in (getattr(self._skills[m], "dependencies", []) or []))
                + sum(1 for other in members if m in (getattr(self._skills[other], "dependencies", []) or [])),
            )

            # Count internal edges
            internal_edges = 0
            for m in members:
                node = self._skills[m]
                deps = set(getattr(node, "dependencies", []) or getattr(node, "references", []) or [])
                internal_edges += len(deps.intersection(members))

            categories = sorted({getattr(self._skills[m], "category", "general") for m in members})
            primary_domain = categories[0] if categories else "general"

            cluster_id = f"cluster_{idx:02d}_{hub_skill.replace('-', '_')}"
            clean_name = f"{hub_skill.replace('-', ' ').title()} & Domain Peers"

            # Match or synthesize emergent capabilities
            emergent_caps: list[EmergentCapability] = []
            for pat in self.CANONICAL_EMERGENT_PATTERNS:
                matching_core = [s for s in pat["core_skills"] if s in members]
                if len(matching_core) >= 2 or (len(pat["core_skills"]) <= 2 and len(matching_core) >= 1):
                    guarded_aps = []
                    guaranteed_invs = []
                    for s_name in matching_core:
                        s_obj = self._skills[s_name]
                        for ap in getattr(s_obj, "anti_patterns", []):
                            ap_name = getattr(ap, "name", "")
                            if ap_name and ap_name not in guarded_aps:
                                guarded_aps.append(ap_name)
                        for inv in getattr(s_obj, "invariants", []):
                            inv_rule = getattr(inv, "rule", "")
                            if inv_rule and inv_rule not in guaranteed_invs:
                                guaranteed_invs.append(inv_rule)

                    emergent_caps.append(
                        EmergentCapability(
                            id=pat["id"],
                            title=pat["title"],
                            description=pat["rationale"],
                            cluster_id=cluster_id,
                            primary_skills=matching_core,
                            recommended_pipeline=[s for s in pat["pipeline"] if s in self._skills],
                            novelty_rationale=pat["rationale"],
                            guarded_anti_patterns=guarded_aps[:6],
                            guaranteed_invariants=guaranteed_invs[:6],
                            keywords=sorted(pat.get("keywords", [])),
                            target_outcomes=pat["outcomes"],
                        )
                    )

            # Dynamic emergent capability synthesis for clusters without a canonical match
            if not emergent_caps and len(members) >= 2:
                member_targets = [
                    getattr(self._skills[m], "target", "") or getattr(self._skills[m], "description", "")
                    for m in members[:3]
                ]
                synth_guarded_aps = []
                synth_invs = []
                for m in members:
                    for ap in getattr(self._skills[m], "anti_patterns", []):
                        ap_name = getattr(ap, "name", "")
                        if ap_name and ap_name not in synth_guarded_aps:
                            synth_guarded_aps.append(ap_name)
                    for inv in getattr(self._skills[m], "invariants", []):
                        inv_rule = getattr(inv, "rule", "")
                        if inv_rule and inv_rule not in synth_invs:
                            synth_invs.append(inv_rule)

                synth_title = f"Composite {hub_skill.replace('-', ' ').title()} & Domain Synthesis"
                synth_desc = (
                    f"Integrates {', '.join(members[:4])} into an end-to-end {primary_domain} pipeline, "
                    f"combining: {' | '.join(t for t in member_targets if t)[:160]}."
                )
                emergent_caps.append(
                    EmergentCapability(
                        id=f"cap_synth_{cluster_id}",
                        title=synth_title,
                        description=synth_desc,
                        cluster_id=cluster_id,
                        primary_skills=members[:5],
                        recommended_pipeline=members[:5],
                        novelty_rationale=(
                            f"Collectively coordinates {len(members)} peer skills to eliminate siloed execution "
                            f"in {primary_domain} with shared verification."
                        ),
                        guarded_anti_patterns=synth_guarded_aps[:6],
                        guaranteed_invariants=synth_invs[:6],
                        keywords=sorted(set(self._tokenize(" ".join(members) + " " + primary_domain))),
                        target_outcomes=[f"End-to-end {primary_domain} domain artifacts"],
                    )
                )

            # Calculate cohesion score
            n = len(members)
            max_edges = n * (n - 1) if n > 1 else 1
            cohesion = round(min(1.0, max(0.1, internal_edges / max(1, max_edges))), 3)

            cluster = SkillCluster(
                cluster_id=cluster_id,
                name=clean_name,
                domain=primary_domain,
                skills=sorted(members),
                central_hub_skill=hub_skill,
                categories=categories,
                internal_edge_count=internal_edges,
                cohesion_score=cohesion,
                emergent_capabilities=emergent_caps,
            )
            clusters.append(cluster)

        self._clusters_cache = clusters
        return clusters

    def discover_emergent_capabilities(
        self, query: str | None = None
    ) -> list[EmergentCapability]:
        """Retrieve all emergent capabilities across clusters, optionally filtered by query."""
        clusters = self.cluster_skills()
        all_caps: list[EmergentCapability] = []
        for c in clusters:
            all_caps.extend(c.emergent_capabilities)

        unique_caps: dict[str, EmergentCapability] = {}
        for cap in all_caps:
            if cap.id not in unique_caps:
                unique_caps[cap.id] = cap

        # Ensure all canonical emergent patterns whose core skills exist in graph are included
        for pat in self.CANONICAL_EMERGENT_PATTERNS:
            matching_core = [s for s in pat["core_skills"] if s in self._skills]
            if len(matching_core) >= 2 and pat["id"] not in unique_caps:
                guarded_aps = []
                guaranteed_invs = []
                for s_name in matching_core:
                    s_obj = self._skills[s_name]
                    for ap in getattr(s_obj, "anti_patterns", []):
                        ap_name = getattr(ap, "name", "")
                        if ap_name and ap_name not in guarded_aps:
                            guarded_aps.append(ap_name)
                    for inv in getattr(s_obj, "invariants", []):
                        inv_rule = getattr(inv, "rule", "")
                        if inv_rule and inv_rule not in guaranteed_invs:
                            guaranteed_invs.append(inv_rule)

                unique_caps[pat["id"]] = EmergentCapability(
                    id=pat["id"],
                    title=pat["title"],
                    description=pat["rationale"],
                    cluster_id="cluster_cross_domain",
                    primary_skills=matching_core,
                    recommended_pipeline=[s for s in pat["pipeline"] if s in self._skills],
                    novelty_rationale=pat["rationale"],
                    guarded_anti_patterns=guarded_aps[:6],
                    guaranteed_invariants=guaranteed_invs[:6],
                    keywords=sorted(pat.get("keywords", [])),
                    target_outcomes=pat["outcomes"],
                )

        res = list(unique_caps.values())
        if not query:
            return res

        q_tokens = self._tokenize(query)
        scored_caps = []
        for cap in res:
            cap_tokens = self._tokenize(
                f"{cap.title} {cap.description} {' '.join(cap.primary_skills)} {' '.join(cap.keywords)}"
            )
            overlap = len(q_tokens & cap_tokens)
            keyword_overlap = len(q_tokens & set(cap.keywords))
            score = overlap + 2.0 * keyword_overlap
            if score > 0:
                scored_caps.append((score, cap))

        scored_caps.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in scored_caps]

    def get_cross_cluster_bridges(self) -> list[CrossClusterBridge]:
        """Detect cross-cluster bridges where directed edges connect distinct capability clusters."""
        if self._bridges_cache is not None:
            return self._bridges_cache

        clusters = self.cluster_skills()
        skill_to_cluster: dict[str, str] = {}
        for c in clusters:
            for s in c.skills:
                skill_to_cluster[s] = c.cluster_id

        cluster_edges: dict[tuple[str, str], list[tuple[str, str]]] = collections.defaultdict(list)

        for s_name, skill in self._skills.items():
            src_c = skill_to_cluster.get(s_name)
            if not src_c:
                continue
            deps = getattr(skill, "dependencies", []) or getattr(skill, "references", []) or []
            for dep in deps:
                tgt_c = skill_to_cluster.get(dep)
                if tgt_c and tgt_c != src_c:
                    cluster_edges[(src_c, tgt_c)].append((s_name, dep))

        bridges: list[CrossClusterBridge] = []
        for (src_c, tgt_c), pairs in cluster_edges.items():
            if len(pairs) >= 1:
                src_cluster = next((c for c in clusters if c.cluster_id == src_c), None)
                tgt_cluster = next((c for c in clusters if c.cluster_id == tgt_c), None)
                if src_cluster and tgt_cluster:
                    bridges.append(
                        CrossClusterBridge(
                            source_cluster=src_c,
                            target_cluster=tgt_c,
                            bridge_skills=pairs[:5],
                            synergy_description=f"Inter-domain synthesis bridging {src_cluster.name} and {tgt_cluster.name}.",
                        )
                    )

        self._bridges_cache = bridges
        return bridges

    def detect_cross_cluster_bridges(self) -> list[CrossClusterBridge]:
        """Alias for get_cross_cluster_bridges."""
        return self.get_cross_cluster_bridges()

    def select_skills_for_task(
        self,
        task: str,
        max_skills: int = 5,
        include_verifier: bool = True,
    ) -> SkillSelectionPlan:
        """Analyze task intent and synthesize a prerequisite-aware execution plan."""
        task_clean = task.strip().lower()
        task_tokens = self._tokenize(task_clean)

        # 1. Match against Emergent Capabilities first
        emergent_caps = self.discover_emergent_capabilities(query=task)
        matched_cap: EmergentCapability | None = emergent_caps[0] if emergent_caps else None

        # 2. Score individual skills (unified with authoritative route_intent when registry is available)
        skill_scores: list[tuple[float, str]] = []
        if self._registry is not None and hasattr(self._registry, "route_intent"):
            try:
                routed = self._registry.route_intent(task, top_k=max_skills * 2, min_confidence=0.15)
                for m in routed.get("matches", []):
                    s_name = m.get("skill_name")
                    conf = float(m.get("confidence", 0.0))
                    if s_name and s_name in self._skills:
                        skill_scores.append((conf * 10.0, s_name))
            except Exception:
                pass

        scored_skills_set = {s for _, s in skill_scores}
        for name, skill in self._skills.items():
            if name in scored_skills_set:
                continue
            score = 0.0
            name_clean = name.replace("-", " ")
            if name_clean in task_clean:
                score += 4.0
            if name in task_clean:
                score += 3.5

            triggers = getattr(skill, "triggers", []) or []
            for t in triggers:
                t_lower = t.lower()
                if t_lower in task_clean:
                    score += 3.0
                else:
                    t_toks = self._tokenize(t_lower)
                    overlap = len(task_tokens & t_toks)
                    if overlap:
                        score += 0.8 * overlap

            target = (getattr(skill, "target", "") or getattr(skill, "description", "")).lower()
            target_toks = self._tokenize(target)
            overlap = len(task_tokens & target_toks)
            if overlap:
                score += 0.3 * overlap

            if score > 0.0:
                skill_scores.append((score, name))

        skill_scores.sort(key=lambda x: x[0], reverse=True)

        # 3. Determine selected core skills (bounded to max_skills)
        selected_skills: list[str] = []
        primary_cluster: str | None = None

        if matched_cap and matched_cap.recommended_pipeline:
            for s in matched_cap.recommended_pipeline:
                if s not in selected_skills and len(selected_skills) < max_skills:
                    selected_skills.append(s)
            primary_cluster = matched_cap.cluster_id

        # Fill with top scored individual skills
        for _, s_name in skill_scores:
            if s_name not in selected_skills and len(selected_skills) < max_skills:
                selected_skills.append(s_name)

        if not selected_skills:
            selected_skills = ["deepen-architecture", "adversarial-agent-verifier"]

        # 4. Immediate prerequisite resolution (bounded to 1-2 direct dependencies)
        immediate_prereqs: list[str] = []
        for s_name in selected_skills:
            s_obj = self._skills.get(s_name)
            if not s_obj:
                continue
            deps = getattr(s_obj, "dependencies", []) or getattr(s_obj, "references", []) or []
            for dep in deps:
                clean_dep = dep.strip().lower().replace("_", "-").lstrip("/")
                if clean_dep in self._skills and clean_dep not in selected_skills and clean_dep not in immediate_prereqs:
                    immediate_prereqs.append(clean_dep)
                    if len(immediate_prereqs) >= 2:
                        break
            if len(immediate_prereqs) >= 2:
                break

        # Assemble candidate nodes (prerequisites first, then selected core skills)
        candidate_nodes: list[str] = [p for p in immediate_prereqs if p not in selected_skills] + list(selected_skills)

        # 5. Topologically sort the candidate skills using DependencyGraph
        dag: DependencyGraph[str] = DependencyGraph()
        for node in candidate_nodes:
            dag.add_node(node)

        # Add declared dependency edges: from prerequisite -> to dependent
        for s_name in candidate_nodes:
            s_obj = self._skills.get(s_name)
            if not s_obj:
                continue
            deps = getattr(s_obj, "dependencies", []) or getattr(s_obj, "references", []) or []
            for dep in deps:
                clean_dep = dep.strip().lower().replace("_", "-").lstrip("/")
                if clean_dep in candidate_nodes and clean_dep != s_name:
                    if clean_dep in dag.transitive_dependents(s_name):
                        logger.debug(
                            "Skipping cyclic dependency edge in skill graph",
                            from_node=clean_dep,
                            to_node=s_name,
                        )
                        continue
                    dag.add_edge(from_node=clean_dep, to_node=s_name)

        # If matched emergent capability has an explicit pipeline, encode those sequential edges
        if matched_cap and matched_cap.recommended_pipeline:
            rec = [s for s in matched_cap.recommended_pipeline if s in candidate_nodes]
            for i in range(len(rec) - 1):
                s_from, s_to = rec[i], rec[i + 1]
                if s_from != s_to and s_from not in dag.transitive_dependents(s_to):
                    dag.add_edge(from_node=s_from, to_node=s_to)

        try:
            sorted_pipeline = dag.topological_sort()
            pipeline = [n for n in sorted_pipeline if n in candidate_nodes]
            for n in candidate_nodes:
                if n not in pipeline:
                    pipeline.append(n)
        except GraphCycleError as err:
            logger.debug(
                "Cycle detected in skill dependency graph, falling back to candidate order",
                cycle=err.cycle,
            )
            pipeline = list(candidate_nodes)

        # 6. Tail verifier injection (Rule 8, Rule 13)
        verifier_skill = None
        if include_verifier:
            verifier_candidates = ["adversarial-agent-verifier", "questio-reflection", "code-review"]
            for v in verifier_candidates:
                if v in self._skills:
                    verifier_skill = v
                    break

        if verifier_skill:
            if verifier_skill in pipeline:
                pipeline.remove(verifier_skill)
            pipeline.append(verifier_skill)

        # 7. Assemble ordered stages with crisp completion gates
        assembled_stages: list[dict[str, Any]] = []
        active_anti_patterns: list[dict[str, str]] = []
        active_invariants: list[dict[str, Any]] = []

        seen_ap = set()
        seen_inv = set()

        for s_name in pipeline:
            s_obj = self._skills.get(s_name)
            if not s_obj:
                continue

            stages = getattr(s_obj, "stages", []) or []
            if stages:
                for st in stages:
                    assembled_stages.append({
                        "skill": s_name,
                        "stage_num": getattr(st, "stage_num", 1),
                        "name": getattr(st, "name", "Stage"),
                        "completion_gate": getattr(st, "completion_gate", "") or getattr(st, "objective", ""),
                    })
            else:
                assembled_stages.append({
                    "skill": s_name,
                    "stage_num": 1,
                    "name": f"Execute {s_name}",
                    "completion_gate": f"Output artifact from {s_name} generated",
                })

            for ap in getattr(s_obj, "anti_patterns", []):
                ap_name = getattr(ap, "name", "")
                if ap_name and ap_name not in seen_ap:
                    seen_ap.add(ap_name)
                    active_anti_patterns.append({
                        "skill": s_name,
                        "anti_pattern": ap_name,
                        "symptom": getattr(ap, "symptom", "") or getattr(ap, "description", ""),
                        "remedy": getattr(ap, "remedy", "") or getattr(ap, "mitigation", ""),
                    })

            for inv in getattr(s_obj, "invariants", []):
                rule = getattr(inv, "rule", "")
                if rule and rule not in seen_inv:
                    seen_inv.add(rule)
                    active_invariants.append({
                        "skill": s_name,
                        "rule": rule,
                        "is_blocking": getattr(inv, "is_blocking", True),
                    })

        # Calculate confidence
        top_score = skill_scores[0][0] if skill_scores else 1.0
        confidence = min(0.98, max(0.35, 0.4 + (top_score / 15.0)))
        if matched_cap:
            confidence = min(0.99, confidence + 0.15)

        # Build human-readable rationale
        if matched_cap:
            rationale = (
                f"Task strongly matched emergent capability '{matched_cap.title}' ({matched_cap.id}). "
                f"Assembled topological pipeline: {' → '.join(pipeline)}. "
                f"{matched_cap.novelty_rationale}"
            )
        else:
            rationale = (
                f"Task routed to top matching domain skills: {', '.join(selected_skills[:3])}. "
                f"Topological pipeline chained {len(pipeline)} skills with {len(assembled_stages)} execution gates "
                f"and {len(active_anti_patterns)} guarded anti-patterns."
            )

        return SkillSelectionPlan(
            task=task,
            selected_skills=selected_skills,
            execution_pipeline=pipeline,
            emergent_capability=matched_cap,
            primary_cluster=primary_cluster,
            prerequisites=immediate_prereqs,
            stages=assembled_stages,
            active_anti_patterns=active_anti_patterns[:8],
            active_invariants=active_invariants[:8],
            recommended_verifier=verifier_skill,
            confidence=round(confidence, 3),
            rationale=rationale,
        )


__all__ = ["SkillClusteringEngine"]

"""Prompts for Propose-Probe-Compose recursion, written as values (never as branches).

Distilled from google-research/harness2 `core.prompts` (reworded, condensed). Design commitments kept:
two *orthogonal* proposal dimensions (INV = how the agent works; DOM = what a practitioner
knows) so parallel candidates do not collapse into one; evidence-is-data injection defence;
an explicit answer-free statement; `KEEP_BASE` as a first-class valid answer; and decision
notes that must cite a trajectory moment for every kept/revised/dropped edit.
"""

from __future__ import annotations

from harness.services.recursive_harnessing.models import SurfaceSpec
from harness.services.recursive_harnessing.prompt_templates import (
    ANSWER_FREE,
    EVIDENCE_BOUNDARY,
    GENERALIZE,
    KEEP_BASE,
    NOTES_FORMAT,
    VERSION,
    _DOM,
    _INV,
    _MEASUREMENT_WORDS,
    _parts,
    check_work_text,
    surface_block,
)

__all__ = [
    "ANSWER_FREE",
    "EVIDENCE_BOUNDARY",
    "GENERALIZE",
    "KEEP_BASE",
    "NOTES_FORMAT",
    "VERSION",
    "aggregate",
    "check_work_text",
    "compose_round",
    "experience",
    "propose",
    "select",
    "surface_block",
]


def propose(
    spec: SurfaceSpec,
    dim: str,
    *,
    work: str,
    deliverable: str = "deliverable",
    k: int = 1,
    index: int = 1,
    round_t: int | None = None,
    yardstick: str = "",
) -> str:
    """One candidate proposal for dimension `dim` ("INV" or "DOM")."""
    if dim not in ("INV", "DOM"):
        raise ValueError(f"unknown dimension {dim!r}; expected 'INV' or 'DOM'")
    head = f"You are proposing ONE edit-set to a working harness (candidate {index} of {k}"
    head += f", round {round_t}" if round_t else ""
    head += "). It will be rolled out ONCE on this same task and compared."
    return _parts(
        head,
        f"# THE WORK\n\n{check_work_text(work)}",
        (_INV if dim == "INV" else _DOM).format(deliverable=deliverable),
        f"# WHAT GOOD PROCESS LOOKS LIKE HERE\n\n{yardstick.strip()}" if yardstick.strip() else "",
        GENERALIZE,
        KEEP_BASE,
        ANSWER_FREE,
        EVIDENCE_BOUNDARY,
        surface_block(spec),
        "Finish with a `<notes>` block: what you changed, the trajectory moment that justifies it.",
    )


def aggregate(spec: SurfaceSpec, *, work: str, k: int = 1, index: int = 1) -> str:
    """Compose ONE final harness from all base evidence and all 2k candidates (parallel mode)."""
    base = f"{k} base rollout{'s' if k > 1 else ''}"
    return _parts(
        "You are composing THE final harness. What you emit is ADOPTED: it runs on this task and, if "
        "selected, enters this domain's library. Every rule that bound the proposers binds you -- "
        "merging an edit launders it.",
        f"# THE WORK\n\n{check_work_text(work)}",
        f"# WHAT YOU HAVE\n\n{base} under the unmodified harness and {2 * k} candidate harnesses "
        f"({k} INV, {k} DOM), each rolled out once. Candidates share task, evidence and model biases: "
        "agreement is support, not independent proof; contradiction is a reason to read the "
        "trajectories, not to vote.",
        "# HOW TO WEIGH THE EVIDENCE\n\n- A failure repeating across the base set is a real property "
        f"of the base harness; a defect in 1/{k} is noise.\n- A candidate has ONE rollout: name the "
        "SPECIFIC MOMENT that shows the mechanism; 'looks like good practice' is not evidence.\n"
        "- Weigh downside as heavily as upside; the costliest failure is a run that produces nothing.\n"
        "- If a rollout tied to an edit produced NOTHING, say so and treat that edit as UNSAFE unless "
        "the rest of the evidence is overwhelming.",
        "# YOUR JOB\n\nCompose ONE harness: MERGE across candidates (resolve overlaps, do not "
        "concatenate), ADOPT ONE wholesale, or KEEP_BASE.\n\n" + KEEP_BASE,
        f"You are one of {k} aggregators who will not see each other; commit to the harness you can "
        "defend, not the consensus."
        if k > 1
        else "",
        ANSWER_FREE,
        EVIDENCE_BOUNDARY,
        surface_block(spec),
        NOTES_FORMAT,
    )


def compose_round(spec: SurfaceSpec, *, work: str, t: int, k: int) -> str:
    """Compose checkpoint C_t from this round's candidates and every earlier round (sequential)."""
    final = t >= k
    return _parts(
        f"You are composing checkpoint {t} of {k} in a sequential adaptation loop.",
        f"# THE WORK\n\n{check_work_text(work)}",
        "# WHAT YOU HAVE\n\nThe shared base rollouts, this round's INV and DOM candidates with their "
        "rollouts, and every earlier round's candidates, checkpoints and trajectories. The previous "
        "checkpoint's own rollout is on-policy evidence of what the harness you are editing does.",
        "# YOUR JOB\n\n"
        + (
            "Compose THE FINAL harness from the WHOLE history.\n"
            if final
            else f"Compose checkpoint {t}; the next round builds on it.\n"
        )
        + "Valid: MERGE across rounds (including a candidate rejected earlier if later evidence now "
        "argues for it), REPRODUCE an earlier checkpoint verbatim if later rounds drifted from the "
        "best state, ADOPT this round's best candidate, or KEEP_BASE (= keep the CURRENT checkpoint "
        "in `context/harness/`).\n\n" + KEEP_BASE,
        ANSWER_FREE,
        EVIDENCE_BOUNDARY,
        surface_block(spec),
        NOTES_FORMAT,
    )


def select(*, work: str, n: int, deliverable: str = "deliverable") -> str:
    """Blind selection prompt over `n` anonymous candidate artifacts."""
    return _parts(
        f"You are choosing which of {n} candidate answers should be delivered to the person who asked for this work.",
        f"# THE WORK\n\n{check_work_text(work)}",
        "# THE CANDIDATES ARE ANONYMOUS ON PURPOSE\n\nIds are arbitrary and shuffled. No candidate is "
        "privileged and there is no credit for a more elaborate one; when several look alike, decide "
        "on the small differences that matter.",
        f"# HOW TO DECIDE, IN THIS ORDER\n\n1. DELIVERY: is every {deliverable} the instructions name "
        "present, in the requested form?\n2. CONFORMANCE: is it ONLY what was asked? Extra or renamed "
        "parts are deviations.\n3. FIDELITY: check claims against `context/source/`; reject invented "
        "specifics.\n4. INTERNAL CONSISTENCY: totals, cross-references and counts agree.\n5. FINISH: "
        "no placeholders or unresolved notes. Length and polish are not merits.",
        ANSWER_FREE.replace("trajectories show", "source material shows"),
        EVIDENCE_BOUNDARY,
        "# OUTPUT FORMAT\n\n<why>at most 6 lines: the deciding criterion and the closest runner-up"
        "</why>\n\n```choice\n<id of the single candidate>\n```",
    )


def experience(*, work: str) -> str:
    """Distil what each edit did and the ONE transferable lesson (cue / lesson / evidence)."""
    return _parts(
        "You are reading the complete record of one improvement round. Write two things for a "
        "library that future work in this domain reads before making its own edits.",
        f"# THE WORK\n\n{check_work_text(work)}",
        "# THE ADOPTED CANDIDATE IS NOT THE ONLY EVIDENCE\n\nSelection compared artifacts with "
        "harnesses hidden, so it says which output read best -- not which edit worked. Read the "
        "trajectories, not the verdict.",
        "# WHAT EACH EDIT DID\n\nDiff every candidate against `context/base_harness/`. One row per "
        "changed component: the edit, the observed execution difference, and a verdict from "
        "`helped`, `hurt`, `no observed effect`, `confounded`. Prefer `confounded` when several "
        "components changed at once or one rollout stands behind the difference; an invented "
        "attribution poisons every later task. Wrap the rows in `<edits>`.",
        "# THE ONE LESSON THAT TRANSFERS\n\nAt most one entry, only if the edit rows support it, in "
        "`<experience>` as lines `cue:`, `lesson:`, `evidence:`, `confidence:`. The cue is the SHAPE "
        "of situation (not this task's facts); the lesson is an applicable, checkable operation on a "
        "harness naming the component. 'be thorough' is too generic; a one-off date never fires again.",
        ANSWER_FREE,
        EVIDENCE_BOUNDARY,
    )

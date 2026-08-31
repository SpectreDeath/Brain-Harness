# Hashline Anchoring with Bounded Shift Recovery

## Context
When autonomous agents perform multi-turn file edits across large codebases, line numbers frequently shift due to preceding modifications, insertion of imports, or concurrent edits. Absolute line number edits (e.g. `replace_file_content` with static start/end lines) fail or corrupt files when lines drift.

## Distilled Learning
Implement hashline anchoring with pluggable `AnchorScheme` implementations and bounded shift recovery:
- **Whitespace-Normalized Line Hashes**: Generate short, lowercase local line hashes from normalized content (`DEFAULT_HASH_LEN = 3-4 chars`), ignoring superficial indentation variations.
- **Multi-Candidate Anchor Strategies**:
  - `ContentOnly` (Candidate A): Local line hash alone (lightweight, zero read-amplification).
  - `ChunkFingerprint` (Candidate B): Local line hash combined with fixed-size chunk fingerprints, balancing freshness with localized edit invalidation.
  - `CheckpointChain` (Candidate C): Local line hash linked to preceding checkpoints for maximum freshness detection.
- **Bounded Shift Recovery (`find_shifted`)**: When a target line has drifted, scan within a bounded search radius (`DEFAULT_SEARCH_RADIUS = 20-50 lines`). If exactly one line in the window validates against the anchor hash, automatically resolve the edit to the shifted line (`ShiftResult::Found`). If ambiguous or not found, safely reject the edit before workspace mutation.

## Triggers & Seam Choices
- **Trigger**: File editing tools (`replace_file_content`, multi-replace, AST patchers) experiencing line drift errors.
- **Seam Choice**: Integrate into the tool runtime (`harness.services.tools` or `grok_build_hashline`) as an anchor verification and recovery layer preceding filesystem writes.

# Spawn Learning: knowledge_distillation (lit-media-forge-1)

- **KI ID**: `ki-literature-media-dual-lens-isnad-distillation`
- **Domain**: `knowledge_distillation`
- **Status**: `adopted`
- **Source Spawn**: `spawn_harness-literature-media-forge_ed7fffbd` (`lit-media-forge-1`)
- **Proposal ID**: `prop_lit-media-forge-1_3b9c51ee`

## Transferable Claim
- **Cue**: when distilling non-fiction books, technical papers, or video lecture transcripts into agent skills and Knowledge Items
- **Lesson**: preserve verbatim source quotes in sources/raw/ verified by IcmVerifier.verify_quotes, apply dual-lens epistemic/procedural seam extraction, and scaffold dual-file KIs with verified isnad claims
- **Evidence**: standalone ki_scaffolder.py + media_pipeline_cli.py distill-seams ok; IcmVerifier quotes verified=1 (valid=True)

## Rationale
Prevents ungrounded paraphrase drift when converting long-form books and multimedia lectures into executable skills.

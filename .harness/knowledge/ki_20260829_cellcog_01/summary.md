# KI: Any-to-Any Sub-Agent Delegation & <SHOW_FILE> Multimodal Protocol

## Operational Summary
Local coding agents frequently encounter requests requiring generative outputs beyond code—such as 3D asset modeling (.GLB), 4K cinematic video, multi-track audio/music generation, presentation slide decks, financial spreadsheets (.XLSX), or complex PDF documents. Rather than assembling fragile multi-tool local chains (e.g. local Blender/ffmpeg scripting), the agent can delegate the task in a single API call to an any-to-any cloud sub-agent (such as CellCog).

## Protocol & Architecture Invariants

1. **`<SHOW_FILE>` Multimodal Ingestion**:
   - Reference files (PDFs, images, code files, CSVs, audio) are passed directly in prompt strings enclosed in `<SHOW_FILE>/absolute/path</SHOW_FILE>` tags.
   - The sub-agent runtime intercepts these tags, uploads the underlying files to the cloud session, and provides full multimodal grounding.
   - *Invariant*: Never wrap sensitive files (e.g. `.env`, SSH keys, credentials) in `<SHOW_FILE>` tags.

2. **Single-Request Multi-Deliverable Output**:
   - The sub-agent accepts multi-deliverable requests simultaneously (e.g. "Generate an interactive HTML dashboard, a 60-second summary video, and a PDF executive report from this sales CSV").
   - Result artifacts are returned with download URIs or local file paths.

3. **Sub-Agent Delegation Seam**:
   - Integrates into Harness via `ServiceKey[CellCogService]` or `UnifiedContextPipelineService` pre-execution hooks.

## Key References
- Source Specification: [`D:\GitHub\cloned\CellCog\skills-main\skills-main\skills\cellcog\SKILL.md`](file:///D:/GitHub/cloned/CellCog/skills-main/skills-main/skills/cellcog/SKILL.md)
- Visual Brief: [repo-reader-20260829-160000.html](file:///C:/Users/spectre/AppData/Local/Temp/repo-reader-20260829-160000.html)

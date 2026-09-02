# KI: Pre-Flight File Integrity Verification & Transparent Blob Path Translation

## Operational Summary
When AI agents invoke external multimodal or document generation services with referenced local files, referencing missing or non-existent files burns API credits on doomed remote workflows. Performing strict pre-flight existence checks and annotating transformed payload tags with `external_local_path` metadata prevents billing loss and enables transparent bi-directional path restoration.

## Protocol & Architecture Invariants

1. **Pre-Flight Fail-Early Validation (`FileProcessor.transform_outgoing`)**:
   - Outgoing prompts are scanned for `<SHOW_FILE>path</SHOW_FILE>` tags.
   - Any path matching local file conventions is checked against the filesystem (`os.path.exists(file_path)`).
   - If any referenced file does not exist, `FileUploadError` is raised immediately before issuing the HTTP request or creating a cloud chat record.

2. **Transparent Path Translation & Attribute Injection**:
   - Valid local files are uploaded to cloud blob storage (`blob_name = self._upload_file(file_path)`).
   - The tag is rewritten as `<SHOW_FILE external_local_path="{file_path}">{blob_name}</SHOW_FILE>`, ensuring the remote engine receives the valid blob key while the client retains the exact local provenance.
   - Output generation tags (`<GENERATE_FILE>`) are similarly augmented with deterministic local destination targets.

3. **Safe Download Routing & Seen Deduplication**:
   - Incoming deliverables download directly to `external_local_path` if declared by the agent, or safely to `~/.cellcog/chats/{chat_id}/` by default.
   - Attachments from already-processed messages are skipped using the per-session `seen_index` cache, minimizing network bandwidth and avoiding disk churn.

## Key References
- File Processor: [`cellcog_python-main/cellcog_python-main/cellcog/files.py`](file:///D:/GitHub/cloned/CellCog/cellcog_python-main/cellcog_python-main/cellcog/files.py#L30-L120)
- Chat Operations: [`cellcog_python-main/cellcog_python-main/cellcog/chat.py`](file:///D:/GitHub/cloned/CellCog/cellcog_python-main/cellcog_python-main/cellcog/chat.py#L45-L90)
- Visual Brief: [repo-reader-20260831-110000.html](file:///C:/Users/spectre/AppData/Local/Temp/repo-reader-20260831-110000.html)

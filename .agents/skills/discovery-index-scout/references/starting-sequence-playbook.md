# Starting Sequence Playbook: Prioritized Intelligence Discovery

This playbook defines the standardized 7-step discovery sequence for scouting open datasets, transcripts, corporate disclosures, and government archives.

---

## The 7-Step Discovery Pipeline

```
[1. Map Political & Speech Corpora] ──► [2. Broadcast Caption Search] ──► [3. Primary Legislative Records]
                                                                                   │
                                                                                   ▼
[6. Temporal Wayback Audit] ◄── [5. Academic & NLP Corpora] ◄── [4. Corporate & Financial Power]
         │
         ▼
[7. Local Source Registry Commit]
```

---

### Step 1: Map Political & Debate Datasets via PolData
- **Primary Source**: `PolData` ([github.com/erikgahner/PolData](https://github.com/erikgahner/PolData))
- **Objective**: Survey existing curated datasets on politicians, parliamentary debate transcripts, election results, and cabinet dynamics before initiating custom scraping.
- **Action**:
  - Filter `PolData` categories: `Speeches and debates`, `Politicians`, `Media`, and `Policies`.
  - Identify whether official parliamentary corpora (e.g. Hansard, Europarl, ParlSpeech) already provide standardized machine-readable extracts.
- **Expected Artifact**: Inventory of candidate datasets with license status and direct download links.

---

### Step 2: Broadcast Speech & Claim Verification via Internet Archive TV News
- **Primary Source**: `Internet Archive TV News` ([archive.org/details/tv](https://archive.org/details/tv))
- **Objective**: Query spoken statements, specific phrasing, or media framing across 4.43M+ TV news broadcasts since 2009.
- **Action**:
  - Formulate exact phrase queries with quotes: `"target claim"` or `speaker_name AND keyword`.
  - Inspect timestamped closed-caption snippets and thumbnail alignments.
  - Cross-reference with Vanderbilt TV News Archive if researching broadcasts prior to 2009.
- **Expected Artifact**: Timestamped transcript snippets, broadcast identifiers, and reference clip URLs.

---

### Step 3: Anchor Primary Legislative & Administrative Records
- **Primary Sources**:
  - `C-SPAN Video Library` ([c-span.org](https://www.c-span.org/))
  - `Congress.gov` ([congress.gov](https://www.congress.gov/))
  - `GovInfo` ([govinfo.gov](https://www.govinfo.gov/))
  - `Federal Register` ([federalregister.gov](https://www.federalregister.gov/))
- **Objective**: Establish ground-truth official documentation for bills, hearing testimonies, executive orders, and agency rules.
- **Action**:
  - Query bill numbers, hearing titles, or CFR citations through `api.congress.gov` or `govinfo.gov/api`.
  - Retrieve official witness testimonies and hearing video from C-SPAN archives.
- **Expected Artifact**: Official statute/hearing transcripts, public law numbers, and regulatory notice dates.

---

### Step 4: Map Financial Flows, Influence & Corporate Ownership
- **Primary Sources**:
  - `USAspending.gov` ([usaspending.gov](https://www.usaspending.gov/))
  - `FEC Data` ([fec.gov/data](https://www.fec.gov/data/))
  - `OpenSecrets` ([opensecrets.org](https://www.opensecrets.org/))
  - `SEC EDGAR` ([sec.gov/edgar](https://www.sec.gov/edgar/search/))
- **Objective**: Follow capital allocation, procurement awards, political campaign funding, and corporate control structures.
- **Action**:
  - Cross-reference company DUNS/UEI identifiers across USAspending contract awards and SAM.gov opportunities.
  - Inspect SEC Form 10-K (annual risks/subsidiaries), Form 4 (insider trades), and Schedule 13D (beneficial ownership).
  - Trace campaign donations and PAC affiliations using FEC individual contribution search.
- **Expected Artifact**: Entity financial dossier linking recipient awards, donor contributions, and parent company filings.

---

### Step 5: Acquire Pre-Structured Research & NLP Corpora
- **Primary Sources**:
  - `Hugging Face Datasets` ([huggingface.co/datasets](https://huggingface.co/datasets))
  - `Zenodo` ([zenodo.org](https://zenodo.org/))
  - `Harvard Dataverse` ([dataverse.harvard.edu](https://dataverse.harvard.edu/))
- **Objective**: Retrieve pre-cleaned, DOI-indexed replication corpora and audio/speech datasets.
- **Action**:
  - Delegate Hugging Face dataset loading to `/hf-datasets-engineer` using streaming mode for high-scale corpora.
  - Search Zenodo and Dataverse for replication datasets tied to peer-reviewed empirical studies.
- **Expected Artifact**: Normalized Parquet or Arrow datasets ready for downstream analytical pipelines.

---

### Step 6: Historical Temporal Audits via Wayback Machine
- **Primary Source**: `Wayback Machine` ([web.archive.org](https://web.archive.org/))
- **Objective**: Detect deleted web pages, altered organizational leadership rosters, and revised policy language.
- **Action**:
  - Query the CDX Server API (`web.archive.org/cdx/search/cdx`) for temporal snapshot timestamps of the target domain.
  - Compare historical snapshots against current active websites to identify altered text or vanished documents.
- **Expected Artifact**: Diff analysis between historical and present-day web text with archived Memento links.

---

### Step 7: Commit to Local Source Registry
- **Primary Tool**: `scripts/catalog_registry.py`
- **Objective**: Persist validated discoveries into a governed, queryable repository ledger.
- **Action**:
  - Record metadata fields: Source Name, Domain Category, Access Method (API/Bulk/Web), Update Cadence, Provenance Tier, and Export Formats.
  - Validate that all committed sources adhere to epistemic chain-of-custody standards (`/epistemic-isnad-audit`).
- **Expected Artifact**: Updated `.agents/skills/discovery-index-scout/registry.json` tracking active discovery nodes.

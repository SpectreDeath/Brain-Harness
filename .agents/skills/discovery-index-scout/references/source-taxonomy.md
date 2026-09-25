# Source Taxonomy: Open Discovery Indexes & Primary Records

This reference taxonomy catalogs the 36+ discovery repositories and primary record indexes across four functional intelligence domains.

---

## Domain 1: Transcript and Video Archives

Primary spoken, legislative, hearing, and broadcast records.

| Source | Target Domain | Access Method | Provenance Tier | Export Formats |
|---|---|---|---|---|
| **C-SPAN Video Library** | U.S. Congressional proceedings, committee hearings, campaign events, policy panels | Web search, API, program transcripts | Primary Official | JSON, VTT, MP4 |
| **Internet Archive TV News** | 4.43M+ U.S. news broadcasts since 2009 with closed-caption search | Web search, IA API | Secondary Archival | JSON, SRT, Video stream |
| **Internet Archive C-SPAN** | C-SPAN video mirrored in IA collection | IA Metadata API | Secondary Archival | JSON, Torrent, XML |
| **Vanderbilt TV News Archive** | U.S. national network news broadcasts since 1968 | Web catalog search, loan requests | Academic Archival | Citations, Loan Video |
| **American Presidency Project** | U.S. presidential speeches, executive orders, debate transcripts | Web search, static documents | Academic Archival | HTML, Plain Text |
| **Miller Center Presidential Speeches** | Curated presidential speech transcripts with audio | Web catalog, audio player | Academic Archival | MP3, HTML, Text |
| **Congress.gov** | Congressional bills, Congressional Record, hearings, committee reports | REST API (api.congress.gov), Bulk XML | Primary Official | JSON, XML, PDF |
| **GovInfo** | Official U.S. Government publications (CFR, FR, Public Laws) | GovInfo API, Bulk data service | Primary Official | JSON, XML, PDF, Mods |
| **Federal Register** | Administrative regulations, executive orders, agency notices | Federal Register REST API | Primary Official | JSON, XML, CSV |
| **Supreme Court Oral Arguments (Oyez)** | SCOTUS oral argument recordings, synchronized transcripts | Web, Oyez unofficial API | Judicial Archival | Audio, JSON, Text |
| **United Nations Digital Library** | UN resolutions, debate speeches, voting records, meeting minutes | UN Digital Library search, OAI-PMH | International Primary | MarcXML, PDF, DublinCore |
| **UK Hansard** | UK House of Commons and House of Lords debate transcripts | UK Parliament API, Hansard search | Parliamentary Official | JSON, XML, HTML |
| **European Parliament Plenary** | European Parliament debate videos and multilingual verbatim reports | Europarl open data portal, Web | Parliamentary Official | XML, PDF, Multilingual Text |

---

## Domain 2: Public Records and Power Data

Corporate disclosures, procurement contracts, campaign finance, and judicial dockets.

| Source | Target Domain | Access Method | Provenance Tier | Export Formats |
|---|---|---|---|---|
| **Data.gov** | U.S. federal open datasets catalog across 100+ agencies | CKAN API, Search catalog | Federal Catalog | JSON, CSV, RDF, GeoJSON |
| **USAspending.gov** | Federal contract awards, grants, direct loans, agency spending | USAspending REST API, Bulk downloads | Primary Official | JSON, CSV archive, TSV |
| **SAM.gov Contract Opportunities** | Federal procurement opportunities, solicitations, awards | SAM.gov Public API, Data feeds | Primary Official | JSON, CSV |
| **Federal Procurement Data System** | Legacy and current federal procurement contracting records | FPDS web search, atom feeds | Primary Official | Atom, XML, CSV |
| **SEC EDGAR** | 10-K, 10-Q, 8-K, Form 4, 13D corporate filings and ownership | SEC EDGAR REST API, Company submissions | Regulatory Primary | JSON, XML, XBRL, HTML |
| **FEC Data** | Federal election campaign contributions, PACs, disbursements | FEC REST API (api.open.fec.gov), Bulk data | Primary Official | JSON, CSV bulk |
| **OpenSecrets** | Campaign finance, lobbying disclosures, outside spending networks | OpenSecrets API, Bulk data licensing | Investigative Research | JSON, CSV, Excel |
| **Senate Lobbying Disclosure** | Official federal LDA lobbying registrations and quarterly reports | LDA REST API, Bulk XML archives | Primary Official | JSON, XML, Zip |
| **ProPublica Nonprofit Explorer** | IRS Form 990 filings, executive compensation, grants | ProPublica Nonprofit REST API | Secondary Archival | JSON, PDF (Form 990) |
| **PACER** | Federal court dockets, judicial orders, litigant filings | PACER web portal, fee-based API | Primary Official | PDF, HTML dockets |
| **CourtListener** | Searchable opinions, RECAP court dockets, oral arguments | CourtListener REST API v4 | Public Interest Archival | JSON, PDF, Audio |
| **FOIA.gov** | Federal Freedom of Information Act portal, agency annual reports | FOIA.gov API, agency routing | Administrative Official | JSON, CSV |
| **National Archives Catalog** | Digitized historical records, military records, finding aids | NARA Catalog API, Web portal | Primary Archival | JSON, XML, Scanned PDF |
| **OpenSanctions** | Global sanctions lists, PEPs, designated corporate entities | OpenSanctions FollowTheMoney API, Bulk | Public Interest Intelligence | JSON, CSV, FtM, Parquet |

---

## Domain 3: Research Datasets and Archives

Scientific, academic, NLP, and web-scale research corpora.

| Source | Target Domain | Access Method | Provenance Tier | Export Formats |
|---|---|---|---|---|
| **Hugging Face Datasets** | Machine learning corpora, speech, political NLP, interviews | `datasets` Python library, HF Hub API | Research Aggregator | Arrow, Parquet, JSON, CSV |
| **Zenodo** | DOI-backed replication packages, research snapshots, data | Zenodo REST API, OAI-PMH | Academic Repository | Tar, Zip, CSV, NetCDF |
| **Harvard Dataverse** | Policy studies, replication datasets, social science archives | Dataverse REST API, Web search | Academic Repository | Tabular, RData, CSV |
| **ICPSR** | Social science survey data, election studies, public policy | ICPSR Web download, institutional SSO | Academic Repository | SAS, SPSS, Stata, CSV |
| **OSF (Open Science Framework)** | Preregistrations, research supplements, project archives | OSF REST API v2 | Open Science Repository | Zip, CSV, Markdown |
| **Kaggle Datasets** | Public user-curated datasets, benchmark competitions | Kaggle CLI / Python API | Community / Benchmark | CSV, SQLite, Parquet, JSON |
| **Google Dataset Search** | Cross-web schema.org dataset search engine | Web search (schema.org crawl index) | Search Engine Meta | Discovery pointers |
| **Internet Archive** | Scanned books, historical audio/video, web collections | IA Python CLI (`internetarchive`), S3-like API | Archival Repository | JSON, Warc, PDF, Audio |
| **Wayback Machine** | Historical snapshots of institutional web pages | Wayback CDX Server API, Availability API | Archival Snapshot | HTML, WARC, CDX JSON |
| **Media Cloud** | Cross-platform news ecosystem analytics, media attention | Media Cloud REST API v2 | Academic Research Tool | JSON, CSV |

---

## Domain 4: GitHub Repositories and Topic Indexes

Curated starter catalogs and domain-specific dataset registries.

| Repository / Index | Key Contents | Primary Use Case |
|---|---|---|
| **[PolData](https://github.com/erikgahner/PolData)** | Curated indexes of political data, debate corpora, politicians, elections | Locating specialized parliamentary corpora and political debate datasets |
| **[Awesome Public Datasets](https://github.com/awesomedata/awesome-public-datasets)** | Topic-organized public datasets across government, NLP, economics | Broad topic-based dataset discovery across multiple scientific fields |
| **[Awesome UK Gov Datasets](https://github.com/i-dot-ai/awesome-gov-datasets)** | UK-government specific data sources and Parliament developer APIs | UK policy, Hansard development, and departmental data acquisition |
| **[HF Datasets Repository](https://github.com/huggingface/datasets)** | Core loader libraries, dataset cards, metadata schemas | Standardizing dataset ingestion and programmatic processing pipelines |
| **[Rev Speech Datasets](https://github.com/revdotcom/speech-datasets)** | Transcribed audio corpora catalog with alignment metadata | Speech-to-text, ASR benchmarking, and speaker diarization research |
| **[GigaSpeech](https://github.com/SpeechColab/GigaSpeech)** | 10,000+ hours of transcribed multi-domain English speech | Scaled audio-text alignment and acoustic model benchmarking |
| **[Topic: government-data](https://github.com/topics/government-data)** | Hundreds of open-source government data ingestion pipelines | Discovering community-built scrapers and official government APIs |
| **[Topic: public-datasets](https://github.com/topics/public-datasets)** | Community collections of open datasets | General public corpus discovery |
| **[Topic: interview-transcripts](https://github.com/topics/interview-transcripts)** | Oral history and qualitative interview transcript collections | Scouting specialized qualitative and historical dialogue corpora |

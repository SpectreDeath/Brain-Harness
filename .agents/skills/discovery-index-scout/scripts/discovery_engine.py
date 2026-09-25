# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml"]
# ///
"""
discovery_engine.py — Slotted Domain Model & Authoritative Catalog Engine for Discovery Indexes.

Unifies discovery sources across:
  1. Base Curated Catalog (46 authoritative indexes across 4 domains)
  2. Local Source Ledger (registry.json)
  3. 3-Tier Layered Configuration (extra_sources in skills.config.yaml)

Provides weighted multi-field search ranking, faceted filtering, provenance statistics,
and multiple output serialization formats (JSON, ASCII table, Markdown).
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Rule 23: UTF-8 standard streams entrypoint invariant
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


# ============================================================================
# Domain Models (Rule 12: Slotted Dataclass Architecture)
# ============================================================================

@dataclass(slots=True, frozen=True)
class DiscoverySource:
    """Immutable, slotted domain entity representing a verified discovery endpoint."""

    id: str
    name: str
    category: str
    url: str
    description: str
    access_method: str
    provenance_tier: str
    update_cadence: str = "Continuous / As Published"
    export_formats: tuple[str, ...] = field(default_factory=tuple)
    tags: tuple[str, ...] = field(default_factory=tuple)
    notes: str = ""
    added_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DiscoverySource:
        name = str(data.get("name", "Unnamed Source"))
        raw_id = data.get("id") or name.lower().replace(" ", "-").replace(".", "").replace("/", "-")
        # Rule 33: JSON / YAML null-field fallback invariant
        formats = tuple(data.get("export_formats") or [])
        tags = tuple(data.get("tags") or [])
        return cls(
            id=str(raw_id),
            name=name,
            category=str(data.get("category", "unclassified")).lower(),
            url=str(data.get("url", "")),
            description=str(data.get("description", "")),
            access_method=str(data.get("access_method", "Web / API")),
            provenance_tier=str(data.get("provenance_tier", "Unknown")),
            update_cadence=str(data.get("update_cadence", "Continuous / As Published")),
            export_formats=formats,
            tags=tags,
            notes=str(data.get("notes", "")),
            added_at=str(data.get("added_at") or datetime.now(timezone.utc).isoformat()),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "url": self.url,
            "description": self.description,
            "access_method": self.access_method,
            "provenance_tier": self.provenance_tier,
            "update_cadence": self.update_cadence,
            "export_formats": list(self.export_formats),
            "tags": list(self.tags),
            "notes": self.notes,
            "added_at": self.added_at,
        }


@dataclass(slots=True, frozen=True)
class SearchResult:
    """Slotted value object containing ranked search match and scoring breakdown."""

    source: DiscoverySource
    score: float
    matched_fields: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        data = self.source.to_dict()
        data["relevance_score"] = round(self.score, 2)
        data["matched_fields"] = list(self.matched_fields)
        return data


# ============================================================================
# Base Curated Discovery Catalog
# ============================================================================

CURATED_SOURCES_DATA: list[dict[str, Any]] = [
    # 1. Transcripts & Video Archives
    {
        "name": "C-SPAN Video Library",
        "category": "transcripts",
        "url": "https://www.c-span.org/",
        "description": "U.S. Congressional proceedings, committee hearings, campaign events, policy panels, and transcripts since 1987.",
        "access_method": "Web, API, Program Transcripts",
        "provenance_tier": "Primary Official",
        "export_formats": ["JSON", "VTT", "MP4"],
        "tags": ["congress", "hearings", "politics", "transcripts", "video"],
    },
    {
        "name": "Internet Archive TV News",
        "category": "transcripts",
        "url": "https://archive.org/details/tv",
        "description": "Searchable closed captions across 4.43M+ U.S. television news broadcasts since 2009.",
        "access_method": "Web Search, IA API",
        "provenance_tier": "Secondary Archival",
        "export_formats": ["JSON", "SRT", "Video stream"],
        "tags": ["television", "captions", "news", "broadcast", "transcripts"],
    },
    {
        "name": "Internet Archive C-SPAN Collection",
        "category": "transcripts",
        "url": "https://archive.org/details/TV-CSPAN?tab=collection",
        "description": "C-SPAN broadcast video mirrored inside the Internet Archive ecosystem.",
        "access_method": "IA Metadata API, Web",
        "provenance_tier": "Secondary Archival",
        "export_formats": ["JSON", "Torrent", "XML"],
        "tags": ["cspan", "video", "government", "archive"],
    },
    {
        "name": "Vanderbilt Television News Archive",
        "category": "transcripts",
        "url": "https://tvnews.vanderbilt.edu/",
        "description": "Comprehensive national network television evening news broadcast archive beginning in 1968.",
        "access_method": "Web Catalog, Inter-library Loan",
        "provenance_tier": "Academic Archival",
        "export_formats": ["Citations", "Loan Video"],
        "tags": ["historical", "television", "evening news", "broadcast"],
    },
    {
        "name": "American Presidency Project",
        "category": "transcripts",
        "url": "https://www.presidency.ucsb.edu/",
        "description": "Presidency documents, executive orders, debate transcripts, press conferences, and campaign statements.",
        "access_method": "Web Search, Static Archives",
        "provenance_tier": "Academic Archival",
        "export_formats": ["HTML", "Text"],
        "tags": ["president", "debates", "executive orders", "speeches"],
    },
    {
        "name": "Miller Center Presidential Speeches",
        "category": "transcripts",
        "url": "https://millercenter.org/the-presidency/presidential-speeches",
        "description": "Curated collection of historical U.S. presidential speech transcripts and audio recordings.",
        "access_method": "Web Catalog, Audio Player",
        "provenance_tier": "Academic Archival",
        "export_formats": ["MP3", "HTML", "Text"],
        "tags": ["president", "speeches", "audio", "history"],
    },
    {
        "name": "Congress.gov",
        "category": "transcripts",
        "url": "https://www.congress.gov/",
        "description": "Official federal legislative data: bills, amendments, Congressional Record, nominations, committee reports.",
        "access_method": "REST API (api.congress.gov), Bulk XML",
        "provenance_tier": "Primary Official",
        "export_formats": ["JSON", "XML", "PDF"],
        "tags": ["congress", "legislation", "bills", "congressional record"],
    },
    {
        "name": "GovInfo",
        "category": "transcripts",
        "url": "https://www.govinfo.gov/",
        "description": "Official publications from all three branches of the U.S. Government (CFR, Federal Register, Public Laws, hearings).",
        "access_method": "GovInfo API, Bulk Data Service",
        "provenance_tier": "Primary Official",
        "export_formats": ["JSON", "XML", "PDF", "MODS"],
        "tags": ["official", "gpo", "statutes", "regulations", "hearings"],
    },
    {
        "name": "Federal Register",
        "category": "transcripts",
        "url": "https://www.federalregister.gov/",
        "description": "The daily journal of the U.S. Government: proposed rules, final regulations, and presidential documents.",
        "access_method": "Federal Register REST API",
        "provenance_tier": "Primary Official",
        "export_formats": ["JSON", "XML", "CSV"],
        "tags": ["regulations", "executive orders", "rules", "agencies"],
    },
    {
        "name": "Supreme Court Oral Arguments (Oyez)",
        "category": "transcripts",
        "url": "https://www.oyez.org/",
        "description": "Audio recordings, synchronized transcripts, and case summaries for U.S. Supreme Court proceedings.",
        "access_method": "Web, Oyez API",
        "provenance_tier": "Judicial Archival",
        "export_formats": ["Audio", "JSON", "Text"],
        "tags": ["scotus", "supreme court", "oral arguments", "judicial"],
    },
    {
        "name": "United Nations Digital Library",
        "category": "transcripts",
        "url": "https://digitallibrary.un.org/",
        "description": "UN speeches, resolutions, meeting records, voting records, and institutional documents.",
        "access_method": "Search Portal, OAI-PMH",
        "provenance_tier": "International Primary",
        "export_formats": ["MarcXML", "PDF", "DublinCore"],
        "tags": ["un", "international", "resolutions", "diplomacy", "speeches"],
    },
    {
        "name": "UK Hansard",
        "category": "transcripts",
        "url": "https://hansard.parliament.uk/",
        "description": "Substantially verbatim report of debates in both the UK House of Commons and House of Lords.",
        "access_method": "UK Parliament API, Web Search",
        "provenance_tier": "Parliamentary Official",
        "export_formats": ["JSON", "XML", "HTML"],
        "tags": ["uk", "parliament", "commons", "lords", "debates", "hansard"],
    },
    {
        "name": "European Parliament Plenary",
        "category": "transcripts",
        "url": "https://www.europarl.europa.eu/plenary/en/debates-video.html",
        "description": "Debate video recordings and multilingual verbatim reports of proceedings from the European Parliament.",
        "access_method": "Europarl Open Data, Web",
        "provenance_tier": "Parliamentary Official",
        "export_formats": ["XML", "PDF", "Multilingual Text"],
        "tags": ["eu", "europe", "parliament", "plenary", "debates"],
    },

    # 2. Public Records and Power Data
    {
        "name": "Data.gov",
        "category": "public_records",
        "url": "https://data.gov/",
        "description": "U.S. Federal open-data catalog covering 200,000+ datasets across hundreds of agencies.",
        "access_method": "CKAN API, Web Search",
        "provenance_tier": "Federal Catalog",
        "export_formats": ["JSON", "CSV", "RDF", "GeoJSON"],
        "tags": ["federal", "open data", "agencies", "census", "environment"],
    },
    {
        "name": "USAspending.gov",
        "category": "public_records",
        "url": "https://www.usaspending.gov/",
        "description": "Official source for federal spending data: contracts, grants, loans, and financial awards by agency and vendor.",
        "access_method": "USAspending REST API, Bulk Archives",
        "provenance_tier": "Primary Official",
        "export_formats": ["JSON", "CSV", "TSV"],
        "tags": ["contracts", "procurement", "spending", "grants", "subsidies"],
    },
    {
        "name": "SAM.gov Contract Opportunities",
        "category": "public_records",
        "url": "https://sam.gov/content/opportunities",
        "description": "Active federal contracting solicitations, pre-solicitation notices, awards, and procurement requirements.",
        "access_method": "SAM.gov Public API, Data Feeds",
        "provenance_tier": "Primary Official",
        "export_formats": ["JSON", "CSV"],
        "tags": ["procurement", "contracts", "rfp", "solicitations", "defense"],
    },
    {
        "name": "Federal Procurement Data System (FPDS)",
        "category": "public_records",
        "url": "https://www.fpds.gov/",
        "description": "Federal contracting data system and historical procurement transactions.",
        "access_method": "FPDS Web Search, Atom Feeds",
        "provenance_tier": "Primary Official",
        "export_formats": ["Atom", "XML", "CSV"],
        "tags": ["procurement", "contracts", "vendors", "transactions"],
    },
    {
        "name": "SEC EDGAR",
        "category": "public_records",
        "url": "https://www.sec.gov/edgar/search/",
        "description": "Corporate financial filings (10-K, 10-Q, 8-K), insider transactions (Form 4), beneficial ownership, and proxy statements.",
        "access_method": "SEC EDGAR REST API, Submissions API",
        "provenance_tier": "Regulatory Primary",
        "export_formats": ["JSON", "XML", "XBRL", "HTML"],
        "tags": ["sec", "corporate", "filings", "insider trades", "10-k", "ownership"],
    },
    {
        "name": "FEC Data",
        "category": "public_records",
        "url": "https://www.fec.gov/data/",
        "description": "Federal election campaign contributions, donor disclosures, candidate receipts, committee spending, and PAC filings.",
        "access_method": "FEC REST API, Bulk Data Downloads",
        "provenance_tier": "Primary Official",
        "export_formats": ["JSON", "CSV bulk"],
        "tags": ["campaign finance", "elections", "pac", "contributions", "donors"],
    },
    {
        "name": "OpenSecrets",
        "category": "public_records",
        "url": "https://www.opensecrets.org/",
        "description": "Comprehensive investigative non-partisan database tracking federal campaign money, lobbying, and revolving-door networks.",
        "access_method": "OpenSecrets API, Bulk Licensing",
        "provenance_tier": "Investigative Research",
        "export_formats": ["JSON", "CSV", "Excel"],
        "tags": ["lobbying", "campaign finance", "influence", "dark money", "revolving door"],
    },
    {
        "name": "Senate Lobbying Disclosure (LDA)",
        "category": "public_records",
        "url": "https://lda.senate.gov/system/public/",
        "description": "Official federal lobbying registrations and quarterly expense/activity reports filed under the Lobbying Disclosure Act.",
        "access_method": "LDA REST API, Bulk XML",
        "provenance_tier": "Primary Official",
        "export_formats": ["JSON", "XML", "ZIP"],
        "tags": ["lobbying", "senate", "registrations", "influence", "clients"],
    },
    {
        "name": "ProPublica Nonprofit Explorer",
        "category": "public_records",
        "url": "https://projects.propublica.org/nonprofits/",
        "description": "Searchable database of IRS Form 990 filings for tax-exempt nonprofit organizations, executive salaries, and grant payouts.",
        "access_method": "ProPublica REST API, Form 990 PDFs",
        "provenance_tier": "Secondary Archival",
        "export_formats": ["JSON", "PDF"],
        "tags": ["nonprofits", "form 990", "irs", "charities", "compensation"],
    },
    {
        "name": "PACER",
        "category": "public_records",
        "url": "https://pacer.uscourts.gov/",
        "description": "Public Access to Court Electronic Records: official U.S. Federal appellate, district, and bankruptcy court dockets.",
        "access_method": "PACER Web Portal, Case Search API",
        "provenance_tier": "Primary Official",
        "export_formats": ["PDF", "HTML dockets"],
        "tags": ["courts", "litigation", "dockets", "federal court", "bankruptcy"],
    },
    {
        "name": "CourtListener",
        "category": "public_records",
        "url": "https://www.courtlistener.com/",
        "description": "Searchable database of millions of court opinions, RECAP federal dockets, judicial financial disclosures, and oral arguments.",
        "access_method": "CourtListener REST API v4",
        "provenance_tier": "Public Interest Archival",
        "export_formats": ["JSON", "PDF", "Audio"],
        "tags": ["courts", "opinions", "recap", "judges", "dockets", "citations"],
    },
    {
        "name": "FOIA.gov",
        "category": "public_records",
        "url": "https://www.foia.gov/",
        "description": "Central federal Freedom of Information Act portal, agency submission routing, and annual agency compliance reports.",
        "access_method": "FOIA.gov API, Agency Routing",
        "provenance_tier": "Administrative Official",
        "export_formats": ["JSON", "CSV"],
        "tags": ["foia", "public records", "transparency", "agency requests"],
    },
    {
        "name": "National Archives Catalog",
        "category": "public_records",
        "url": "https://catalog.archives.gov/",
        "description": "Official catalog of digitized U.S. Government historical documents, photos, audio, and archival finding aids.",
        "access_method": "NARA Catalog API, Web Portal",
        "provenance_tier": "Primary Archival",
        "export_formats": ["JSON", "XML", "Scanned PDF"],
        "tags": ["nara", "national archives", "historical", "military", "records"],
    },
    {
        "name": "OpenSanctions",
        "category": "public_records",
        "url": "https://www.opensanctions.org/",
        "description": "Structured open database on international sanctions lists, politically exposed persons (PEPs), and corporate ownership networks.",
        "access_method": "FollowTheMoney API, Bulk Parquet",
        "provenance_tier": "Public Interest Intelligence",
        "export_formats": ["JSON", "CSV", "FtM", "Parquet"],
        "tags": ["sanctions", "pep", "illicit finance", "security", "watchlists"],
    },

    # 3. Research Datasets and Archives
    {
        "name": "Hugging Face Datasets",
        "category": "research_corpora",
        "url": "https://huggingface.co/datasets",
        "description": "Repository of machine learning datasets, parliamentary NLP corpora, speech benchmarks, and interview archives.",
        "access_method": "datasets Python library, Hub API",
        "provenance_tier": "Research Aggregator",
        "export_formats": ["Arrow", "Parquet", "JSON", "CSV"],
        "tags": ["nlp", "ml", "speech", "benchmarks", "corpora", "transcripts"],
    },
    {
        "name": "Zenodo",
        "category": "research_corpora",
        "url": "https://zenodo.org/",
        "description": "CERN/OpenAIRE research archive providing permanent DOIs for replication packages, datasets, software, and papers.",
        "access_method": "Zenodo REST API, OAI-PMH",
        "provenance_tier": "Academic Repository",
        "export_formats": ["TAR", "ZIP", "CSV", "NetCDF"],
        "tags": ["doi", "replication", "academic", "open science", "datasets"],
    },
    {
        "name": "Harvard Dataverse",
        "category": "research_corpora",
        "url": "https://dataverse.harvard.edu/",
        "description": "Open social science, political science, and public policy research repository for replication data and surveys.",
        "access_method": "Dataverse REST API, Web Download",
        "provenance_tier": "Academic Repository",
        "export_formats": ["Tabular", "RData", "CSV"],
        "tags": ["social science", "policy", "political science", "replication"],
    },
    {
        "name": "ICPSR",
        "category": "research_corpora",
        "url": "https://www.icpsr.umich.edu/",
        "description": "Inter-university Consortium for Political and Social Research: major archive of behavioral and social science surveys.",
        "access_method": "Web Portal, Institutional Access",
        "provenance_tier": "Academic Repository",
        "export_formats": ["SAS", "SPSS", "Stata", "CSV"],
        "tags": ["surveys", "voting", "demographics", "elections", "social science"],
    },
    {
        "name": "OSF (Open Science Framework)",
        "category": "research_corpora",
        "url": "https://osf.io/",
        "description": "Platform for scientific project management, preregistrations, research supplements, and public data deposits.",
        "access_method": "OSF REST API v2",
        "provenance_tier": "Open Science Repository",
        "export_formats": ["ZIP", "CSV", "Markdown"],
        "tags": ["open science", "preregistration", "reproducibility", "experiments"],
    },
    {
        "name": "Kaggle Datasets",
        "category": "research_corpora",
        "url": "https://www.kaggle.com/datasets",
        "description": "Community repository of public tabular, text, and multimodal datasets with accompanying notebooks.",
        "access_method": "Kaggle CLI / Python API",
        "provenance_tier": "Community / Benchmark",
        "export_formats": ["CSV", "SQLite", "Parquet", "JSON"],
        "tags": ["community", "tabular", "competitions", "machine learning"],
    },
    {
        "name": "Google Dataset Search",
        "category": "research_corpora",
        "url": "https://datasetsearch.research.google.com/",
        "description": "Cross-web search engine indexing datasets using schema.org markup across thousands of academic and civic repositories.",
        "access_method": "Web Search Index",
        "provenance_tier": "Search Engine Meta",
        "export_formats": ["Discovery pointers"],
        "tags": ["search engine", "metadata", "schema.org", "discovery"],
    },
    {
        "name": "Internet Archive",
        "category": "research_corpora",
        "url": "https://archive.org/",
        "description": "Digital library containing millions of digitized books, historical audio recordings, videos, and web collection archives.",
        "access_method": "IA Python CLI, S3-like API",
        "provenance_tier": "Archival Repository",
        "export_formats": ["JSON", "WARC", "PDF", "Audio"],
        "tags": ["archive", "books", "multimedia", "web collections", "history"],
    },
    {
        "name": "Wayback Machine",
        "category": "research_corpora",
        "url": "https://web.archive.org/",
        "description": "Historical snapshots of the World Wide Web; indispensable for temporal audits of deleted or altered web content.",
        "access_method": "CDX Server API, Availability API",
        "provenance_tier": "Archival Snapshot",
        "export_formats": ["HTML", "WARC", "CDX JSON"],
        "tags": ["wayback", "web archive", "temporal audit", "history", "snapshots"],
    },
    {
        "name": "Media Cloud",
        "category": "research_corpora",
        "url": "https://mediacloud.org/",
        "description": "Open source media analysis platform for tracking news attention, source ecosystems, and public narrative framing.",
        "access_method": "Media Cloud REST API v2",
        "provenance_tier": "Academic Research Tool",
        "export_formats": ["JSON", "CSV"],
        "tags": ["news analysis", "media attention", "narratives", "journalism"],
    },

    # 4. GitHub Repositories and Topic Indexes
    {
        "name": "PolData",
        "category": "github_indexes",
        "url": "https://github.com/erikgahner/PolData",
        "description": "Curated index of political datasets: politicians, parties, cabinets, elections, debates, and speech corpora across countries.",
        "access_method": "Git Clone, GitHub Markdown",
        "provenance_tier": "Curated Index",
        "export_formats": ["Markdown Catalog", "Direct Links"],
        "tags": ["poldata", "politics", "debates", "parliamentary", "speech corpora"],
    },
    {
        "name": "Awesome Public Datasets",
        "category": "github_indexes",
        "url": "https://github.com/awesomedata/awesome-public-datasets",
        "description": "Topic-organized catalog of high-quality public data sources across economics, NLP, politics, and science.",
        "access_method": "Git Clone, Markdown Catalog",
        "provenance_tier": "Curated Index",
        "export_formats": ["Markdown", "Direct Links"],
        "tags": ["awesome list", "public datasets", "open data", "multi-domain"],
    },
    {
        "name": "Awesome UK Government Datasets",
        "category": "github_indexes",
        "url": "https://github.com/i-dot-ai/awesome-gov-datasets",
        "description": "Curated UK government data sources, Hansard APIs, and Parliament developer resources.",
        "access_method": "Git Clone, Markdown Catalog",
        "provenance_tier": "Curated Index",
        "export_formats": ["Markdown", "Direct Links"],
        "tags": ["uk", "government", "hansard", "developer apis"],
    },
    {
        "name": "Hugging Face Datasets Source Repository",
        "category": "github_indexes",
        "url": "https://github.com/huggingface/datasets",
        "description": "Source code, loaders, documentation, and dataset cards powering the Hugging Face dataset ecosystem.",
        "access_method": "Git Clone, Python Package",
        "provenance_tier": "Engineering Tooling",
        "export_formats": ["Python code", "Documentation"],
        "tags": ["huggingface", "loaders", "documentation", "arrow", "parquet"],
    },
    {
        "name": "Rev Speech Datasets",
        "category": "github_indexes",
        "url": "https://github.com/revdotcom/speech-datasets",
        "description": "Curated index of speech and audio datasets with transcript annotations for ASR and diarization benchmarking.",
        "access_method": "Git Clone, Markdown Catalog",
        "provenance_tier": "Curated Index",
        "export_formats": ["Markdown", "Corpus links"],
        "tags": ["speech", "asr", "audio", "transcripts", "diarization"],
    },
    {
        "name": "GigaSpeech",
        "category": "github_indexes",
        "url": "https://github.com/SpeechColab/GigaSpeech",
        "description": "10,000+ hours multi-domain transcribed English speech corpus and processing toolkit for ASR models.",
        "access_method": "Git Clone, Corpus Download",
        "provenance_tier": "Academic Benchmark",
        "export_formats": ["WAV", "JSON", "Text"],
        "tags": ["speech", "audio", "asr", "transcribed speech", "benchmark"],
    },
    {
        "name": "GitHub Topic: government-data",
        "category": "github_indexes",
        "url": "https://github.com/topics/government-data",
        "description": "GitHub topic directory indexing hundreds of open-source government data scrapers, pipelines, and tools.",
        "access_method": "GitHub Topic Search",
        "provenance_tier": "Community Topic Index",
        "export_formats": ["Repository links"],
        "tags": ["github topic", "government data", "pipelines", "scrapers"],
    },
    {
        "name": "GitHub Topic: public-datasets",
        "category": "github_indexes",
        "url": "https://github.com/topics/public-datasets",
        "description": "GitHub topic directory for open and public dataset collections and data exploration tools.",
        "access_method": "GitHub Topic Search",
        "provenance_tier": "Community Topic Index",
        "export_formats": ["Repository links"],
        "tags": ["github topic", "public datasets", "open data"],
    },
    {
        "name": "GitHub Topic: interview-transcripts",
        "category": "github_indexes",
        "url": "https://github.com/topics/interview-transcripts",
        "description": "GitHub topic directory for qualitative interview transcript repositories and oral history projects.",
        "access_method": "GitHub Topic Search",
        "provenance_tier": "Community Topic Index",
        "export_formats": ["Repository links"],
        "tags": ["github topic", "interviews", "transcripts", "oral history"],
    },
]


# ============================================================================
# Authoritative Catalog Engine
# ============================================================================

class DiscoveryCatalogEngine:
    """
    Authoritative domain engine coordinating:
      - Multi-source aggregation (Base curated + registry.json + 3-tier config extra_sources)
      - Weighted relevance search ranking & multi-field faceted filtering
      - Idempotent registry persistence
      - Output serialization (JSON, ASCII Table, Markdown)
    """

    def __init__(
        self,
        registry_path: Path | str | None = None,
        config_path: Path | str | None = None,
    ) -> None:
        self.skill_dir = Path(__file__).resolve().parent.parent
        self.registry_path = Path(registry_path) if registry_path else self.skill_dir / "registry.json"
        self.config_path = Path(config_path) if config_path else self.skill_dir / "config.default.yaml"
        self._sources: dict[str, DiscoverySource] = {}
        self.reload()

    def reload(self) -> None:
        """Reload and merge all sources across the three tiers."""
        self._sources = {}

        # 1. Load base curated sources
        for item in CURATED_SOURCES_DATA:
            src = DiscoverySource.from_dict(item)
            self._sources[src.id] = src

        # 2. Merge local registry.json if present
        if self.registry_path.exists():
            try:
                raw = json.loads(self.registry_path.read_text(encoding="utf-8"))
                items = raw.get("sources") or []
                for item in items:
                    raw_id = item.get("id") or item.get("name", "").lower().replace(" ", "-").replace(".", "").replace("/", "-")
                    existing = self._sources.get(raw_id)
                    if existing:
                        merged_data = existing.to_dict()
                        for k, v in item.items():
                            if v:
                                merged_data[k] = v
                        src = DiscoverySource.from_dict(merged_data)
                    else:
                        src = DiscoverySource.from_dict(item)
                    self._sources[src.id] = src
            except Exception as err:
                sys.stderr.write(f"Warning: Failed to load registry from {self.registry_path}: {err}\n")

        # 3. Merge 3-tier config extra_sources
        self._load_config_overrides()

    def _load_config_overrides(self) -> None:
        """Load additive sources from 3-tier config."""
        candidate_paths: list[Path] = []
        if self.config_path.exists():
            candidate_paths.append(self.config_path)

        # Look for project overrides
        cur = self.skill_dir.resolve()
        while cur != cur.parent:
            cand = cur / ".agents" / "skills.config.yaml"
            if cand.exists():
                candidate_paths.append(cand)
                break
            cur = cur.parent

        for cp in candidate_paths:
            try:
                content = cp.read_text(encoding="utf-8")
                # Parse YAML or fallback
                extra_sources = self._extract_yaml_extra_sources(content)
                for item in extra_sources:
                    src = DiscoverySource.from_dict(item)
                    self._sources[src.id] = src
            except Exception:
                pass

    @staticmethod
    def _extract_yaml_extra_sources(content: str) -> list[dict[str, Any]]:
        try:
            import yaml
            parsed = yaml.safe_load(content)
            if isinstance(parsed, dict):
                # Check root or skill-named block
                if "extra_sources" in parsed and isinstance(parsed["extra_sources"], list):
                    return parsed["extra_sources"]
                block = parsed.get("discovery-index-scout") or parsed.get("discovery_index_scout") or {}
                if isinstance(block, dict) and "extra_sources" in block and isinstance(block["extra_sources"], list):
                    return block["extra_sources"]
        except Exception:
            pass
        return []

    def get_source(self, source_id: str) -> DiscoverySource | None:
        """Lookup source by exact ID."""
        return self._sources.get(source_id)

    def list_all_sources(self) -> list[DiscoverySource]:
        """Return all aggregated discovery sources."""
        return list(self._sources.values())

    def search(
        self,
        query: str | None = None,
        category: str | None = None,
        tag: str | None = None,
        provenance_tier: str | None = None,
        export_format: str | None = None,
        limit: int = 20,
    ) -> list[SearchResult]:
        """
        Execute weighted multi-field relevance search with faceted filtering.
        Scoring weights:
          - Exact title match: +10.0
          - Token match in title: +5.0
          - Exact tag match: +4.0
          - Token in tag: +2.5
          - Token in description: +2.0
          - Token in access method: +1.0
        """
        scored_results: list[SearchResult] = []
        tokens = [t.lower() for t in re.split(r"\s+", query.strip())] if query and query.strip() else []

        for src in self._sources.values():
            # Faceted filters (hard gates)
            if category and src.category.lower() != category.lower():
                continue
            if tag and not any(tag.lower() in t.lower() for t in src.tags):
                continue
            if provenance_tier and provenance_tier.lower() not in src.provenance_tier.lower():
                continue
            if export_format and not any(export_format.lower() in ef.lower() for ef in src.export_formats):
                continue

            # If no free-text query, score by base provenance tier
            if not tokens:
                base_score = 1.0
                if "primary" in src.provenance_tier.lower():
                    base_score += 0.5
                scored_results.append(SearchResult(source=src, score=base_score, matched_fields=("category",)))
                continue

            # Calculate weighted multi-field relevance
            score = 0.0
            matched_fields: list[str] = []
            name_lower = src.name.lower()
            desc_lower = src.description.lower()
            tags_lower = [t.lower() for t in src.tags]

            # Check exact full phrase in title
            full_query = " ".join(tokens)
            if full_query in name_lower:
                score += 10.0
                matched_fields.append("title_exact")

            for token in tokens:
                if token in name_lower:
                    score += 5.0
                    matched_fields.append("title")
                for t in tags_lower:
                    if token == t:
                        score += 4.0
                        matched_fields.append("tag_exact")
                    elif token in t:
                        score += 2.5
                        matched_fields.append("tag")
                if token in desc_lower:
                    score += 2.0
                    matched_fields.append("description")
                if token in src.access_method.lower():
                    score += 1.0
                    matched_fields.append("access_method")

            if score > 0.0:
                scored_results.append(
                    SearchResult(
                        source=src,
                        score=score,
                        matched_fields=tuple(dict.fromkeys(matched_fields)),
                    )
                )

        # Sort descending by score, then alphabetical by name
        scored_results.sort(key=lambda r: (-r.score, r.source.name))
        return scored_results[:limit]

    def register_source(self, source_data: dict[str, Any] | DiscoverySource, persist: bool = True) -> DiscoverySource:
        """Register or update a source and optionally persist to registry.json."""
        if isinstance(source_data, DiscoverySource):
            src = source_data
        else:
            src = DiscoverySource.from_dict(source_data)

        self._sources[src.id] = src

        if persist:
            self.save_registry()
        return src

    def save_registry(self, target_path: Path | None = None) -> None:
        """Persist registered sources into registry.json."""
        out_path = target_path or self.registry_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": "1.0.0",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "total_count": len(self._sources),
            "sources": [s.to_dict() for s in self._sources.values()],
        }
        out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def get_stats(self) -> dict[str, Any]:
        """Compute faceted distribution statistics."""
        by_category: dict[str, int] = {}
        by_provenance: dict[str, int] = {}
        for s in self._sources.values():
            by_category[s.category] = by_category.get(s.category, 0) + 1
            by_provenance[s.provenance_tier] = by_provenance.get(s.provenance_tier, 0) + 1
        return {
            "total_sources": len(self._sources),
            "by_category": by_category,
            "by_provenance": by_provenance,
        }

    # --- Formatting utilities ---

    @staticmethod
    def format_json(results: list[SearchResult] | list[DiscoverySource]) -> str:
        """Format items as pretty-printed JSON."""
        data = [r.to_dict() for r in results]
        return json.dumps({"total": len(data), "results": data}, indent=2)

    @staticmethod
    def format_table(results: list[SearchResult] | list[DiscoverySource]) -> str:
        """Format items as formatted ASCII table."""
        if not results:
            return "No discovery sources matched the specified criteria."

        lines: list[str] = [
            f"{'SOURCE NAME':<32} | {'CATEGORY':<16} | {'PROVENANCE':<20} | URL",
            f"{'-'*32}-|-{'-'*16}-|-{'-'*20}-|-{'-'*30}",
        ]
        for r in results:
            src = r.source if isinstance(r, SearchResult) else r
            lines.append(f"{src.name:<32} | {src.category:<16} | {src.provenance_tier:<20} | {src.url}")
        return "\n".join(lines)

    @staticmethod
    def format_markdown(results: list[SearchResult] | list[DiscoverySource]) -> str:
        """Format items as Markdown table."""
        if not results:
            return "_No discovery sources matched the specified criteria._"

        lines: list[str] = [
            "| Source | Category | Provenance Tier | Access Method | URL |",
            "|---|---|---|---|---|",
        ]
        for r in results:
            src = r.source if isinstance(r, SearchResult) else r
            lines.append(f"| [{src.name}]({src.url}) | `{src.category}` | {src.provenance_tier} | {src.access_method} | {src.url} |")
        return "\n".join(lines)

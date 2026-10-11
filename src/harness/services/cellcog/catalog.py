"""Static capability catalog harvested from CellCog sub-agent architecture."""

from __future__ import annotations

from harness.services.cellcog.models import CellCogCapabilityItem

CELLCOG_CATALOG: tuple[CellCogCapabilityItem, ...] = (
    # Research & Analysis
    CellCogCapabilityItem("deep-research-cellcog", "Research & Analysis", "Deep multi-source research with citation synthesis (#1 on DeepResearch Bench)", "team", "flash"),
    CellCogCapabilityItem("stock-analysis-cellcog", "Research & Analysis", "Financial fundamentals, DCF valuation, balance sheet analysis", "team", "core"),
    CellCogCapabilityItem("crypto-research-cellcog", "Research & Analysis", "On-chain tokenomics, protocol architecture, liquidity depth", "team", "core"),
    CellCogCapabilityItem("data-analysis-cellcog", "Research & Analysis", "Statistical regressions, anomaly detection, CSV exploratory data analysis", "agent", "max"),
    CellCogCapabilityItem("news-briefing-cellcog", "Research & Analysis", "Curated real-time news intelligence briefings and geopolitical digests", "team", "flash"),

    # Video & Cinema
    CellCogCapabilityItem("video-generation-cellcog", "Video & Cinema", "Generative video production with temporal consistency and lip-sync", "agent", "max"),
    CellCogCapabilityItem("cinematic-video-cellcog", "Video & Cinema", "4K cinematic trailers, scene transitions, shot compositions", "agent", "max"),
    CellCogCapabilityItem("instagram-reels-tiktok-cellcog", "Video & Cinema", "9:16 viral short-form video generation with dynamic subtitles", "agent", "core"),
    CellCogCapabilityItem("youtube-video-cellcog", "Video & Cinema", "Long-form YouTube video generation with chapter sequencing", "agent", "max"),
    CellCogCapabilityItem("seedance-video-generation-cellcog", "Video & Cinema", "Dance and motion choreographic video generation", "agent", "core"),

    # Images & Design
    CellCogCapabilityItem("image-generation-cellcog", "Images & Design", "High-fidelity text-to-image and image-to-image synthesis", "creative", "core"),
    CellCogCapabilityItem("logo-brand-identity-cellcog", "Images & Design", "Vector-style branding, typography guidelines, iconography kits", "creative", "core"),
    CellCogCapabilityItem("meme-generator-cellcog", "Images & Design", "Context-aware viral meme design and trending image formats", "creative", "core"),
    CellCogCapabilityItem("nano-banana-image-cellcog", "Images & Design", "Reference-grounded multi-angle product photography", "creative", "core"),
    CellCogCapabilityItem("3d-model-generation-cellcog", "Images & Design", "Production-ready .GLB and .OBJ 3D assets from text or sketches", "agent", "max"),
    CellCogCapabilityItem("gif-generator-cellcog", "Images & Design", "Optimized animated GIF asset generation", "creative", "core"),
    CellCogCapabilityItem("sticker-generator-cellcog", "Images & Design", "Die-cut transparent sticker packs and emoji sets", "creative", "core"),

    # Audio & Music
    CellCogCapabilityItem("audio-generation-cellcog", "Audio & Music", "Voice synthesis, sound effect generation, stem isolation", "agent", "core"),
    CellCogCapabilityItem("music-generation-cellcog", "Audio & Music", "Full-length instrumental and vocal musical compositions across genres", "agent", "max"),
    CellCogCapabilityItem("podcast-generation-cellcog", "Audio & Music", "Multi-host interactive audio podcast synthesis with show notes", "agent", "max"),

    # Avatars & Personas
    CellCogCapabilityItem("avatar-creation-cellcog", "Avatars & Personas", "Hyper-realistic speaking avatar synthesis and facial rigging", "agent", "max"),

    # Documents & Slides
    CellCogCapabilityItem("pdf-document-generation-cellcog", "Documents & Slides", "Publication-ready formatted PDF reports with tables and charts", "agent", "core"),
    CellCogCapabilityItem("presentation-slides-cellcog", "Documents & Slides", "High-impact 16:9 executive presentation slide decks", "creative", "core"),
    CellCogCapabilityItem("excel-spreadsheet-cellcog", "Documents & Slides", "Multi-tab .XLSX spreadsheets with financial formulas and macros", "agent", "core"),
    CellCogCapabilityItem("resume-cover-letter-cellcog", "Documents & Slides", "ATS-optimized executive resume and tailored cover letters", "creative", "core"),
    CellCogCapabilityItem("legal-documents-cellcog", "Documents & Slides", "NDAs, MSAs, terms of service, and compliance contract drafting", "agent", "max"),

    # Apps & Prototypes
    CellCogCapabilityItem("dashboard-web-app-cellcog", "Apps & Prototypes", "Interactive standalone HTML5/Tailwind executive dashboards", "creative", "max"),
    CellCogCapabilityItem("game-asset-generation-cellcog", "Apps & Prototypes", "2D/3D sprites, isometric tilesets, and game engine assets", "agent", "max"),
    CellCogCapabilityItem("ui-prototype-wireframe-cellcog", "Apps & Prototypes", "High-fidelity UI mockups and clickable interactive prototypes", "creative", "max"),
    CellCogCapabilityItem("diagram-flowchart-cellcog", "Apps & Prototypes", "Architecture schematics, sequence diagrams, and flowcharts", "agent", "core"),

    # Creative
    CellCogCapabilityItem("comic-manga-generator-cellcog", "Creative", "Multi-panel comic strips, manga pages, and storyboards", "creative", "max"),
    CellCogCapabilityItem("creative-writing-cellcog", "Creative", "Worldbuilding lore, character bibles, and narrative scripts", "creative", "core"),
    CellCogCapabilityItem("tutoring-education-cellcog", "Creative", "Interactive Socratic curricula, lesson plans, and quiz banks", "agent", "core"),
    CellCogCapabilityItem("travel-planning-cellcog", "Creative", "Day-by-day travel itineraries with maps and venue bookings", "agent", "core"),

    # Development
    CellCogCapabilityItem("coding-agent-cellcog", "Development", "Autonomous multi-file software engineering and debugging", "agent", "max"),
    CellCogCapabilityItem("pair-programming-cellcog", "Development", "Interactive real-time code review, refactoring, and AST inspection", "agent", "max"),
    CellCogCapabilityItem("project-management-cellcog", "Development", "Gantt timeline generation, sprint task decomposition, PRD drafting", "agent", "core"),
    CellCogCapabilityItem("brainstorming-strategy-cellcog", "Development", "First-principles strategic ideation and market entry frameworks", "agent", "core"),
)

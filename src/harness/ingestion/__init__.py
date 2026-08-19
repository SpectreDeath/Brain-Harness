"""Ingestion — GitHub repository to plugin conversion pipeline."""

from .converter import ConversionError, ConvertedPlugin, RepoConverter
from .fetcher import DEFAULT_PLUGIN_DIR, FetchError, RepoFetcher
from .inspector import InspectionError, RepoInspector
from .pipeline import PluginIngestionEngine, PluginIngestionPipeline

__all__ = [
    "DEFAULT_PLUGIN_DIR",
    "ConversionError",
    "ConvertedPlugin",
    "FetchError",
    "InspectionError",
    "PluginIngestionEngine",
    "PluginIngestionPipeline",
    "RepoConverter",
    "RepoFetcher",
    "RepoInspector",
]

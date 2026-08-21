"""Ingestion — GitHub repository and multi-source to plugin conversion pipeline."""

from .converter import ConversionError, ConvertedPlugin, RepoConverter
from .fetcher import DEFAULT_PLUGIN_DIR, FetchError, RepoFetcher
from .inspector import InspectionError, RepoInspector
from .pipeline import PluginIngestionEngine, PluginIngestionPipeline
from .resolvers import (
    GitHubSourceResolver,
    LocalDirectorySourceResolver,
    OpenAPISourceResolver,
    PyPISourceResolver,
    ResolvedSource,
    SourceResolver,
    UniversalSourceRegistry,
)

__all__ = [
    "DEFAULT_PLUGIN_DIR",
    "ConversionError",
    "ConvertedPlugin",
    "FetchError",
    "GitHubSourceResolver",
    "InspectionError",
    "LocalDirectorySourceResolver",
    "OpenAPISourceResolver",
    "PluginIngestionEngine",
    "PluginIngestionPipeline",
    "PyPISourceResolver",
    "RepoConverter",
    "RepoFetcher",
    "RepoInspector",
    "ResolvedSource",
    "SourceResolver",
    "UniversalSourceRegistry",
]

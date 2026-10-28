"""Ingestion — GitHub repository and multi-source to plugin conversion pipeline."""

from .converter import ConversionError, ConvertedPlugin, RepoConverter
from .fetcher import DEFAULT_PLUGIN_DIR, FetchError, RepoFetcher
from .inspector import InspectionError, RepoInspector
from .monorepo import detect_monorepo_subprojects, partition_monorepo
from .pipeline import PluginIngestionEngine, PluginIngestionPipeline
from .pypi_converter import PyPIConverter, PyPIFetchError
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
    "PyPIConverter",
    "PyPIFetchError",
    "PyPISourceResolver",
    "RepoConverter",
    "RepoFetcher",
    "RepoInspector",
    "ResolvedSource",
    "SourceResolver",
    "UniversalSourceRegistry",
    "detect_monorepo_subprojects",
    "partition_monorepo",
]

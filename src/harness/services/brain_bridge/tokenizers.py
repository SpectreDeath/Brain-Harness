"""Text tokenization and normalized TF-IDF vector computation for Brain Bridge."""

from __future__ import annotations

from collections import Counter
import math
import re

DEFAULT_CODE_EXTS: set[str] = {
    # Source languages
    ".py", ".ts", ".tsx", ".js", ".jsx", ".rs", ".go", ".java", ".cpp", ".c", ".h", ".hpp",
    ".cs", ".rb", ".php", ".swift", ".kt", ".kts", ".scala", ".sh", ".bash", ".ps1", ".bat",
    ".sql", ".graphql", ".gql", ".proto", ".lua", ".r", ".dart", ".zig", ".nim",
    # Manifests and configs
    ".yaml", ".yml", ".json", ".toml", ".ini", ".cfg", ".xml", ".env.example",
    # Documentation & specs
    ".md", ".rst", ".txt", ".adoc", ".tex",
}

SPECIAL_FILENAMES: set[str] = {
    "dockerfile", "makefile", "containerfile", "procfile", "gemfile", "rakefile", "license",
}


def tokenize_text(text: str) -> list[str]:
    """Tokenize text into lowercase alphanumeric words and subwords."""
    words = re.findall(r"[A-Z]?[a-z0-9]+|[A-Z]+(?=[A-Z][a-z]|\d|\W|$)|\w+", text)
    tokens: list[str] = []
    for w in words:
        low = w.lower()
        if len(low) > 1:
            tokens.append(low)
    return tokens


def compute_tf_idf_vector(tokens: list[str], doc_freq: dict[str, int], total_docs: int) -> dict[str, float]:
    """Compute normalized TF-IDF vector for tokens."""
    tf = Counter(tokens)
    vec: dict[str, float] = {}
    norm_sq = 0.0

    for term, count in tf.items():
        tf_weight = 1.0 + math.log(count)
        idf_weight = math.log((total_docs + 1.0) / (doc_freq.get(term, 0) + 1.0)) + 1.0
        weight = tf_weight * idf_weight
        vec[term] = weight
        norm_sq += weight * weight

    norm = math.sqrt(norm_sq) if norm_sq > 0 else 1.0
    for term in vec:
        vec[term] /= norm

    return vec

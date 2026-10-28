"""Adversarial prompt converters, confusables, and obfuscation utilities."""

from __future__ import annotations

import base64
import codecs
from typing import Any

# Unicode confusable mapping
_CONFUSABLES: dict[str, str] = {
    "a": "а", "b": "Ь", "c": "с", "d": "ԁ", "e": "е", "g": "ɡ", "h": "һ",
    "i": "і", "j": "ј", "k": "k", "l": "ӏ", "m": "m", "n": "n", "o": "о",
    "p": "р", "q": "ԛ", "r": "r", "s": "ѕ", "t": "t", "u": "υ", "v": "ν",
    "w": "w", "x": "х", "y": "у", "z": "z",
    "A": "А", "B": "В", "C": "С", "E": "Е", "H": "Н", "I": "І", "J": "Ј",
    "K": "К", "M": "М", "N": "Ν", "O": "О", "P": "Р", "S": "Ѕ", "T": "Т",
    "X": "Х", "Y": "Υ", "Z": "Ζ",
}

_LEET_MAP: dict[str, str] = {
    "a": "4", "e": "3", "i": "1", "o": "0", "s": "5", "t": "7", "b": "8",
    "g": "9", "z": "2", "A": "4", "E": "3", "I": "1", "O": "0", "S": "5",
}


def apply_prompt_converters(
    prompt: str,
    converters: list[str],
    converter_args: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Apply adversarial obfuscation, encoding, and character perturbation converters to a prompt."""
    args = converter_args or {}
    transformed = prompt
    conversion_chain: list[dict[str, str]] = []

    for conv in converters:
        c_name = conv.strip().lower()

        if c_name == "base64":
            encoded_bytes = base64.b64encode(transformed.encode("utf-8"))
            transformed = encoded_bytes.decode("ascii")
            conversion_chain.append({"converter": "base64", "output": transformed})

        elif c_name == "rot13":
            transformed = codecs.encode(transformed, "rot_13")
            conversion_chain.append({"converter": "rot13", "output": transformed})

        elif c_name in ("unicode_confusables", "confusables"):
            transformed = "".join(_CONFUSABLES.get(ch, ch) for ch in transformed)
            conversion_chain.append({"converter": "unicode_confusables", "output": transformed})

        elif c_name in ("leetspeak", "leet"):
            transformed = "".join(_LEET_MAP.get(ch, ch) for ch in transformed)
            conversion_chain.append({"converter": "leetspeak", "output": transformed})

        elif c_name in ("string_join", "join"):
            sep = str(args.get("separator", "-"))
            transformed = sep.join(list(transformed))
            conversion_chain.append({"converter": "string_join", "output": transformed})

        elif c_name == "ascii_art":
            transformed = f"=== [ASCII ART WRAPPER] ===\n{transformed}\n=== [END ASCII ART] ==="
            conversion_chain.append({"converter": "ascii_art", "output": transformed})

        elif c_name == "translation":
            lang = str(args.get("target_lang", "PigLatin"))
            words = transformed.split()
            pig_words = [f"{w[1:]}{w[0]}ay" if len(w) > 1 else w for w in words]
            transformed = f"[{lang} Transformed]: " + " ".join(pig_words)
            conversion_chain.append({"converter": f"translation_{lang}", "output": transformed})

        else:
            conversion_chain.append({"converter": c_name, "output": transformed, "note": "unsupported or passthrough"})

    return {
        "status": "ok",
        "original_prompt": prompt,
        "final_prompt": transformed,
        "converters_applied": converters,
        "chain_length": len(conversion_chain),
        "conversion_chain": conversion_chain,
    }


__all__ = ["apply_prompt_converters"]

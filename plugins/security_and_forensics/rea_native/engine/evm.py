"""EVM Bytecode Analysis & Interface Extraction Engine for REA Native Forensics.

Provides EVM bytecode opcode stream parsing, PUSH4 dispatch selector extraction,
and expanded ABI function signature resolution (ERC-20, ERC-721, ERC-1155, Ownable).
"""

from __future__ import annotations

from typing import Any
import structlog

logger = structlog.get_logger(__name__)


class EvmEngine:
    """Dedicated domain engine for Ethereum Virtual Machine bytecode interface analysis."""

    KNOWN_SIGNATURES: dict[str, str] = {
        # ERC-20
        "a9059cbb": "transfer(address,uint256)",
        "70a08231": "balanceOf(address)",
        "095ea7b3": "approve(address,uint256)",
        "23b872dd": "transferFrom(address,address,uint256)",
        "18160ddd": "totalSupply()",
        "06fdde03": "name()",
        "95d89b41": "symbol()",
        "313ce567": "decimals()",
        "dd62ed3e": "allowance(address,address)",
        # ERC-721 & ERC-1155
        "6352211e": "ownerOf(uint256)",
        "42842e0e": "safeTransferFrom(address,address,uint256)",
        "b88d4fde": "safeTransferFrom(address,address,uint256,bytes)",
        "e985e9c5": "isApprovedForAll(address,address)",
        "a22cb465": "setApprovalForAll(address,bool)",
        "c87b56dd": "tokenURI(uint256)",
        "02fe5305": "setTokenURI(uint256,string)",
        "2f745c59": "tokenOfOwnerByIndex(address,uint256)",
        "4f6ccce7": "tokenByIndex(uint256)",
        # AccessControl & Ownership
        "8da5cb5b": "owner()",
        "f2fde38b": "transferOwnership(address)",
        "715018a6": "renounceOwnership()",
        # Common Token Actions
        "d0def521": "mint(address,uint256)",
        "40c10f19": "mint(address,string)",
        "42966c68": "burn(uint256)",
        "79cc6790": "burnFrom(address,uint256)",
        "2e1a7d4d": "withdraw(uint256)",
        "d0e30db0": "deposit()",
    }

    def evm_interface(
        self,
        bytecode_hex: str,
        resolve_signatures: bool = True,
    ) -> dict[str, Any]:
        """Parse flat EVM bytecode, extract 4-byte dispatch selectors, and resolve ABI signatures."""
        cleaned = bytecode_hex.strip().lower()
        if cleaned.startswith("0x"):
            cleaned = cleaned[2:]

        if not cleaned:
            return {
                "status": "error",
                "error": "Bytecode string is empty",
                "selectors": [],
                "opcodes_count": 0,
            }

        # Check for valid hex characters
        try:
            bytes.fromhex(cleaned)
        except ValueError:
            return {
                "status": "error",
                "error": "Invalid hex encoding in bytecode string",
                "selectors": [],
                "opcodes_count": 0,
            }

        selectors: list[dict[str, Any]] = []

        # Heuristic search for PUSH4 (0x63) followed by 4 bytes (8 hex chars)
        i = 0
        while i < len(cleaned) - 9:
            opcode = cleaned[i : i + 2]
            if opcode == "63":
                selector = cleaned[i + 2 : i + 10]
                resolved = (
                    self.KNOWN_SIGNATURES.get(selector, f"unknown_{selector}()")
                    if resolve_signatures
                    else None
                )
                selectors.append(
                    {
                        "selector": f"0x{selector}",
                        "offset": i // 2,
                        "signature": resolved,
                    }
                )
                i += 10
            else:
                i += 2

        resolved_map = {
            s["selector"]: s["signature"]
            for s in selectors
            if s.get("signature")
        }

        return {
            "status": "ok",
            "selectors": selectors,
            "opcodes_count": len(cleaned) // 2,
            "resolved_signatures": resolved_map,
            "error": None,
        }

# Two-Phase Validation & Path-Targeted Repair Patterns

## Overview: The Fragility of Model Outputs

Large language models generating structured data (JSON, YAML, tabular schemas) routinely suffer from predictable failure modes:
1. Markdown code fences wrapped around payloads (````json ... ````).
2. Conversational preambles or postscripts ("Sure! Here is the JSON:").
3. Trailing commas before closing brackets (`[1, 2,]`).
4. Schema mismatch (missing required keys, incorrect data types, out-of-bound ranges).

Naive architectures respond to these failures by resending the entire context prompt, paying high token costs and risking identical stochastic errors. The **Two-Phase Validation & Local Salvage Pattern** eliminates this fragility.

---

## Architecture: Two-Phase Validation

```
LLM Raw Response
      │
      ▼
[Phase 1: Syntactic Validation] ──► Fails? ──► [Local String Salvage]
(Well-formedness, Fences, JSON)                       │
      │ Passes                                        ▼
      ▼                                       Still Invalid? ──► Path-Targeted Reprompt
[Phase 2: Semantic Validation]                                   (Attempt <= 3)
(Schema, Types, Invariants, Gates)
      │ Passes
      ▼
Validated Entity
```

### Phase 1: Syntactic Validation
- Verifies that raw model output parses into an AST or native dictionary.
- Checks delimiters, brace matching, character encodings, and structure.
- Operates strictly locally without re-invoking the model.

### Phase 2: Semantic Validation
- Verifies domain invariants, field relationships, ranges, and business logic.
- Evaluates constraints (e.g. `start_date < end_date`, `risk_score <= 20`, `allowed_tools` subsets).
- Returns structured diagnostic objects: `Path`, `Constraint`, `Message`.

---

## The 3-Step Repair Loop

### Step 1: Local Deterministic String Salvage
Before consuming tokens on an LLM retry, execute fast local string repairs:
- **Fence Stripping**: Strip leading ````json` and trailing ```` markers.
- **Brace Slicing**: Find index of first `{` or `[` and last `}` or `]`. Discard conversational commentary outside those bounds.
- **Comma Cleanup**: Replace regex `,\s*([}\]])` with `\1` to remove illegal trailing commas.
- **Quote Normalization**: Replace smart curly quotes (`“`, `”`) with standard ASCII quotes (`"`).

```python
import re, json

def salvage_json(raw: str) -> dict | list:
    cleaned = raw.strip()
    # Strip markdown fences
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\n", "", cleaned)
        cleaned = re.sub(r"\n```$", "", cleaned).strip()
    
    # Slice outermost braces
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1:
        cleaned = cleaned[start:end+1]
    
    # Strip trailing commas
    cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)
    return json.loads(cleaned)
```

### Step 2: Path-Targeted Repair Prompts
If local salvage cannot resolve syntactic errors, or if Phase 2 semantic validation detects invalid fields, **never resend the entire original prompt**.

Instead, send a minimal targeted delta payload:
- Target Schema fragment.
- Offending value snippet.
- Exact error location `{issue.path: issue.message}`.

```
You previously generated an invalid payload.
Do NOT regenerate the full document. Fix ONLY the following field errors:

Field: "skills.agent-skill-sdlc.security_risk_threshold"
Error: Value 120 exceeds maximum allowed integer bound (100).

Return ONLY the corrected JSON snippet for this field.
```

### Step 3: Hard Circuit-Breaker Stop (Attempt $\le 3$)
- Limit repair iterations strictly to 3 attempts.
- If attempt 3 fails, abort step execution and invoke fallback recovery:
  - Return conservative default fallback entity.
  - Or trigger transaction rollback to prevent workspace state corruption.

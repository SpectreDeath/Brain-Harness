# Diátaxis Taxonomy Architecture Guide

The Diátaxis documentation framework (formulated by Daniele Procida) organizes technical documentation along two core axes:
1. **Practical Steps vs. Theoretical Understanding**
2. **Learning vs. Working Information**

This creates four non-overlapping quadrants with strict behavioral boundaries.

---

## The 4 Quadrants Matrix

| Dimension | Learning-Oriented | Working-Oriented |
|---|---|---|
| **Practical Steps** | **Tutorials** (Lesson for newcomers)<br>- Guided journey<br>- Inspires confidence<br>- Fixed outcome | **How-To Guides** (Recipe for practitioners)<br>- Goal-directed series of steps<br>- Solves a real-world problem<br>- Adaptable |
| **Theoretical Knowledge** | **Explanation** (Understanding & context)<br>- Discursive and reflective<br>- Explains *why* and design trade-offs<br>- Illuminates connections | **Reference** (Authoritative lookup)<br>- Information-oriented<br>- Accurate and neutral<br>- Complete specifications |

---

## 1. Tutorials (Learning-Oriented)
- **Goal**: Teach newcomers basic orientation and build early momentum.
- **Tone**: Patient, prescriptive, encouraging, step-by-step.
- **Rule**: Never offer alternative pathways; provide exactly one working path.
- **Anti-Pattern**: Introducing deep conceptual theory or exhaustive parameter lists in a tutorial.

## 2. How-To Guides (Problem-Oriented)
- **Goal**: Help competent users accomplish a specific real-world task.
- **Tone**: Practical, outcome-focused, efficient.
- **Structure**:
  1. Goal statement ("How to authenticate via OAuth 2.0 PKCE").
  2. Prerequisites (CLI tools, API keys, installed libraries).
  3. Step-by-step procedure with copy-pasteable snippets.
  4. Verification step ("Verify successful token issuance").
- **Anti-Pattern**: Explaining underlying theory instead of focusing on the task.

## 3. Reference (Information-Oriented)
- **Goal**: Provide authoritative technical descriptions of the machinery.
- **Tone**: Neutral, rigorous, exhaustive, unambiguous.
- **Content**: Endpoint anatomy, CLI flags, JSON schemas, return types, status codes.
- **Rule**: Mirrors the code structure exactly (e.g., OpenAPI schemas).
- **Anti-Pattern**: Adding narrative instructions or onboarding steps.

## 4. Explanation (Understanding-Oriented)
- **Goal**: Clarify architectural context, rationale, and design trade-offs.
- **Tone**: Discursive, illuminating, higher-level.
- **Content**: Why gRPC was chosen over REST, event-driven consistency guarantees, security threat models.
- **Anti-Pattern**: Documenting step-by-step commands in an architectural explanation.

---

## Anti-Conflation Checklist
- [ ] Every page states its target quadrant in the introductory metadata.
- [ ] Tutorials do not list reference tables.
- [ ] Reference pages do not embed narrative tutorial walkthroughs.
- [ ] Explanation documents do not contain installation recipes.

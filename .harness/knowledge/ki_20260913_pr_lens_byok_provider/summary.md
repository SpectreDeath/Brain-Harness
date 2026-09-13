# Normalized BYOK Multi-LLM Provider Architecture

## Context
Code review tooling hardcoded to a single model provider suffers from vendor lock-in, rate limiting, and enterprise credential friction. Different developer environments have distinct available keys (GEMINI_API_KEY vs OPENAI_API_KEY vs internal proxy endpoints).

## Distilled Learning
PR Lens decouples analysis prompts from model runtimes through a strict provider seam:
- **Unified Interface**: All providers implement a uniform contract: `generateGraph(prompt: string, options: ProviderOptions): Promise<string>`.
- **Environment Detection**: Runtime automatically selects the active provider based on environment variables (`GEMINI_API_KEY`, `OPENAI_API_KEY`) or CLI flags (`--provider gemini`).
- **Structured Schema Enforcement**: Uses native provider structured output capabilities (e.g. Gemini JSON mode, OpenAI response_format) while falling back to robust JSON markdown fence extraction.

## Triggers & Seam Choices
- **Trigger**: CLI model dispatch, automated CI workflows, and autonomous agent LLM routing.
- **Seam Choice**: Integration into `harness.services.llm` and plugin service adapters.

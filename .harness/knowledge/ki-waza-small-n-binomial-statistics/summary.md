# Waza: Small-N Wilson CI, Unbiased Pass^k, Seeded Bootstrap & Hake Gain

**Upstream Repository**: https://github.com/microsoft/waza @ `cc6afc5e`

## Core Mechanics
- **Wilson Score Interval (`WilsonCI`)**: Stays inside `[0, 1]` and maintains coverage at the `3-10` trials typical of agent evals where normal approximations and raw bootstraps break down.
- **Unbiased `PassHatK` (`PassHatK(successes, trials, k)`)**: Computes `C(successes, k) / C(trials, k)` sequentially via `prod_{i=0..k-1} (successes - i) / (trials - i)`, avoiding binomial exponentiation bias.
- **Seeded Percentile Bootstrap (`BootstrapCIWithSeed`)**: Runs 10,000 resamples with optional deterministic seed; `IsSignificant` holds only when the difference interval excludes `0` (`Lower > 0 || Upper < 0`).
- **Hake Normalized Gain (`NormalizedGain`)**: `(post - pre) / (1 - pre)` normalizes ceiling effects (`0.9 -> 0.95` vs `0.1 -> 0.15`).

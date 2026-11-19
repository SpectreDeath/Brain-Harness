# Google Research `norml`: No-Reward Meta-Learning with Learned Advantage Functions & Offsets

## 1. Context & Provenance

- **Upstream Repository**: `https://github.com/google-research/google-research` (`norml/` subproject, 24 files)
- **Snapshot Reference**: `google-research-master` (archive snapshot, non-git)
- **Publication**: *NoRML: No-Reward Meta Learning* (Yang et al., 2019; `https://arxiv.org/abs/1903.01063`)
- **Primary Verified Sources**:
  - `norml/README.md` (`L1-L63`)
  - `norml/maml_rl.py` (`L39-L390`, sha256 `02d3ae9a964e2478266b4b48e2f092cd6dcfee00763f09b82858b6e60bfc7896`)
  - `norml/config_maml.py` (`L41-L90`, sha256 `553085108eb7f4b8548e9081425c65b48c372a6283ac16084a5286f2c139e826`)

---

## 2. Core Problem & Architectural Thesis

Standard meta-reinforcement learning (`MAML-RL`) requires scalar task rewards during fast test-time inner-loop adaptation. Under real-world dynamics shifts (e.g., rotated controls or shifted sensor biases), reward signals may be unavailable at test time. `norml` solves this by meta-learning (1) an inner-loop **advantage estimator** driven purely by observed transition tuples `(s_{t+1}, s_t, a_t)` and (2) a learned inner **weight offset** `e` plus per-parameter inner learning rates `a`, trained end-to-end with external-reward PPO in the outer loop.

---

## 3. Verified Implementation Invariants

### A. Inner No-Reward Adaptation & Clipped Outer PPO (`maml_rl.py` `L128-L390`)
- `_create_weights` (`L128-L154`) optionally allocates per-parameter inner learning rates (`learn_inner_lr_tensor`), parameter adaptation offsets `e_weights` (`learn_offset`), and inner advantage network weights `adv_weights` (`learn_advantage_function_inner`).
- `_construct_inner_networks` (`L234-L390`):
  - When `learn_advantage_function_inner` is active, concatenates `[network_next_input_train, network_input_train, train_actions]` as input to the learned advantage estimator rather than reading test-time rewards (`L297-L303`), computing inner updates `test_weights[k] = theta - a * grad (+ e)`.
  - Guards PPO inner clipping with `self.ppo and (not self.learn_advantage_function_inner)` (`L307`) and optimizes outer meta-loss (`test_weights`) via clipped surrogate PPO objectives (`L383-L390`).
  - `_update_value_function` (`L196-L233`) fits per-task regularized linear regression baselines over cubic state + normalized timestep features (`L226`).

### B. Ablation-Ready `{ENV}_{ALG}` Configuration Registry (`config_maml.py` `L41-L90`)
- Defines named experiment dictionaries (e.g., `MOVE_POINT_ROTATE_MAML`) parameterizing `task_generator`, `task_env_modifiers`, `learn_offset`, `learn_inner_lr_tensor`, and `ppo_clip_value=0.2` to isolate `DR`, `MAML`, `MAML_OFFSET`, `MAML_LAF`, and `NORML`.

---

## 4. Applicability to Brain Harness & Anti-Patterns

- **Harness Seam Targets**: Self-adaptation loops and policy optimization workers can separate fast unsupervised inner-loop correction signals (transition consistency / learned critic feedback without sparse external labels) from slower verified outer-loop objective updates.
- **Anti-Patterns**:
  - **Do not apply inner PPO clipping simultaneously with learned inner advantage optimization** — `maml_rl.py` (`L307`) disables inner PPO when `learn_advantage_function_inner` is true so meta-gradients propagate cleanly through the inner step.
  - **Do not omit per-task regularized value baselines** (`eye * 1e-5` ridge term at `L227`) when estimating policy returns across short rollouts.

# Google Tunix Post-Training Plugin

JAX-based LLM post-training, GRPO, and math rewards.


---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `tunix_inspect_config` | `(pipeline_type, model_name, learning_rate, batch_size)` | Generate and validate GRPO, PPO, or PEFT post-training configurations for JAX execution |
| `tunix_launch_grpo` | `(config_dict, dry_run, num_steps)` | Prepare and simulate or launch a GRPO (Group Relative Policy Optimization) post-training step |
| `tunix_launch_peft` | `(config_dict, lora_rank, dry_run)` | Launch or simulate parameter-efficient fine-tuning (PEFT/LoRA) using Tunix SFT trainer |
| `tunix_compute_math_reward` | `(completion, ground_truth, format_check)` | Compute mathematical reasoning and formatting reward scores on candidate model completions |

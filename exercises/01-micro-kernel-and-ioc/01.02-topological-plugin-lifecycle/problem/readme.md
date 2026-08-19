# Problem: Manage Plugin Lifecycle with Dependencies

## Objective

Create two interconnected plugins where `PluginB` requires a service provided by `PluginA`, and verify that `PluginLifecycle` enables them in the correct dependency order.

## Tasks

1. Define `PluginA` providing `SERVICE_A_KEY`.
2. Define `PluginB` requiring `SERVICE_A_KEY`.
3. Load and enable both plugins using `PluginLifecycle`.

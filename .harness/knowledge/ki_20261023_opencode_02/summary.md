# Dual-Runtime Plugin Interface Architecture (Effect & Promise)

## Context
High-concurrency micro-kernel architectures often rely on advanced effect runtimes (such as Effect-TS or Trio/AnyIO) for structured concurrency, fibers, and bounded cancellation. However, requiring third-party plugin authors to master complex monadic types severely limits ecosystem adoption.

## Distilled Learning
Implement a dual-runtime adapter architecture in the plugin subsystem:
- **Internal Kernel Seam (`plugin/effect`)**: Uses native Effect types with full fiber management, interruption guarantees, and typed error channels.
- **External Public Facade (`plugin/promise`)**: Translates effects into standard asynchronous Promises (`async/await`) and standard event emitters via an adapter layer (`packages/plugin/src/promise/adapter.ts`).
- Plugin authors can write plain async JavaScript/TypeScript functions, while the runtime automatically lifts them into cooperative kernel fibers with proper lifecycle hooks.

## Triggers & Seam Choices
- **Trigger**: Exposing advanced asynchronous runtime capabilities to untrusted or community-authored plugins.
- **Seam Choice**: Implement an adapter wrapper at the IoC / plugin host boundary that seamlessly handles bidirectional conversion between Promises and kernel effect fibers.

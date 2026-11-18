# gVisor User-Space Kernel Isolation: Sentry, Gofer & Immutable Sandbox Specs

## Provenance
- **Upstream Repository**: `https://github.com/google/gvisor` (`b6c312b83f13d6150a3386bd1f7c170ba2342cc4`)
- **Surfaced By**: Ontology-Spider portfolio scan (`unlearned_tested` top-level gap)

## Architectural Insights
1. **No Syscall Passthrough (`g3doc/architecture_guide/security.md#L100-L220`)**:
   Instead of wrapping the host kernel with `seccomp-bpf` alone, gVisor re-implements the Linux System API inside a pure-Go user-space Sentry (`CGo` forbidden, `unsafe` restricted to `*unsafe.go`) and applies `seccomp-bpf` as a second layer shrinking Sentry's own host attack surface.
2. **Brokered Filesystem via Gofer & FD Donation (`runsc/sandbox/sandbox.go#L148-L295`)**:
   `Sandbox` is documented as strictly immutable per container spec. Filesystem mounts are mediated by separate Gofer processes connected over sockets (`IOFiles`, `GoferMountConfs`) and explicit file descriptor donation (`DonateAndClose`) inside an empty mount namespace.
3. **Platform Substrate Seam (`pkg/sentry/platform/platform.go#L35-L70`)**:
   `Platform` abstracts address-space mapping, preemption detection, and context execution cleanly away from the host virtualization or interception mechanism.

## Harness Relevance
- Models clean FD/pipe capability brokering for Brain Harness's untrusted subprocess sandbox isolation (`AGENTS.md` Rules 5, 14, 15).

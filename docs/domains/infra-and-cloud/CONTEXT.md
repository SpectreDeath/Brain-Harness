# Infrastructure & Cloud Context

The Infrastructure & Cloud context governs container management, Kubernetes manifest validation, Infrastructure-as-Code (IaC) linting, and automated delivery pipelines.

## Language

**Container Manager**:
A runtime interface that manages isolated OCI container lifecycles, volume mounts, and network port bindings.
_Avoid_: Docker wrapper, sandbox host

**Manifest Validator**:
A static schema checker that asserts structural compliance and resource limit specifications for Kubernetes YAML objects.
_Avoid_: K8s linter, YAML checker

**Infrastructure Spec**:
A declarative Terraform HCL or OpenTofu definition specifying cloud resources, security groups, and ingress policies.
_Avoid_: IaC script, deployment file

**Pipeline**:
A directed workflow definition specifying build, test, and container packaging stages for CI/CD automation.
_Avoid_: Action script, build job

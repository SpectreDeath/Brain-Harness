# Michael Feathers' Seam Catalog for AI Agents

In *Working Effectively with Legacy Code*, Michael Feathers defines a **seam** as:
> *A place where you can alter behavior in your program without editing in that place.*

Every seam comes with an **enabling point**: the place where you choose which behavior is executed.

---

## The Four Primary Seam Archetypes

### 1. Object / Parameter Injection Seam
The cleanest and most maintainable seam in object-oriented and functional systems.

* **Pattern**: When a function instantiates or directly accesses a concrete dependency (e.g. database client, email service), extract the dependency to a parameter or constructor argument with a default value.
* **Legacy Code**:
  ```python
  def activate_customer(customer_id: str) -> None:
      db = DatabaseConnection() # Tightly coupled!
      db.update("customers", customer_id, {"active": True})
  ```
* **Seam Introduced**:
  ```python
  def activate_customer(customer_id: str, db=None) -> None:
      db = db or DatabaseConnection() # Parameter seam!
      db.update("customers", customer_id, {"active": True})
  ```
* **Enabling Point**: Passing a mock or in-memory repository during test invocation.
* **Positive Invariant**: Keep the seam mechanical. Do **not** redesign the customer activation rules while adding the parameter.

---

### 2. Interface / Adapter Seam
Extract a lightweight protocol or interface defining only the exact methods the legacy code consumes.

* **Pattern**:
  ```python
  class CustomerStore(Protocol):
      def find_by_id(self, customer_id: str) -> dict | None: ...
      def save(self, customer: dict) -> None: ...
  ```
* **Enabling Point**: Injecting an in-memory dictionary-backed store during characterization testing.

---

### 3. Preprocessor / Module Patch Seam
Used when language features or runtime environments allow monkeypatching or dependency interception without altering call sites.

* **Pattern**:
  ```python
  monkeypatch.setattr("legacy_module.requests.post", mock_post)
  ```
* **Enabling Point**: The test fixture module setup.
* **Usage**: Ideal for legacy code with extensive top-level imports that are impractical to parameterize immediately.

---

### 4. Link / Import Aliasing Seam
Altering the module resolution order or configuration path so that legacy imports resolve to test doubles.

---

## Architectural Rules for Seam Introduction
1. **Mechanical Minimality**: The seam change must be trivial and self-evident. Never refactor surrounding business logic during seam creation.
2. **Backward Compatibility**: Preserve existing function signatures by utilizing optional parameters or default arguments.
3. **Characterization Immediate Execution**: As soon as the seam is introduced, execute the characterization suite to guarantee zero regression before refactoring begins.

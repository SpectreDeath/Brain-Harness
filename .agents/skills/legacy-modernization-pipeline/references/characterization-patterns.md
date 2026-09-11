# Characterization Testing & Seam Extraction Patterns

## 1. The Golden Master Test Pattern
A characterization test locks down existing observable behavior of a software system without making assumptions about intended correctness.

```python
def test_golden_master_pricing_calculation():
    # Arrange legacy black box
    calculator = LegacyPricingEngine()
    
    # Act over input matrix
    results = [
        calculator.calculate(units, tier, discount)
        for units in [0, 1, 10, 50, 100]
        for tier in ["standard", "premium", "enterprise"]
        for discount in [0.0, 0.15, 0.5]
    ]
    
    # Assert against golden snapshot
    assert results == EXPECTED_GOLDEN_SNAPSHOT
```

## 2. Seam Injection Protocols
According to Michael Feathers (*Working Effectively with Legacy Code*), a seam is an inflection point where behavior can be varied without modifying source code directly.

### Object Seams via IoC & Typed Keys
```python
# Legacy tightly coupled instantiation:
# db = PostgresConnection("postgres://...")

# Modernized Seam Injection:
db = context.require(DATABASE_SERVICE_KEY)
```

## 3. Synthetic Mutation Testing
To prove characterization tests will detect regression:
1. Introduce a deliberate off-by-one or operator mutation (`>` to `>=`).
2. Run characterization test suite.
3. Confirm that the test fails immediately.
4. Revert mutation before refactoring begins.

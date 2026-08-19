# Problem: Verify Logic Rules with Em-Cubed Bridge

## Objective

Use the `EmCubedPlugin` to verify a transitive relationship rule (e.g. `ancestor(X, Y) :- parent(X, Y)`).

## Tasks

1. Initialize `EmCubedPlugin`.
2. Add facts: `parent(alice, bob)`, `parent(bob, charlie)`.
3. Add rule: `ancestor(X, Y) :- parent(X, Y)` and `ancestor(X, Z) :- parent(X, Y), ancestor(Y, Z)`.
4. Query `ancestor(alice, charlie)` and verify truth.

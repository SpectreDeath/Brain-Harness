# Denormal IEEE-754 FP32 Simulated Addition Bypassing CUDA Core ALU Contention

## Context
Extracted during automated repository triad ingestion from [`DeepSelect`](D:\GitHub\cloned\Google\DeepSelect) (DeepSeek Sparse Attention TopK kernel).

## Distilled Learning
For non-negative integers x, y <= 2^22, the bitwise integer addition result x + y is identical to treating their 32-bit patterns as IEEE-754 denormal floats and executing a floating-point addition: __float_as_uint(__uint_as_float(x) + __uint_as_float(y)). DeepSelect uses this to replace integer additions, bypassing ALU resource contention with bitwise/comparison instructions and achieving 2x throughput over integer multiply-add.

## Mental Models
- **Denormal Float Equivalence**:  In IEEE-754 single precision, numbers with zero exponent are denormal numbers where the mantissa acts as a linear integer representation without an implicit leading 1.
- **ALU Pipeline Diversification**:  CUDA SM integer units are heavily shared between address calculation, comparison, and bitwise operations. Floating-point units have dedicated pipelines and higher throughput on modern architectures.

## Decision Heuristics
- For index offsets and histogram accumulations bounded by 2^22 (approx 4.19M), substitute integer addition with denormal FP32 addition to exploit unused FP ALU throughput.
- Assert MAX_VOCAB_SIZE <= 1u << 23 at compile time to guarantee strict absence of exponent overflow into normalized float space.

## Anti-Pattern Defenses
- **Over-Relying on Integer MAD**:  Using integer mad (multiply-add) instructions when int ALU is saturated, which delivers only half the instruction throughput of FP32 addition.
- **Unbounded FP32 Integer Emulation**:  Applying denormal float addition when values exceed 2^22, which causes exponent bits to set and corrupts the integer bit pattern.

## Triggers & Seam Choices
- **Trigger**: High-throughput TopK kernel design, DeepSeek sparse attention inference, vocabulary sampling, or GPU ALU contention optimization.
- **Seam Choice**: Integration via Brain Harness IoC `ServiceContext` and typed `ServiceKey[DeepSelectTopkProtocol]`.

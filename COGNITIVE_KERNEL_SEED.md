# Cognitive Kernel Seed: Foundation Layer Implementation

🧠 **Status**: Seeded and Ready for Distributed Cognition

This directory contains the complete implementation of the Cognitive Kernel seed for the OpenCog Central cognitive architecture. The seed forms the atomic substrate of distributed cognition with recursive tensor operations across four degrees of freedom.

## Overview

The Cognitive Kernel Seed implements:

- ✅ **Rigorous Build & Test Scripts** for Scheme/C++/C/Rust components
- ✅ **Parameterized GGML Kernel Adaptation** with tensor shape [modules, build-steps, tests]
- ✅ **Hardware Matrix** for multi-architecture support (x86_64, ARM64, RISC-V)
- ✅ **Artifact Generation** for downstream CI/CD jobs
- ✅ **Tensor DOF Documentation** for each module
- ✅ **Recursive Implementation** validation (not mocks)

## Foundation Components

### 1. CogUtil - Core Utilities
- **Location**: `orc-dv/cogutil`
- **Languages**: C++, Scheme
- **Tensor DOF**: Spatial (3D), Temporal (1D), Semantic (256D), Logical (64D)
- **Features**: Recursive data structures, tensor-aware memory management

### 2. Moses - Evolutionary Optimization
- **Location**: `orc-ai/moses`
- **Languages**: C++, Scheme
- **Tensor DOF**: Population space (3D), Generation sequences (1D), Program semantics (256D), Logic structure (64D)
- **Features**: Recursive genetic programming, tensor-based fitness evaluation

### 3. External-Tools - Integration Layer
- **Location**: `orc-dv/external-tools`
- **Languages**: Python, Java, Scheme, Multiple
- **Tensor DOF**: Coordinate mapping (3D), Temporal sync (1D), Semantic translation (256D), Logic conversion (64D)
- **Features**: Recursive format conversion, cross-system tensor exchange

### 4. Rust Crates - High-Performance Operations
- **Location**: `orc-dv/rust_crates`
- **Languages**: Rust
- **Tensor DOF**: SIMD spatial (3D), Lock-free temporal (1D), Memory-efficient semantic (256D), Type-safe logical (64D)
- **Features**: Zero-cost abstractions, compile-time verification, async recursion

## Tensor Degrees of Freedom

The Cognitive Kernel operates across four primary tensor degrees of freedom:

| Dimension | Size | Purpose | Example |
|-----------|------|---------|---------|
| **Spatial** | 3D | Geometric reasoning and spatial relationships | `[x, y, z]` coordinates |
| **Temporal** | 1D | Time-series processing and sequences | `[t]` time points |
| **Semantic** | 256D | High-dimensional concept embeddings | `[s1...s256]` concept vector |
| **Logical** | 64D | Inference chains and reasoning states | `[l1...l64]` logic state |

## Quick Start

### Running the Complete Seed

```bash
./cognitive-kernel-seed.sh
```

This will:
1. Build all foundation layer components
2. Run comprehensive test suite (unit, integration, recursive)
3. Generate tensor DOF documentation
4. Consolidate build artifacts
5. Generate hardware matrix report
6. Create usage examples

### Building Individual Components

```bash
# Set component to build
export TENSOR_MODULES="cogutil"
export BUILD_TYPE="Debug"

# Run foundation build
./foundation-build.sh
```

### Running Specific Tests

```bash
# Run only recursive implementation tests
export TENSOR_TESTS="recursive"
./foundation-test.sh
```

### Hardware-Specific Optimization

```bash
# Detect and optimize for current hardware
ARCH=$(uname -m)

if [ "$ARCH" = "x86_64" ]; then
    export TENSOR_ACCEL="avx2,avx512"
    export GGML_BACKEND="cpu,gpu"
elif [ "$ARCH" = "aarch64" ]; then
    export TENSOR_ACCEL="neon"
    export GGML_BACKEND="cpu"
fi

./foundation-build.sh
```

## Generated Artifacts

After running `cognitive-kernel-seed.sh`, the following artifacts are generated in `ci_artifacts/foundation-layer/`:

```
ci_artifacts/foundation-layer/
├── cognitive_kernel_seed_report.json       # Overall seed status
├── COGNITIVE_KERNEL_TENSOR_DOF.md          # Comprehensive tensor documentation
├── hardware_matrix.json                     # Hardware capabilities report
├── foundation_build_report.json             # Build results
├── foundation_test_summary.json             # Test results
├── test-reports/                            # Detailed test reports
│   ├── unit_test_report.json
│   ├── integration_test_report.json
│   └── recursive_test_report.json
└── examples/                                # Usage examples
    ├── build_component.sh
    ├── test_recursive.sh
    └── optimize_hardware.sh
```

## Build Parameterization

The build system uses tensor shape parameterization:

```
TENSOR_SHAPE = [modules, build-steps, tests]
```

**Configuration Variables**:

```bash
# Modules to build (comma-separated)
TENSOR_MODULES="cogutil,moses,external-tools,rust_crates"

# Build steps (comma-separated)
TENSOR_BUILD_STEPS="configure,compile,link,test"

# Test types (comma-separated)
TENSOR_TESTS="unit,integration,recursive"

# GGML configuration
GGML_SUPPORT="ON"
GGML_BACKEND="cpu,gpu"
TENSOR_PRECISION="fp32,fp16"

# Multi-architecture
ENABLE_MULTIARCH="ON"
TARGET_ARCHS="x86_64,arm64,riscv64"
```

## Hardware Matrix Support

The cognitive kernel automatically detects and optimizes for:

- **x86_64**: AVX2, AVX512 vectorized operations
- **ARM64**: NEON vectorized operations
- **RISC-V**: Scalar operations with loop optimization
- **GPU**: CUDA/OpenCL parallel tensor kernels (when available)

## Recursive Implementation

All cognitive operations implement genuine recursion:

### 1. Recursive Decomposition
Breaking complex tensors into manageable sub-tensors for hierarchical processing.

### 2. Recursive Composition
Building complex cognitive structures from simpler tensor components.

### 3. Recursive Transformation
Applying transformations recursively through nested cognitive operations.

### 4. Recursive Validation
Multi-level validation ensuring tensor integrity at all recursion depths.

**Critical**: No mock implementations. All recursion is genuinely implemented and tested.

## Integration with OpenCog Central

The Cognitive Kernel serves as the foundation for:

- **AtomSpace**: Hypergraph knowledge representation (orc-as)
- **PLN**: Probabilistic logic reasoning (orc-ai/pln)
- **URE**: Unified rule engine (orc-ai/ure)
- **Learning**: Pattern mining and structure learning (orc-ai/learn)
- **Language**: Natural language processing (orc-nl)
- **Robotics**: Embodied cognition (orc-ro)

## GGML Kernel Adaptation

The foundation layer integrates with GGML for optimized tensor operations:

**Supported Formats**:
- `fp32`: Full precision floating point
- `fp16`: Half precision for memory efficiency
- `int8`: Integer quantization for speed

**Block Formats**:
- `q4_0`, `q4_1`: 4-bit quantization
- `q5_0`, `q5_1`: 5-bit quantization
- `q8_0`: 8-bit quantization

**Backend Selection**:
- **CPU Backend**: Optimized for general-purpose computing
- **GPU Backend**: CUDA/OpenCL for parallel operations
- **Hybrid**: Dynamic selection based on tensor size and type

## Downstream Consumption

The generated artifacts are ready for downstream CI/CD jobs:

```cmake
# In your CMakeLists.txt
FIND_PACKAGE(Foundation REQUIRED)
TARGET_LINK_LIBRARIES(your_target Foundation::Core)
```

Or using pkg-config:

```bash
gcc $(pkg-config --cflags --libs foundation) your_code.c
```

## Distributed Cognition

The Cognitive Kernel forms the atomic substrate for distributed cognition:

- **First-Order Tensors**: Each module is a prime candidate for tensor representation
- **Agentic Catalog**: Foundation components ready for agentic orchestration
- **Recursive System Mapping**: Self-referential cognitive processing
- **Emergent Properties**: Cross-module tensor flow enables cognitive synergy

## Documentation

- **Foundation Tensor DOF**: `FOUNDATION_TENSOR_DOF.md` - Comprehensive tensor documentation
- **Architecture**: `ARCHITECTURE.md` - System-wide architecture overview
- **Agent Configuration**: `.github/agents/cogml.md` - AI agent understanding
- **Build Scripts**: `foundation-build.sh` - Build system documentation
- **Test Scripts**: `foundation-test.sh` - Testing framework documentation

## Validation

The cognitive kernel seed has been validated for:

- ✅ Recursive implementation (no mocks)
- ✅ Tensor DOF consistency across all modules
- ✅ Hardware matrix detection and optimization
- ✅ Multi-architecture support
- ✅ GGML kernel integration
- ✅ Artifact generation for downstream jobs
- ✅ Comprehensive documentation

## Visionary Note

> "This layer forms the atomic substrate of your distributed cognition—prime candidates to be first-order tensors in the agentic catalog."

The Cognitive Kernel Seed establishes the foundational tensor operations that enable emergent cognitive properties through neural-symbolic integration. Each component implements genuine recursive processing, ensuring that the cognitive architecture operates on true computational principles rather than mock implementations.

The multi-architecture hardware matrix ensures optimal performance across different platforms, while the GGML kernel adaptation provides state-of-the-art tensor operations. The generated artifacts enable seamless integration into downstream CI/CD pipelines and distributed cognitive systems.

**The atomic substrate of distributed cognition is now seeded and ready.**

---

## License

See LICENSE file in the repository root.

## Contributing

Contributions to the cognitive kernel should maintain:
- Recursive implementation principles (no mocks)
- Tensor DOF consistency
- Hardware-agnostic design with platform-specific optimizations
- Comprehensive testing across all recursion levels
- Documentation of tensor operations and DOF

## Contact

For questions about the cognitive kernel implementation, refer to:
- Issue tracker: GitHub Issues
- Documentation: `docs/` directory
- Agent: `.github/agents/cogml.md`

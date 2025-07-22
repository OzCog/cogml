# Build Troubleshooting Guide

This document provides solutions for common build failures in the CogML ecosystem.

## Quick Fix for Build Failures

If you encounter build failures, try this automated verification script:

```bash
./scripts/verify-build.sh
```

## Common Issues and Solutions

### 1. Missing Guile Development Packages

**Symptoms:**
- AtomSpace fails to configure with "Guile was not found" error
- All dependent components (URE, CogServer, etc.) fail to build

**Solution:**
```bash
sudo apt-get install -y guile-3.0-dev cython3 python3-dev
```

### 2. Missing lib Directory in AtomSpace

**Symptoms:**
- CMake error: `ADD_SUBDIRECTORY given source "lib" which is not an existing directory`

**Solution:**
This is automatically handled in the CI workflow and the `lib` directory is now included in the repository. If you encounter this locally:

```bash
cd orc-as/atomspace
mkdir -p lib
echo "# Empty lib directory for build compatibility" > lib/CMakeLists.txt
```

### 3. Missing Unify Dependency for URE

**Symptoms:**
- URE fails to configure with "Unify missing: it is needed!" error

**Solution:**
```bash
cd /tmp
git clone --depth 1 https://github.com/opencog/unify
cd unify
mkdir -p build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release -DATOMSPACE_DATA_DIR=/usr/local/share/opencog
make -j$(nproc)
sudo make install
sudo ldconfig
```

### 4. Cython Compatibility Issues

**Symptoms:**
- Build succeeds for core libraries but fails on Python bindings
- Errors like "Invalid operand type for '*'" in .pyx files

**Solution:**
These are non-critical - the core C++ libraries build successfully. The Cython bindings may fail with newer Cython versions but don't affect the core functionality.

### 5. Dependency Installation Timeouts

**Symptoms:**
- apt-get commands timeout during CI builds
- Connection timeout errors

**Solution:**
The build scripts now use retry logic and chunked package installation:

```bash
./.github/scripts/install-deps.sh basic
```

## Build Order

Components must be built in this order due to dependencies:

1. **cogutil** (foundation) - Required by all others
2. **atomspace** (core) - Required by AI and server components  
3. **unify** (external) - Required by URE
4. **ure** (AI reasoning) - Can be built in parallel with moses/cogserver
5. **moses** (AI optimization) - Independent of other AI components
6. **cogserver** (server) - Requires atomspace but independent of AI components

## Verification Commands

Test each component individually:

```bash
# Test cogutil
cd orc-dv/cogutil && mkdir -p build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release && make -j$(nproc)

# Test atomspace
cd ../../../orc-as/atomspace && mkdir -p build && cd build  
cmake .. -DCMAKE_BUILD_TYPE=Release && make -j$(nproc)

# Test URE (after building unify)
cd ../../../orc-ai/ure && mkdir -p build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release && make -j$(nproc)

# Test MOSES
cd ../../../orc-ai/moses && mkdir -p build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release && make -j$(nproc)

# Test CogServer
cd ../../../orc-sv/cogserver && mkdir -p build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release && make -j$(nproc)
```

## Environment Requirements

- Ubuntu 24.04 or compatible
- CMake 3.10+
- GCC/G++ 9+
- Python 3.8+
- Guile 3.0+
- Boost 1.60+

## Getting Help

If you continue to experience build issues:

1. Run the verification script: `./scripts/verify-build.sh`
2. Check the specific error messages against this guide
3. Ensure all dependencies are properly installed
4. Try building components individually to isolate the issue
5. Check that you're using compatible versions of dependencies
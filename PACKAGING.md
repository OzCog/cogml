# CogML Package Generation

This document describes the package generation functionality implemented for the CogML project as per issue #172.

## Overview

The CogML project now supports automatic package generation after build completion, providing both traditional binary packages and specialized cognitive artifact packages using OpenCog-style hypergraph pattern encoding.

## Features

### 1. CPack Binary Package Generation

The main `CMakeLists.txt` includes comprehensive CPack configuration that supports:

- **TGZ/ZIP Archives**: Cross-platform compressed archives
- **Debian Packages**: For Ubuntu/Debian systems with proper dependencies
- **Component-based Packaging**: Modular installation (foundation, core, ai, robotics, web, docs)
- **Source Packages**: Distribution source code with proper exclusions

### 2. Scheme Hypergraph Cognitive Artifact Packaging

The `pack-cogml.scm` script provides specialized packaging for cognitive artifacts:

- **Hypergraph Pattern Detection**: Identifies OpenCog-style cognitive patterns
- **Recursive Artifact Collection**: Scans cognitive directories (scheme/, src/, opencog/, etc.)
- **Cognitive Complexity Analysis**: Measures pattern density and complexity
- **Metadata Extraction**: Generates comprehensive artifact metadata
- **Validation Functions**: Includes package integrity validation

### 3. Automated CI/CD Integration

The GitHub Actions workflow `build-test-package.yml` includes:

- **Post-build Package Generation**: Runs `cpack` after successful builds
- **Scheme Package Creation**: Executes hypergraph packaging script
- **Artifact Upload**: Stores packages with 30-day retention
- **Release Automation**: Creates GitHub releases for tagged versions

## Usage

### Manual Package Generation

1. **Build the project:**
   ```bash
   mkdir build && cd build
   cmake .. -DCMAKE_BUILD_TYPE=Release
   make
   ```

2. **Generate binary packages:**
   ```bash
   cpack                    # Generate all configured formats
   cpack -G TGZ            # Generate only TGZ
   cpack -G DEB            # Generate only Debian package
   ```

3. **Generate cognitive artifact package:**
   ```bash
   cd ..
   guile -s pack-cogml.scm release
   ```

### Automated Package Generation

Packages are automatically generated for:

- **Push to main branch**: Creates development packages
- **Tagged releases**: Creates release packages with GitHub release
- **Pull requests**: Validates packaging functionality

### Package Output

Generated packages include:

- `cogml-VERSION-Linux.tar.gz` - Binary distribution (TGZ)
- `cogml-VERSION-Linux.zip` - Binary distribution (ZIP)  
- `cogml-VERSION-Linux.deb` - Debian package
- `release/cogml-hypergraph.scm` - Cognitive artifact package
- `release/packaging-summary.txt` - Packaging report

## Package Contents

### Binary Packages
- Compiled libraries and executables
- Documentation and README files
- Configuration files and examples
- Install scripts and metadata

### Cognitive Artifact Package
- Hypergraph-encoded cognitive patterns
- Scheme code and AtomSpace definitions
- Python integration modules
- Cognitive complexity metrics
- Validation functions

## Validation

Run the validation suite to test packaging functionality:

```bash
./validate-packaging.sh
```

This tests:
- CPack configuration
- Scheme script functionality  
- GitHub Actions integration
- Package generation
- Content validation

## Dependencies

### Build Dependencies
- CMake 3.16+
- Boost libraries (≥1.60)
- Build tools (gcc/clang)

### Packaging Dependencies
- CPack (included with CMake)
- Guile 3.0+ (for cognitive artifacts)
- Debian tools (for .deb packages)

## Configuration

### CPack Settings

Key CPack variables in `CMakeLists.txt`:
- `CPACK_PACKAGE_NAME`: Package name
- `CPACK_PACKAGE_VERSION`: Version number
- `CPACK_GENERATOR`: Output formats
- `CPACK_COMPONENTS_ALL`: Component list

### Scheme Script Settings

Configuration in `pack-cogml.scm`:
- `*artifact-extensions*`: File types to package
- `*cognitive-directories*`: Directories to scan
- `*hypergraph-patterns*`: Patterns to detect

## Integration with ECAN

The packaging system implements Economic Attention Allocation (ECAN) principles by:
- Prioritizing high-complexity cognitive modules
- Allocating packaging resources based on cognitive importance
- Optimizing attention for frequently updated components

## Future Extensions

The packaging framework supports extension for:
- Additional package formats (RPM, MSI, etc.)
- Custom cognitive artifact encoders
- Integration with tensor dimension encoding
- Distributed packaging for large cognitive modules

## Troubleshooting

Common issues and solutions:

1. **CMake configuration fails**: Install missing Boost libraries
2. **Scheme script fails**: Install Guile 3.0 or later
3. **Debian package creation fails**: Install `debhelper` and `fakeroot`
4. **GitHub Actions timeout**: Reduce package scope or increase timeout

For additional support, see the project's main documentation or create an issue.
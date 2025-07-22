# Build Timeout Fix Documentation

## Problem
The CogML build pipeline was failing due to timeout issues with large `apt-get install` commands that looked like this:

```bash
sudo apt-get update && sudo apt-get install -y build-essential cmake libboost-all-dev guile-3.0-dev cython3 python3-nose valgrind doxygen
```

This would crash sessions and cause build failures in the `atomspace` and `moses` jobs.

## Root Cause
1. **Large package installations**: Installing many packages in a single command
2. **Verbose output**: Default apt-get output was overwhelming logs
3. **No resilience**: If any package failed, the entire command failed
4. **Timeout sensitivity**: Long-running commands would hit GitHub Actions timeout limits

## Solution Implemented

### 1. Chunked Package Installation
Instead of one large command, we split into smaller, logical groups:

```bash
# Old approach (problematic)
sudo apt-get install -y build-essential cmake libboost-all-dev guile-3.0-dev cython3 python3-nose valgrind doxygen

# New approach (resilient)  
sudo apt-get update -q
sudo apt-get install -y -q build-essential cmake
sudo apt-get install -y -q libboost-all-dev
sudo apt-get install -y -q guile-3.0-dev cython3
sudo apt-get install -y -q python3-nose python3-dev valgrind doxygen
```

### 2. Quieter Output
Added `-q` flag to reduce log verbosity and prevent log size issues.

### 3. Enhanced Self-Healing
- Added self-healing capabilities to MOSES build step (matching AtomSpace)
- Integrated with existing `scripts/auto_fix.py` system
- Added environment variables for configuration

### 4. Files Modified
- `.github/workflows/cogml-build.yml` - Main workflow
- `.github/workflows/atomspace-build.yml` - AtomSpace-specific workflow  
- `.github/workflows/moses-build.yml` - MOSES-specific workflow

## Validation
- ✅ Tested chunked installation approach locally
- ✅ Confirmed CMake configuration works
- ✅ Successfully built cogutil component  
- ✅ Verified package installations complete without timeout

## Usage Guidelines
For future workflow modifications:

**✅ DO:**
- Split large package installations into smaller chunks
- Use `-q` flag for quieter output
- Group related packages together logically
- Test locally before deployment

**❌ DON'T:**
- Install more than 4-5 packages in a single apt-get command
- Use verbose output in automated builds
- Ignore timeout considerations for long-running commands

## Monitoring
Monitor the build pipeline for:
- Individual package installation timeouts
- Log size issues
- Self-healing system activation
- Overall build duration improvements

This fix specifically addresses issue #163 regarding CogML build pipeline failures.
# GitHub Actions Build Fix Summary

## Problem
The CogML build pipeline was failing on `atomspace` and `moses` jobs due to timeout issues with dependency installation commands (`sudo apt-get update && sudo apt-get install`).

## Root Cause
The GitHub Actions workflow was using direct `sudo apt-get update` and `sudo apt-get install` commands that are prone to:
- Network timeouts
- Package repository unavailability
- Hanging on interactive prompts
- Session crashes due to long-running operations

## Solution Implemented

### 1. Resilient Dependency Installation Script
Created `.github/scripts/install-deps.sh` with:
- **Retry Logic**: 3 attempts for `apt-get update` with 10-second delays between retries
- **Timeout Protection**: 300-second timeouts for all operations to prevent hanging
- **Non-Interactive Mode**: `DEBIAN_FRONTEND=noninteractive` to prevent prompts
- **Batch Installation**: Install packages in smaller groups to reduce failure risk
- **Profile Support**: Different dependency sets for different job types

### 2. Dependency Profiles
- `basic`: Essential build tools (cmake, build-essential, boost, python3-nose, valgrind, doxygen)
- `guile`: Basic + Guile development (guile-3.0-dev, cython3) + Python Cython
- `rocks`: Guile + RocksDB support (librocksdb-dev)
- `restful`: Guile + RESTful API support (libcpprest-dev) 
- `cogserver`: Guile + SSL support (libssl-dev)
- `moses`: Basic dependencies only (lightweight)

### 3. Updated Jobs
All major build jobs updated to use the resilient script:
- `cogutil` → `basic` profile
- `atomspace` → `guile` profile  
- `atomspace-rocks` → `rocks` profile
- `atomspace-restful` → `restful` profile
- `moses` → `moses` profile
- `ure`, `pln`, `miner`, `asmoses`, `learn` → `guile` profile
- `cogserver` → `cogserver` profile
- `opencog-central` → `rocks` profile

### 4. Lightweight Job Optimization
Packaging and documentation jobs use simplified retry logic for minimal dependencies.

## Expected Benefits
- **Reduced Timeouts**: Retry logic and timeouts prevent hanging builds
- **Better Reliability**: Batch installation reduces failure risk
- **Faster Builds**: Optimized dependency installation with appropriate profiles
- **Easier Maintenance**: Centralized dependency management

## Validation
- Script syntax validated
- All dependency profiles tested
- Maintains existing functionality while improving reliability

This addresses the specific timeout issues mentioned by @drzo and should resolve the failing `atomspace` and `moses` jobs in the build pipeline.
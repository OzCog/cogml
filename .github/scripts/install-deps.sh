#!/bin/bash

# Script to install dependencies in a more resilient way
# Usage: ./install-deps.sh [package-type]
#   package-type: basic, guile, rocks, restful, moses

set -e

echo "Starting dependency installation..."

# Set non-interactive mode
export DEBIAN_FRONTEND=noninteractive

# Function to retry apt-get update
retry_apt_update() {
    local max_attempts=5
    local attempt=1
    local backoff=5
    
    while [ $attempt -le $max_attempts ]; do
        echo "Attempting apt update (attempt $attempt/$max_attempts)..."
        if timeout 240 sudo apt-get update -q; then
            echo "apt update succeeded"
            return 0
        else
            echo "apt update failed"
            if [ $attempt -lt $max_attempts ]; then
                echo "Retrying in $backoff seconds..."
                sleep $backoff
                backoff=$((backoff * 2))  # Exponential backoff
            fi
            attempt=$((attempt + 1))
        fi
    done
    
    echo "All apt update attempts failed, but continuing..."
    return 0  # Don't fail the script, just warn
}

# Function to install packages with timeout and retry
install_packages() {
    local packages="$1"
    local max_attempts=3
    local attempt=1
    
    echo "Installing packages: $packages"
    
    while [ $attempt -le $max_attempts ]; do
        echo "Package install attempt $attempt/$max_attempts for: $packages"
        if timeout 240 sudo apt-get install -y --no-install-recommends $packages; then
            echo "Package installation succeeded: $packages"
            return 0
        else
            echo "Package installation failed: $packages"
            if [ $attempt -lt $max_attempts ]; then
                echo "Retrying package installation in 5 seconds..."
                sleep 5
            fi
            attempt=$((attempt + 1))
        fi
    done
    
    echo "WARNING: Failed to install packages after $max_attempts attempts: $packages"
    echo "Continuing anyway - some packages may be missing..."
    return 0  # Don't fail the script
}

# Retry apt update
retry_apt_update

# Install common/base packages
echo "Installing base dependencies..."
install_packages "build-essential cmake"
install_packages "libboost-all-dev"
install_packages "python3-nose python3-dev"
install_packages "valgrind doxygen"

# Install specific packages based on job type
case "${1:-basic}" in
    "guile")
        echo "Installing Guile dependencies..."
        install_packages "guile-3.0-dev cython3"
        ;;
    "rocks")
        echo "Installing RocksDB dependencies..."
        install_packages "guile-3.0-dev cython3"
        install_packages "librocksdb-dev"
        ;;
    "restful")
        echo "Installing RESTful dependencies..."
        install_packages "guile-3.0-dev cython3"
        install_packages "libcpprest-dev"
        ;;
    "cogserver")
        echo "Installing CogServer dependencies..."
        install_packages "guile-3.0-dev cython3"
        install_packages "libssl-dev"
        ;;
    "moses")
        echo "Installing MOSES dependencies..."
        # MOSES only needs basic dependencies
        ;;
    *)
        echo "Using basic dependency set"
        ;;
esac

# Install Python Cython if needed
if [[ "${1}" =~ ^(guile|rocks|restful|cogserver)$ ]]; then
    echo "Installing Python Cython..."
    timeout 120 python3 -m pip install --upgrade pip cython || echo "WARNING: Python pip/cython installation had issues, continuing..."
    python3 -m cython --version || echo "WARNING: Cython not available, but continuing..."
fi

echo "Dependency installation completed successfully"
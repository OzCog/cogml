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
    local max_attempts=3
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        echo "Attempting apt update (attempt $attempt/$max_attempts)..."
        if timeout 300 sudo apt-get update; then
            echo "apt update succeeded"
            return 0
        else
            echo "apt update failed"
            if [ $attempt -lt $max_attempts ]; then
                echo "Retrying in 10 seconds..."
                sleep 10
            fi
            attempt=$((attempt + 1))
        fi
    done
    
    echo "All apt update attempts failed"
    return 1
}

# Function to install packages with timeout
install_packages() {
    local packages="$1"
    echo "Installing packages: $packages"
    timeout 300 sudo apt-get install -y --no-install-recommends $packages
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
    python3 -m pip install --upgrade pip cython || true
    python3 -m cython --version || true
fi

echo "Dependency installation completed successfully"
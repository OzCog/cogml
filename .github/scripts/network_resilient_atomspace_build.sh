#!/bin/bash
# Helper script for network-resilient AtomSpace build
# Usage: network_resilient_atomspace_build.sh [atomspace_source_dir]

ATOMSPACE_DIR="${1:-orc-as/atomspace}"

echo "🔧 Building AtomSpace with network resilience"

cd "$ATOMSPACE_DIR"

# Create missing lib directory if it doesn't exist
if [ ! -d "lib" ]; then
  mkdir -p lib
  echo "# Empty lib directory for build compatibility" > lib/CMakeLists.txt
fi

# Network resilience: Handle Haskell bindings network connectivity issues
DISABLE_HASKELL=false

# Test connectivity to stackage snapshots
if ! curl -s --max-time 10 --connect-timeout 5 "https://raw.githubusercontent.com/commercialhaskell/stackage-snapshots/master/lts/14/27.yaml" > /dev/null; then
  echo "⚠️ Network connectivity to stackage snapshots is unavailable"
  DISABLE_HASKELL=true
fi

# Test connectivity to Haskell downloads
if ! curl -s --max-time 10 --connect-timeout 5 "https://downloads.haskell.org" > /dev/null; then
  echo "⚠️ Network connectivity to Haskell downloads is unavailable"
  DISABLE_HASKELL=true
fi

if [ "$DISABLE_HASKELL" = true ]; then
  echo "Temporarily disabling Haskell bindings to prevent build failure"
  # Disable Haskell bindings by commenting out the subdirectory addition
  if [ -f "opencog/CMakeLists.txt" ]; then
    sed -i 's/^\s*ADD_SUBDIRECTORY\s*(haskell)/# ADD_SUBDIRECTORY (haskell) # Disabled due to network issues/' opencog/CMakeLists.txt
  fi
else
  echo "✅ Network connectivity to Haskell resources is available"
fi

# Build
if [ ! -d "build" ]; then
  mkdir -p build
fi
cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)
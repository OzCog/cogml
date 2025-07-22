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
echo "Testing stackage snapshots connectivity..."
if ! curl -s --max-time 10 --connect-timeout 5 "https://raw.githubusercontent.com/commercialhaskell/stackage-snapshots/master/lts/14/27.yaml" > /dev/null; then
  echo "⚠️ Network connectivity to stackage snapshots is unavailable"
  DISABLE_HASKELL=true
fi

# Test connectivity to Haskell downloads (specific GHC file that commonly fails)
echo "Testing Haskell GHC download connectivity..."
if ! curl -s --max-time 15 --connect-timeout 10 --head "https://downloads.haskell.org/~ghc/8.6.5/ghc-8.6.5-x86_64-fedora27-linux.tar.xz" > /dev/null; then
  echo "⚠️ Network connectivity to Haskell GHC downloads is unavailable"
  DISABLE_HASKELL=true
fi

# Additional safety check: test if Stack can list GHC versions (which requires network)
echo "Testing Stack network functionality..."
if ! timeout 30s stack --resolver lts-14.27 list-dependencies --depth 0 > /dev/null 2>&1; then
  echo "⚠️ Stack network operations are failing"
  DISABLE_HASKELL=true
fi

if [ "$DISABLE_HASKELL" = true ]; then
  echo "🚫 Temporarily disabling Haskell bindings to prevent build failure"
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
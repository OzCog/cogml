#!/bin/bash

# Script to fix missing lib directories that cause CMake ADD_SUBDIRECTORY errors
# This addresses the issue where atomspace and related components expect lib/ directories

set -e

echo "🔧 Fixing missing lib directories for OpenCog components..."

# List of components that need lib directories based on CMakeLists.txt requirements
COMPONENTS_NEEDING_LIB=(
    "orc-as/atomspace"
    "orc-as/atomspace-rocks"
    "orc-as/atomspace-restful"
    "orc-ct/spacetime"
)

for component in "${COMPONENTS_NEEDING_LIB[@]}"; do
    lib_dir="${component}/lib"
    
    if [ -d "$component" ]; then
        if [ ! -d "$lib_dir" ]; then
            echo "Creating missing lib directory: $lib_dir"
            mkdir -p "$lib_dir"
            echo "# Empty lib directory for build compatibility" > "$lib_dir/CMakeLists.txt"
            echo "✅ Created: $lib_dir/CMakeLists.txt"
        else
            echo "✅ Already exists: $lib_dir"
        fi
    else
        echo "⚠️  Component not found: $component"
    fi
done

echo "✅ Lib directory fix completed"
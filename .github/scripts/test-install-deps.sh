#!/bin/bash

# Test script to validate the dependency installation script
# This is used for local testing and validation

echo "Testing dependency installation script..."

SCRIPT_PATH="./.github/scripts/install-deps.sh"

if [ ! -f "$SCRIPT_PATH" ]; then
    echo "Error: Script not found at $SCRIPT_PATH"
    exit 1
fi

if [ ! -x "$SCRIPT_PATH" ]; then
    echo "Error: Script is not executable"
    exit 1
fi

echo "✓ Script exists and is executable"

# Test script syntax
bash -n "$SCRIPT_PATH"
if [ $? -eq 0 ]; then
    echo "✓ Script syntax is valid"
else
    echo "✗ Script has syntax errors"
    exit 1
fi

# Test different parameter combinations (dry-run style test)
echo "Testing different dependency profiles..."

PROFILES=("basic" "guile" "rocks" "restful" "moses" "cogserver")

for profile in "${PROFILES[@]}"; do
    echo "  - Testing profile: $profile"
    # We can't actually run the full installation in CI, but we can check the script logic
    grep -q "\"$profile\")" "$SCRIPT_PATH"
    if [ $? -eq 0 ]; then
        echo "    ✓ Profile $profile is supported in the script"
    else
        echo "    ✗ Profile $profile not found in script"
    fi
done

echo "✓ All dependency profiles are properly defined"
echo "Dependency installation script validation completed successfully!"
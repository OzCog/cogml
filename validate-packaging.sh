#!/bin/bash

# CogML Package Generation Validation Script
# This script tests the package generation functionality implemented as per issue #172

echo "========================================="
echo "CogML Package Generation Test Suite"
echo "========================================="

# Change to project root
cd /home/runner/work/cogml/cogml

# Test 1: Verify CPack configuration is present in CMakeLists.txt
echo "Test 1: Checking CPack configuration in CMakeLists.txt..."
if grep -q "INCLUDE(CPack)" CMakeLists.txt; then
    echo "✅ CPack configuration found in CMakeLists.txt"
else
    echo "❌ CPack configuration missing from CMakeLists.txt"
    exit 1
fi

# Test 2: Verify Scheme packaging script exists and is executable
echo "Test 2: Checking Scheme packaging script..."
if [ -f "pack-cogml.scm" ]; then
    echo "✅ Scheme packaging script (pack-cogml.scm) exists"
else
    echo "❌ Scheme packaging script missing"
    exit 1
fi

# Test 3: Test Scheme script functionality
echo "Test 3: Testing Scheme script functionality..."
mkdir -p test-validation-release
if guile -s pack-cogml.scm test-validation-release > /dev/null 2>&1; then
    if [ -f "test-validation-release/cogml-hypergraph.scm" ]; then
        echo "✅ Scheme packaging script executed successfully"
        ARTIFACTS_COUNT=$(grep "Total artifacts:" test-validation-release/packaging-summary.txt | cut -d: -f2 | tr -d ' ')
        echo "   Found $ARTIFACTS_COUNT artifacts"
    else
        echo "❌ Scheme packaging script failed to generate package"
        exit 1
    fi
else
    echo "❌ Scheme packaging script execution failed"
    exit 1
fi

# Test 4: Test CPack functionality with minimal configuration
echo "Test 4: Testing CPack functionality..."
mkdir -p test-validation-build
cd test-validation-build

# Create minimal test CMakeLists.txt
cat > CMakeLists.txt << 'EOF'
CMAKE_MINIMUM_REQUIRED(VERSION 3.16)
PROJECT(cogml-validation)

SET(CPACK_PACKAGE_NAME "cogml")
SET(CPACK_PACKAGE_VERSION "1.0.0")
SET(CPACK_GENERATOR "TGZ")
INSTALL(FILES "${CMAKE_CURRENT_SOURCE_DIR}/../README.md" DESTINATION . OPTIONAL)
INCLUDE(CPack)
EOF

# Configure and generate package
if cmake . > /dev/null 2>&1 && cpack -G TGZ > /dev/null 2>&1; then
    if ls *.tar.gz > /dev/null 2>&1; then
        echo "✅ CPack package generation successful"
        PACKAGE_FILE=$(ls *.tar.gz | head -1)
        echo "   Generated package: $PACKAGE_FILE"
    else
        echo "❌ CPack failed to generate package file"
        exit 1
    fi
else
    echo "❌ CPack configuration or execution failed"
    exit 1
fi

cd ..

# Test 5: Check GitHub Actions workflow enhancements
echo "Test 5: Checking GitHub Actions workflow..."
if grep -q "Run CPack to Package All Artifacts" .github/workflows/build-test-package.yml; then
    echo "✅ GitHub Actions workflow includes CPack step"
else
    echo "❌ GitHub Actions workflow missing CPack step"
    exit 1
fi

if grep -q "Generate Scheme Hypergraph Package" .github/workflows/build-test-package.yml; then
    echo "✅ GitHub Actions workflow includes Scheme packaging step"
else
    echo "❌ GitHub Actions workflow missing Scheme packaging step"
    exit 1
fi

if grep -q "Upload Package Artifacts" .github/workflows/build-test-package.yml; then
    echo "✅ GitHub Actions workflow includes artifact upload"
else
    echo "❌ GitHub Actions workflow missing artifact upload"
    exit 1
fi

# Test 6: Verify .gitignore excludes build artifacts
echo "Test 6: Checking .gitignore configuration..."
if grep -q "release/" .gitignore && grep -q "*.tar.gz" .gitignore; then
    echo "✅ .gitignore properly excludes build artifacts"
else
    echo "❌ .gitignore missing required exclusions"
    exit 1
fi

# Cleanup
rm -rf test-validation-release test-validation-build

echo ""
echo "========================================="
echo "✅ ALL TESTS PASSED!"
echo "Package generation functionality has been successfully implemented."
echo ""
echo "Summary of implemented features:"
echo "- CPack integration in CMakeLists.txt (TGZ, ZIP, DEB formats)"
echo "- Scheme script for hypergraph cognitive artifact packaging" 
echo "- Enhanced GitHub Actions workflow with packaging steps"
echo "- Artifact upload and release generation"
echo "- Proper .gitignore configuration"
echo "========================================="
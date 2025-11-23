#!/bin/bash
# Build MkDocs documentation for production

set -e

echo "=========================================="
echo "Building MkDocs Documentation"
echo "=========================================="

# Check if mkdocs is installed
if ! command -v mkdocs &> /dev/null; then
    echo "Error: mkdocs is not installed"
    echo "Install it with: pip install mkdocs-material"
    exit 1
fi

# Build documentation
echo "Building documentation..."
mkdocs build --clean

# Verify build
if [ ! -d "site" ]; then
    echo "Error: site directory was not created"
    exit 1
fi

echo ""
echo "=========================================="
echo "Documentation built successfully!"
echo "=========================================="
echo "Output directory: site/"
echo ""
echo "Next steps:"
echo "1. Test locally: mkdocs serve"
echo "2. Deploy to production (see doc/DEPLOYMENT.md)"
echo ""


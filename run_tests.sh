#!/bin/bash
# Test runner script

echo "Running hotel AI agent tests..."
echo "================================"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run pytest with coverage
pytest tests/ -v --tb=short

echo ""
echo "Tests completed!"
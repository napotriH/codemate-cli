#!/bin/bash

echo "🚀 Installing CodeMate CLI..."

# Check if Python is installed
if ! command -v python &> /dev/null; then
    echo "❌ Python is not installed. Please install Python first."
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Install CodeMate CLI
echo "⚙️ Installing CodeMate CLI..."
python install.py

echo "✅ Installation complete!"
echo ""
echo "Usage:"
echo "  codemate    - Start CodeMate CLI"
echo ""
echo "Enjoy coding with CodeMate! 🎉"
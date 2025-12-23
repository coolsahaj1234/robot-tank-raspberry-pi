#!/bin/bash

# Helper script to set up Xcode project
# This creates a basic project structure guide

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_NAME="RobotController"

echo "🤖 macOS Robot Controller - Project Setup Helper"
echo "=================================================="
echo ""

# Check for Xcode
if ! command -v xcodebuild &> /dev/null; then
    echo "❌ Xcode is not installed!"
    echo ""
    echo "Please install Xcode first:"
    echo "  1. Open App Store"
    echo "  2. Search for 'Xcode'"
    echo "  3. Click 'Get' (it's free)"
    echo "  4. Wait for installation (~10GB, 30-60 min)"
    echo "  5. Open Xcode once to accept license"
    echo ""
    echo "Then run this script again."
    exit 1
fi

echo "✅ Xcode found: $(xcodebuild -version | head -1)"
echo ""

# Check if project already exists
if [ -d "$PROJECT_DIR/$APP_NAME.xcodeproj" ]; then
    echo "⚠️  Xcode project already exists at:"
    echo "   $PROJECT_DIR/$APP_NAME.xcodeproj"
    echo ""
    read -p "Open it in Xcode? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        open "$PROJECT_DIR/$APP_NAME.xcodeproj"
        exit 0
    fi
fi

echo "📋 Setup Instructions:"
echo ""
echo "Since Xcode project files are complex, please create the project manually:"
echo ""
echo "1. Open Xcode"
echo "2. File → New → Project"
echo "3. Choose: macOS → App"
echo "4. Fill in:"
echo "   - Product Name: RobotController"
echo "   - Interface: SwiftUI"
echo "   - Language: Swift"
echo "5. Save in: $PROJECT_DIR"
echo "6. Then add all Swift files from RobotController/ folder"
echo ""
echo "📖 See INSTALL.md for detailed step-by-step instructions"
echo ""
echo "Would you like to open the project directory? (y/n)"
read -p "> " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    open "$PROJECT_DIR"
fi

echo ""
echo "✅ Setup helper complete!"
echo "   Next: Follow INSTALL.md for detailed instructions"


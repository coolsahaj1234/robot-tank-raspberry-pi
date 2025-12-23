#!/bin/bash

# Build and Run Script for Robot Controller macOS App
# This script will create an Xcode project and build/run the app

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_NAME="RobotController"
BUILD_DIR="$PROJECT_DIR/build"
PROJECT_FILE="$PROJECT_DIR/$APP_NAME.xcodeproj"

echo "🤖 Robot Controller Build Script"
echo "================================"
echo ""

# Check for Xcode
if ! command -v xcodebuild &> /dev/null; then
    echo "❌ Error: Xcode command-line tools not found!"
    echo "Please install Xcode from the App Store, or run:"
    echo "  xcode-select --install"
    exit 1
fi

echo "✅ Found Xcode command-line tools"

# Check if Xcode project exists
if [ ! -d "$PROJECT_FILE" ]; then
    echo ""
    echo "📦 Creating Xcode project..."
    echo "This will open Xcode - please follow these steps:"
    echo "  1. In Xcode, go to File → Save Project"
    echo "  2. Close Xcode"
    echo "  3. Run this script again"
    echo ""
    
    # Create project structure
    mkdir -p "$PROJECT_DIR/$APP_NAME.xcodeproj"
    
    # Try to open Xcode to create project
    if command -v open &> /dev/null; then
        echo "Opening Xcode..."
        open -a Xcode "$PROJECT_DIR"
    else
        echo "Please open Xcode manually and create a new macOS App project named '$APP_NAME'"
    fi
    
    exit 0
fi

echo "✅ Found Xcode project"

# Build the project
echo ""
echo "🔨 Building project..."
xcodebuild -project "$PROJECT_FILE" \
    -scheme "$APP_NAME" \
    -configuration Release \
    -derivedDataPath "$BUILD_DIR" \
    clean build

if [ $? -ne 0 ]; then
    echo "❌ Build failed!"
    echo "Please check the errors above and fix them in Xcode"
    exit 1
fi

echo ""
echo "✅ Build successful!"

# Find the built app
APP_PATH="$BUILD_DIR/Build/Products/Release/$APP_NAME.app"

if [ -d "$APP_PATH" ]; then
    echo ""
    echo "🚀 Launching app..."
    open "$APP_PATH"
    echo "✅ App launched!"
else
    echo "⚠️  App bundle not found at expected location: $APP_PATH"
    echo "Please build the project in Xcode and run it from there"
fi


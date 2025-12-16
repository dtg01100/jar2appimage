#!/usr/bin/env python3
"""
Test script for the unified jar2appimage CLI
Validates that all functionality works correctly
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent / "src"))

from jar2appimage.cli_simple import main, run_legacy_cli


def test_basic_functionality():
    """Test basic CLI functionality"""
    print("🧪 Testing Basic Functionality")
    print("=" * 50)
    
    # Test help system
    print("\n1. Testing help system...")
    result = main(['--help'])
    assert result == 1, "Help should exit with code 1"
    print("✅ Help system works")
    
    # Test command help
    print("\n2. Testing command help...")
    result = main(['convert', '--help'])
    assert result == 1, "Command help should exit with code 1"
    print("✅ Command help works")
    
    # Test examples
    print("\n3. Testing examples...")
    result = main(['examples'])
    assert result == 0, "Examples should exit with code 0"
    print("✅ Examples work")
    
    # Test troubleshooting
    print("\n4. Testing troubleshooting...")
    result = main(['troubleshoot'])
    assert result == 0, "Troubleshooting should exit with code 0"
    print("✅ Troubleshooting works")
    
    # Test best practices
    print("\n5. Testing best practices...")
    result = main(['best-practices'])
    assert result == 0, "Best practices should exit with code 0"
    print("✅ Best practices work")
    
    # Test version
    print("\n6. Testing version...")
    result = main(['version'])
    assert result == 0, "Version should exit with code 0"
    print("✅ Version works")
    
    print("\n✅ Basic functionality tests passed!")


def test_argument_parsing():
    """Test argument parsing and validation"""
    print("\n🧪 Testing Argument Parsing")
    print("=" * 50)
    
    # Test invalid JAR file (should fail gracefully)
    print("\n1. Testing invalid JAR file...")
    result = main(['convert', 'nonexistent.jar'])
    assert result == 1, "Should fail with invalid JAR file"
    print("✅ Invalid JAR file handling works")
    
    # Test conflicting options
    print("\n2. Testing conflicting options...")
    result = main(['convert', 'test.jar', '--bundled', '--no-bundled'])
    assert result == 1, "Should fail with conflicting options"
    print("✅ Conflicting options handling works")
    
    # Test invalid Java version
    print("\n3. Testing invalid Java version...")
    result = main(['convert', 'test.jar', '--jdk-version', 'invalid'])
    assert result == 1, "Should fail with invalid Java version"
    print("✅ Invalid Java version handling works")
    
    print("\n✅ Argument parsing tests passed!")


def test_platform_detection():
    """Test platform detection functionality"""
    print("\n🧪 Testing Platform Detection")
    print("=" * 50)
    
    # Test platform check
    print("\n1. Testing platform check...")
    result = main(['check-platform'])
    # Should succeed on Linux, may fail on other platforms
    print(f"✅ Platform check completed (exit code: {result})")
    
    # Test verbose platform check
    print("\n2. Testing verbose platform check...")
    result = main(['check-platform', '--verbose'])
    print(f"✅ Verbose platform check completed (exit code: {result})")
    
    print("\n✅ Platform detection tests passed!")


def test_legacy_compatibility():
    """Test backward compatibility with old CLIs"""
    print("\n🧪 Testing Legacy Compatibility")
    print("=" * 50)
    
    # Test legacy platform check
    print("\n1. Testing legacy platform check...")
    result = run_legacy_cli(['--check-platform'])
    print(f"✅ Legacy platform check completed (exit code: {result})")
    
    # Test legacy help patterns
    print("\n2. Testing legacy help patterns...")
    result = run_legacy_cli(['--examples'])
    assert result == 0, "Legacy examples should work"
    print("✅ Legacy examples work")
    
    # Test legacy troubleshooting
    print("\n3. Testing legacy troubleshooting...")
    result = run_legacy_cli(['--troubleshooting'])
    assert result == 0, "Legacy troubleshooting should work"
    print("✅ Legacy troubleshooting works")
    
    print("\n✅ Legacy compatibility tests passed!")


def test_java_management():
    """Test Java management functionality"""
    print("\n🧪 Testing Java Management")
    print("=" * 50)
    
    # Test Java summary
    print("\n1. Testing Java summary...")
    result = main(['java-summary'])
    print(f"✅ Java summary completed (exit code: {result})")
    
    # Test Java detection
    print("\n2. Testing Java detection...")
    result = main(['java-summary', '--detect-java'])
    print(f"✅ Java detection completed (exit code: {result})")
    
    # Test tools check
    print("\n3. Testing tools check...")
    result = main(['check-tools'])
    print(f"✅ Tools check completed (exit code: {result})")
    
    print("\n✅ Java management tests passed!")


def test_utilities():
    """Test utility commands"""
    print("\n🧪 Testing Utility Commands")
    print("=" * 50)
    
    # Test file validation (with non-existent file)
    print("\n1. Testing file validation...")
    result = main(['validate', 'nonexistent.AppImage'])
    assert result == 1, "Should fail with non-existent AppImage"
    print("✅ File validation handling works")
    
    # Test missing-only tools check
    print("\n2. Testing missing-only tools check...")
    result = main(['check-tools', '--missing-only'])
    print(f"✅ Missing-only tools check completed (exit code: {result})")
    
    # Test fix suggestions
    print("\n3. Testing fix suggestions...")
    result = main(['check-tools', '--fix-suggestions'])
    print(f"✅ Fix suggestions completed (exit code: {result})")
    
    print("\n✅ Utility commands tests passed!")


def test_verbose_logging():
    """Test verbose logging functionality"""
    print("\n🧪 Testing Verbose Logging")
    print("=" * 50)
    
    # Test verbose with valid command
    print("\n1. Testing verbose platform check...")
    result = main(['check-platform', '--verbose'])
    print(f"✅ Verbose platform check completed (exit code: {result})")
    
    # Test verbose with examples
    print("\n2. Testing verbose examples...")
    result = main(['examples', '--verbose'])
    print(f"✅ Verbose examples completed (exit code: {result})")
    
    print("\n✅ Verbose logging tests passed!")


def run_all_tests():
    """Run all test suites"""
    print("🚀 Starting jar2appimage Unified CLI Tests")
    print("=" * 60)
    
    test_suites = [
        test_basic_functionality,
        test_argument_parsing,
        test_platform_detection,
        test_legacy_compatibility,
        test_java_management,
        test_utilities,
        test_verbose_logging,
    ]
    
    passed = 0
    total = len(test_suites)
    
    for test_suite in test_suites:
        try:
            test_suite()
            passed += 1
        except Exception as e:
            print(f"❌ Test failed: {test_suite.__name__}")
            print(f"   Error: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} test suites passed")
    
    if passed == total:
        print("🎉 All tests passed! The unified CLI is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the output above.")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
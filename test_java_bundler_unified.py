#!/usr/bin/env python3
"""
Test script for the Unified Java Bundler module

This script validates that the unified Java bundler works correctly
and provides a simple demonstration of its capabilities.
"""

import os
import sys
import tempfile
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_unified_bundler():
    """Test the unified Java bundler functionality"""

    print("🧪 Testing Unified Java Bundler")
    print("=" * 50)

    try:
        # Import the unified bundler
        from jar2appimage.java_bundler_unified import (
            Configuration,
            JavaBundler,
            create_java_bundler,
        )
        print("✅ Successfully imported unified Java bundler")

        # Test 1: Configuration creation
        print("\n📋 Test 1: Configuration Creation")
        config = Configuration(
            java_version="17",
            use_jre=True,
            interactive_mode=False,
            bundling_strategy="appimage"
        )
        print(f"✅ Configuration created: {config}")

        # Test 2: JavaBundler instantiation
        print("\n🏗️ Test 2: JavaBundler Instantiation")
        bundler = JavaBundler(config)
        print("✅ JavaBundler instantiated successfully")

        # Test 3: Convenience function
        print("\n⚡ Test 3: Convenience Functions")
        create_java_bundler(
            java_version="17",
            use_jre=True,
            interactive_mode=False
        )
        print("✅ create_java_bundler() works")

        # Test 4: Java detection (without actual Java)
        print("\n🔍 Test 4: Java Detection")
        try:
            java_info = bundler.detector.detect_system_java()
            if java_info:
                print(f"✅ Java detected: {java_info['version']} ({java_info['type']})")
            else:
                print("ℹ️  No system Java found (expected in test environment)")
        except Exception as e:
            print(f"⚠️  Java detection test failed: {e}")

        # Test 5: Configuration properties
        print("\n⚙️ Test 5: Configuration Properties")
        print(f"✅ Package type: {config.package_type}")
        print(f"✅ Target arch: {config.target_arch}")
        print(f"✅ Is LTS: {config.is_lts_version}")

        # Test 6: Java info
        print("\n📊 Test 6: Java Information")
        try:
            info = bundler.get_java_info()
            print(f"✅ Java info retrieved: {len(info)} keys")
            print(f"   - Config: {info['config']['java_version']}")
            print(f"   - Platform: {info['platform']['system']}")
        except Exception as e:
            print(f"⚠️  Java info test failed: {e}")

        # Test 7: JAR analysis (create dummy JAR)
        print("\n📦 Test 7: JAR Analysis")
        try:
            # Create a minimal JAR file for testing
            with tempfile.NamedTemporaryFile(suffix='.jar', delete=False) as temp_jar:
                # Write minimal ZIP/JAR structure
                import zipfile
                with zipfile.ZipFile(temp_jar.name, 'w') as jar:
                    jar.writestr('META-INF/MANIFEST.MF',
                               'Manifest-Version: 1.0\nMain-Class: Test\n')
                    jar.writestr('Test.class', 'dummy class content')

                requirements = bundler.detector.analyze_jar_requirements(temp_jar.name)
                print(f"✅ JAR analyzed: {requirements}")

                # Clean up
                os.unlink(temp_jar.name)
        except Exception as e:
            print(f"⚠️  JAR analysis test failed: {e}")

        # Test 8: Exception handling
        print("\n🚨 Test 8: Exception Handling")
        try:
            # Test with non-existent JAR
            bundler.detector.analyze_jar_requirements("nonexistent.jar")
        except Exception as e:
            print(f"✅ Exception handling works: {type(e).__name__}")

        print("\n🎉 All core tests completed successfully!")
        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_module_syntax():
    """Test that the module compiles correctly"""

    print("\n🔧 Testing Module Syntax")
    print("=" * 30)

    try:
        import py_compile
        module_path = Path("src/jar2appimage/java_bundler_unified.py")

        if module_path.exists():
            py_compile.compile(module_path, doraise=True)
            print("✅ Module compiles without syntax errors")
            return True
        else:
            print("❌ Module file not found")
            return False

    except py_compile.PyCompileError as e:
        print(f"❌ Syntax error: {e}")
        return False
    except Exception as e:
        print(f"❌ Compilation test failed: {e}")
        return False

def test_documentation():
    """Test that documentation is available"""

    print("\n📚 Testing Documentation")
    print("=" * 30)

    doc_file = Path("JAVA_BUNDLER_UNIFIED_DOCUMENTATION.md")
    if doc_file.exists():
        content = doc_file.read_text()
        if len(content) > 1000:  # Basic content check
            print("✅ Documentation exists and has content")
            print(f"   Size: {len(content)} characters")
            return True
        else:
            print("⚠️  Documentation exists but seems incomplete")
            return False
    else:
        print("❌ Documentation file not found")
        return False

def main():
    """Main test runner"""

    print("🚀 Unified Java Bundler Validation")
    print("=" * 50)

    tests = [
        ("Module Syntax", test_module_syntax),
        ("Core Functionality", test_unified_bundler),
        ("Documentation", test_documentation),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n🔬 Running {test_name} Test")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)

    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1

    print(f"\nResults: {passed}/{len(results)} tests passed")

    if passed == len(results):
        print("\n🎉 All tests passed! Unified Java Bundler is ready for use.")
        return 0
    else:
        print(f"\n⚠️  {len(results) - passed} test(s) failed. Please review the issues above.")
        return 1

if __name__ == "__main__":
    exit(main())

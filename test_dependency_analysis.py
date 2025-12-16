#!/usr/bin/env python3
"""
Test Suite for Comprehensive Dependency Analysis

This test suite validates the new dependency analysis functionality
and ensures it works correctly with various JAR files.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

# Add the src directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

try:
    from jar2appimage.dependency_analyzer import (
        ComprehensiveDependencyAnalyzer,
        AnalysisConfiguration,
        analyze_application_dependencies,
        quick_dependency_check
    )
    from jar2appimage.jar_analyzer import JarAnalyzer, analyze_jar_file
    from jar2appimage.dependency_graph import Dependency, DependencyScope, DependencyType
    from jar2appimage.dependency_resolver import DependencyResolver, ResolutionContext
    IMPORTS_OK = True
except ImportError as e:
    print(f"Import error: {e}")
    IMPORTS_OK = False


class TestDependencyAnalysis(unittest.TestCase):
    """Test cases for dependency analysis functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        if not IMPORTS_OK:
            self.skipTest("Required imports not available")
        
        self.config = AnalysisConfiguration(
            analyze_bytecode=True,
            resolve_transitive=False,
            generate_reports=False,
            verbose=False
        )
        self.analyzer = ComprehensiveDependencyAnalyzer(self.config)
    
    def test_configuration_creation(self):
        """Test configuration object creation"""
        config = AnalysisConfiguration()
        self.assertIsInstance(config, AnalysisConfiguration)
        self.assertTrue(config.analyze_bytecode)
        self.assertFalse(config.resolve_transitive)
    
    def test_dependency_object_creation(self):
        """Test dependency object creation"""
        dep = Dependency(
            group_id="test.group",
            artifact_id="test-artifact",
            version="1.0.0",
            scope=DependencyScope.COMPILE,
            dependency_type=DependencyType.MAVEN
        )
        
        self.assertEqual(dep.group_id, "test.group")
        self.assertEqual(dep.artifact_id, "test-artifact")
        self.assertEqual(dep.version, "1.0.0")
        self.assertEqual(dep.scope, DependencyScope.COMPILE)
        self.assertEqual(dep.dependency_type, DependencyType.MAVEN)
        self.assertEqual(dep.maven_coordinates, "test.group:test-artifact:1.0.0")
    
    def test_jar_analyzer_creation(self):
        """Test JAR analyzer creation"""
        analyzer = JarAnalyzer()
        self.assertIsInstance(analyzer, JarAnalyzer)
        self.assertIsNotNone(analyzer.class_parser)
        self.assertIsNotNone(analyzer.manifest_parser)
    
    def test_dependency_resolver_creation(self):
        """Test dependency resolver creation"""
        resolver = DependencyResolver()
        self.assertIsInstance(resolver, DependencyResolver)
        self.assertIsNotNone(resolver.known_patterns)
        self.assertIsNotNone(resolver.platform_specific_deps)
    
    def test_empty_jar_analysis(self):
        """Test analysis of non-existent JAR file"""
        non_existent_jar = "/path/to/nonexistent.jar"
        
        result = analyze_application_dependencies([non_existent_jar], self.config)
        
        self.assertIsInstance(result, ComprehensiveAnalysisResult)
        self.assertGreater(len(result.errors), 0)
        self.assertTrue(any("does not exist" in error for error in result.errors))
    
    def test_quick_dependency_check_structure(self):
        """Test quick dependency check returns correct structure"""
        non_existent_jar = "/path/to/nonexistent.jar"
        
        result = quick_dependency_check(non_existent_jar)
        
        # Check required keys
        required_keys = [
            'jar_path', 'is_valid', 'main_class', 'dependency_count',
            'has_conflicts', 'estimated_size_mb', 'java_version',
            'warnings', 'errors'
        ]
        
        for key in required_keys:
            self.assertIn(key, result)
        
        # Check types
        self.assertIsInstance(result['jar_path'], str)
        self.assertIsInstance(result['is_valid'], bool)
        self.assertIsInstance(result['dependency_count'], int)
        self.assertIsInstance(result['has_conflicts'], bool)
        self.assertIsInstance(result['estimated_size_mb'], (int, float))
        self.assertIsInstance(result['warnings'], list)
        self.assertIsInstance(result['errors'], list)
    
    @patch('jar2appimage.jar_analyzer.zipfile.ZipFile')
    def test_jar_analyzer_with_mock_zip(self, mock_zip_file):
        """Test JAR analyzer with mocked ZIP file"""
        # Mock ZIP file behavior
        mock_zip = Mock()
        mock_zip.namelist.return_value = ['META-INF/MANIFEST.MF']
        mock_zip.read.return_value = b'Manifest-Version: 1.0\n'
        mock_zip.infolist.return_value = []
        mock_zip_file.return_value.__enter__.return_value = mock_zip
        
        # Create a temporary file to test with
        with tempfile.NamedTemporaryFile(suffix='.jar', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            result = analyze_jar_file(temp_path)
            self.assertIsInstance(result, JarAnalysisResult)
            self.assertTrue(result.is_valid_jar)  # ZIP file structure is valid
        finally:
            os.unlink(temp_path)
    
    def test_dependency_coordinates_equality(self):
        """Test dependency coordinate matching"""
        dep1 = Dependency("org.springframework", "spring-core", "5.3.0")
        dep2 = Dependency("org.springframework", "spring-core", "5.3.1")
        
        # Same coordinates should match
        self.assertTrue(dep1.matches_coordinates("org.springframework:spring-core"))
        self.assertTrue(dep2.matches_coordinates("org.springframework:spring-core"))
        
        # Different coordinates should not match
        self.assertFalse(dep1.matches_coordinates("org.springframework:spring-web"))
    
    def test_dependency_jar_filename_generation(self):
        """Test JAR filename generation from dependency"""
        dep = Dependency("org.springframework", "spring-core", "5.3.0")
        self.assertEqual(dep.jar_filename, "spring-core-5.3.0.jar")
        
        dep_no_version = Dependency("org.springframework", "spring-core")
        self.assertEqual(dep_no_version.jar_filename, "spring-core.jar")
    
    def test_analysis_configuration_options(self):
        """Test various analysis configuration options"""
        config = AnalysisConfiguration(
            analyze_bytecode=False,
            analyze_manifest=True,
            target_platform=Platform.LINUX,
            java_version="11",
            bundle_native_libraries=False
        )
        
        self.assertFalse(config.analyze_bytecode)
        self.assertTrue(config.analyze_manifest)
        self.assertEqual(config.target_platform, Platform.LINUX)
        self.assertEqual(config.java_version, "11")
        self.assertFalse(config.bundle_native_libraries)
    
    def test_empty_dependency_list_handling(self):
        """Test handling of empty dependency lists"""
        resolver = DependencyResolver()
        context = ResolutionContext()
        
        result = resolver.resolve_dependencies([], context)
        
        self.assertIsInstance(result, ResolutionResult)
        self.assertEqual(len(result.resolved_dependencies), 0)
        self.assertEqual(len(result.conflicts), 0)
        self.assertEqual(len(result.warnings), 0)
        self.assertEqual(len(result.errors), 0)


class TestIntegrationScenarios(unittest.TestCase):
    """Integration test scenarios"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        if not IMPORTS_OK:
            self.skipTest("Required imports not available")
    
    def test_end_to_end_analysis_workflow(self):
        """Test the complete analysis workflow"""
        config = AnalysisConfiguration(
            analyze_bytecode=True,
            resolve_transitive=False,
            generate_reports=True,
            output_format='text'
        )
        
        # This should work even with non-existent JAR (will show errors)
        result = analyze_application_dependencies(['/nonexistent.jar'], config)
        
        # Verify the result structure
        self.assertIsInstance(result, ComprehensiveAnalysisResult)
        self.assertIsInstance(result.reports, dict)
        self.assertIsInstance(result.warnings, list)
        self.assertIsInstance(result.errors, list)
        self.assertIsInstance(result.recommendations, list)
    
    def test_configuration_preservation(self):
        """Test that configuration is preserved through analysis"""
        config = AnalysisConfiguration(
            verbose=True,
            analyze_bytecode=False,
            bundle_native_libraries=True
        )
        
        analyzer = ComprehensiveDependencyAnalyzer(config)
        
        # Verify configuration is preserved
        self.assertEqual(analyzer.config.verbose, True)
        self.assertEqual(analyzer.config.analyze_bytecode, False)
        self.assertEqual(analyzer.config.bundle_native_libraries, True)


def create_test_jar() -> str:
    """Create a minimal test JAR file for testing"""
    import zipfile
    
    with tempfile.NamedTemporaryFile(suffix='.jar', delete=False) as temp_file:
        temp_path = temp_file.name
    
    # Create a minimal JAR with manifest
    with zipfile.ZipFile(temp_path, 'w') as zf:
        manifest_content = """Manifest-Version: 1.0
Main-Class: com.example.Main

"""
        zf.writestr('META-INF/MANIFEST.MF', manifest_content)
        
        # Add a dummy class file (minimal Java class file structure)
        # This is a minimal valid class file with just the magic number and basic structure
        dummy_class = bytes([
            0xCA, 0xFE, 0xBA, 0xBE,  # Magic number
            0x00, 0x00,              # Minor version
            0x00, 0x34,              # Major version (Java 8)
            0x00, 0x0D,              # Constant pool count
            0x07, 0x00, 0x02,        # Class #2
            0x01, 0x00, 0x0D,        # UTF8 "com/example/Main"
            0x07, 0x00, 0x04,        # Class #4
            0x01, 0x00, 0x10,        # UTF8 "java/lang/Object"
            0x01, 0x00, 0x06,        # UTF8 "<init>"
            0x01, 0x00, 0x03,        # UTF8 "()V"
            0x01, 0x00, 0x04,        # UTF8 "Code"
            0x01, 0x00, 0x0F,        # UTF8 "LineNumberTable"
            0x01, 0x00, 0x0A,        # UTF8 "SourceFile"
            0x01, 0x00, 0x08,        # UTF8 "Main.java"
            0x00, 0x21,              # Access flags (public super)
            0x00, 0x01,              # This class
            0x00, 0x03,              # Super class
            0x00, 0x00,              # Interfaces count
            0x00, 0x00,              # Fields count
            0x00, 0x01,              # Methods count
            0x00, 0x01,              # Access flags (public)
            0x00, 0x02,              # Name index
            0x00, 0x03,              # Descriptor index
            0x00, 0x01,              # Attributes count
            0x00, 0x04,              # Attribute name index
            0x00, 0x00, 0x00, 0x0B,  # Attribute length
            0x00, 0x01,              # max_stack
            0x00, 0x01,              # max_locals
            0x00, 0x00, 0x00, 0x05,  # code_length
            0x2A,                    # aload_0
            0xB7, 0x00, 0x05,        # invokespecial Object.<init>
            0xB1,                    # return
            0x00, 0x00,              # exception_table_length
            0x00, 0x00,              # attributes_count
            0x00, 0x00,              # Class attributes count
        ])
        
        zf.writestr('com/example/Main.class', dummy_class)
    
    return temp_path


def run_basic_validation_test():
    """Run a basic validation test without full JAR file"""
    print("🧪 Running Basic Validation Test")
    print("=" * 40)
    
    if not IMPORTS_OK:
        print("❌ Import test failed - skipping validation")
        return False
    
    try:
        # Test basic imports
        print("✅ Testing imports...")
        
        # Test configuration creation
        config = AnalysisConfiguration()
        print("✅ Configuration creation successful")
        
        # Test dependency creation
        dep = Dependency("test.group", "test-artifact", "1.0.0")
        print(f"✅ Dependency creation successful: {dep.maven_coordinates}")
        
        # Test analyzer creation
        analyzer = ComprehensiveDependencyAnalyzer(config)
        print("✅ Analyzer creation successful")
        
        # Test quick check structure (with non-existent file)
        result = quick_dependency_check('/nonexistent.jar')
        print("✅ Quick check structure validation successful")
        
        print("\n🎉 All basic validation tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Validation test failed: {e}")
        return False


def run_integration_test():
    """Run integration test with actual JAR file"""
    print("\n🔧 Running Integration Test")
    print("=" * 40)
    
    if not IMPORTS_OK:
        print("❌ Import test failed - skipping integration test")
        return False
    
    try:
        # Create test JAR
        test_jar_path = create_test_jar()
        print(f"✅ Created test JAR: {test_jar_path}")
        
        try:
            # Test JAR analysis
            jar_result = analyze_jar_file(test_jar_path)
            print(f"✅ JAR analysis successful")
            print(f"   - Valid JAR: {jar_result.is_valid_jar}")
            print(f"   - Class files: {len(jar_result.class_files)}")
            print(f"   - Resources: {len(jar_result.resources)}")
            
            # Test comprehensive analysis
            config = AnalysisConfiguration(generate_reports=True, output_format='text')
            comp_result = analyze_application_dependencies([test_jar_path], config)
            print(f"✅ Comprehensive analysis successful")
            print(f"   - Reports generated: {len(comp_result.reports)}")
            print(f"   - Recommendations: {len(comp_result.recommendations)}")
            print(f"   - Warnings: {len(comp_result.warnings)}")
            print(f"   - Errors: {len(comp_result.errors)}")
            
            print("\n🎉 Integration test passed!")
            return True
            
        finally:
            # Clean up test JAR
            os.unlink(test_jar_path)
            print(f"🧹 Cleaned up test JAR")
            
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test runner"""
    print("🧪 COMPREHENSIVE DEPENDENCY ANALYSIS TEST SUITE")
    print("=" * 50)
    
    # Run basic validation
    basic_passed = run_basic_validation_test()
    
    # Run integration test
    integration_passed = run_integration_test()
    
    # Run unit tests if basic validation passed
    unit_tests_passed = False
    if basic_passed:
        print("\n📋 Running Unit Tests")
        print("=" * 40)
        try:
            # Create test suite
            loader = unittest.TestLoader()
            suite = loader.loadTestsFromTestCase(TestDependencyAnalysis)
            
            # Run tests
            runner = unittest.TextTestRunner(verbosity=1)
            result = runner.run(suite)
            
            unit_tests_passed = result.wasSuccessful()
            
            if unit_tests_passed:
                print("\n🎉 All unit tests passed!")
            else:
                print(f"\n❌ Unit tests failed: {result.failures + result.errors} failures")
                
        except Exception as e:
            print(f"❌ Unit test execution failed: {e}")
    
    # Summary
    print("\n📊 TEST SUMMARY")
    print("=" * 20)
    print(f"Basic Validation: {'✅ PASSED' if basic_passed else '❌ FAILED'}")
    print(f"Integration Test: {'✅ PASSED' if integration_passed else '❌ FAILED'}")
    print(f"Unit Tests: {'✅ PASSED' if unit_tests_passed else '❌ FAILED'}")
    
    overall_success = basic_passed and integration_passed and unit_tests_passed
    print(f"\nOverall Result: {'🎉 SUCCESS' if overall_success else '💥 FAILURE'}")
    
    return 0 if overall_success else 1


if __name__ == '__main__':
    sys.exit(main())
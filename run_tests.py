#!/usr/bin/env python3
"""
Test runner for Personal Codex Agent

This script runs all tests and provides a comprehensive test report.
"""

import sys
import os
import subprocess
from pathlib import Path

def run_tests():
    """Run all tests and return results"""
    print("🧪 Running Personal Codex Agent Test Suite")
    print("=" * 50)
    
    # Add current directory to Python path
    sys.path.insert(0, str(Path.cwd()))
    
    # Test files to run
    test_files = [
        "tests/test_config.py",
        "tests/test_mock_llm.py", 
        "tests/test_document_processor.py",
        "tests/test_embeddings.py",
        "tests/test_agent.py"
    ]
    
    results = {}
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    
    for test_file in test_files:
        if not Path(test_file).exists():
            print(f"❌ Test file not found: {test_file}")
            continue
            
        print(f"\n📋 Running {test_file}...")
        print("-" * 30)
        
        try:
            # Run pytest on individual test file
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                test_file, 
                "-v", 
                "--tb=short"
            ], capture_output=True, text=True, cwd=Path.cwd())
            
            # Parse results
            output_lines = result.stdout.split('\n')
            test_summary = [line for line in output_lines if 'passed' in line or 'failed' in line or 'error' in line]
            
            if test_summary:
                print('\n'.join(test_summary))
            
            # Count tests
            for line in output_lines:
                if '::' in line and ('PASSED' in line or 'FAILED' in line or 'ERROR' in line):
                    total_tests += 1
                    if 'PASSED' in line:
                        passed_tests += 1
                    else:
                        failed_tests += 1
            
            results[test_file] = {
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
            
        except Exception as e:
            print(f"❌ Error running {test_file}: {e}")
            results[test_file] = {
                'returncode': 1,
                'stdout': '',
                'stderr': str(e)
            }
            failed_tests += 1
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    print(f"Total Tests: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {failed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "No tests run")
    
    # Overall result
    if failed_tests == 0:
        print("\n🎉 All tests passed!")
        return True
    else:
        print(f"\n⚠️  {failed_tests} test(s) failed")
        return False

def run_specific_test(test_name):
    """Run a specific test"""
    test_file = f"tests/test_{test_name}.py"
    if not Path(test_file).exists():
        print(f"❌ Test file not found: {test_file}")
        return False
    
    print(f"🧪 Running {test_file}...")
    result = subprocess.run([
        sys.executable, "-m", "pytest", 
        test_file, 
        "-v", 
        "--tb=long"
    ], cwd=Path.cwd())
    
    return result.returncode == 0

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Run specific test
        test_name = sys.argv[1]
        success = run_specific_test(test_name)
        sys.exit(0 if success else 1)
    else:
        # Run all tests
        success = run_tests()
        sys.exit(0 if success else 1)

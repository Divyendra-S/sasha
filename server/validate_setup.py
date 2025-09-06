#!/usr/bin/env python3
"""
Setup validation script for the Interview Bot.

This script validates that all required components are properly set up
and configured for running the interview bot with parallel information extraction.
"""

import os
import sys
import importlib
from pathlib import Path
from dotenv import load_dotenv


def check_file_structure():
    """Check that all required files exist."""
    print("\n📁 Checking File Structure...")
    
    required_files = [
        "bot.py",
        "interview_extractor.py",
        "test_mock_extraction.py",
        "test_extraction.py",
        "validate_setup.py",
        "requirements.txt",
        "README_INTERVIEW_BOT.md"
    ]
    
    missing_files = []
    for filename in required_files:
        if not Path(filename).exists():
            missing_files.append(filename)
            print(f"❌ Missing: {filename}")
        else:
            print(f"✅ Found: {filename}")
    
    if missing_files:
        print(f"\n⚠️  Missing {len(missing_files)} required files")
        return False
    
    print("✅ All required files present")
    return True


def check_environment_variables():
    """Check that required environment variables are set."""
    print("\n🔑 Checking Environment Variables...")
    
    # Load environment variables
    load_dotenv(override=True)
    
    required_vars = {
        "GROQ_API_KEY": "Speech-to-Text and Text-to-Speech service",
        "GOOGLE_API_KEY": "Gemini LLM for conversation and extraction"
    }
    
    missing_vars = []
    for var_name, description in required_vars.items():
        value = os.getenv(var_name)
        if not value:
            missing_vars.append((var_name, description))
            print(f"❌ Missing: {var_name} ({description})")
        else:
            # Show first few and last few characters for security
            masked_value = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
            print(f"✅ Found: {var_name} = {masked_value}")
    
    if missing_vars:
        print(f"\n⚠️  Missing {len(missing_vars)} required environment variables")
        print("\nPlease create a .env file with the following variables:")
        for var_name, description in missing_vars:
            print(f"   {var_name}=your_{var_name.lower()}_here  # {description}")
        return False
    
    print("✅ All required environment variables are set")
    return True


def check_python_dependencies():
    """Check that required Python packages are installed."""
    print("\n📦 Checking Python Dependencies...")
    
    required_packages = [
        ("pipecat", "Core pipecat framework"),
        ("loguru", "Logging"),
        ("python-dotenv", "Environment variable loading"),
        ("asyncio", "Async support (built-in)"),
        ("json", "JSON parsing (built-in)"),
        ("dataclasses", "Data structures (built-in)"),
        ("typing", "Type hints (built-in)"),
    ]
    
    missing_packages = []
    
    for package_name, description in required_packages:
        try:
            if package_name in ["asyncio", "json", "dataclasses", "typing"]:
                # Built-in packages
                importlib.import_module(package_name)
            else:
                # External packages - handle special cases
                if package_name == "python-dotenv":
                    importlib.import_module("dotenv")
                else:
                    importlib.import_module(package_name.replace("-", "_"))
            print(f"✅ Found: {package_name} ({description})")
        except ImportError:
            missing_packages.append((package_name, description))
            print(f"❌ Missing: {package_name} ({description})")
    
    if missing_packages:
        print(f"\n⚠️  Missing {len(missing_packages)} required packages")
        print("\nTo install missing packages, run:")
        print("   pip install -r requirements.txt")
        return False
    
    print("✅ All required dependencies are available")
    return True


def check_imports():
    """Check that custom modules can be imported."""
    print("\n🔌 Checking Module Imports...")
    
    try:
        # Test importing our custom modules
        sys.path.insert(0, os.getcwd())
        
        from interview_extractor import InterviewData, InterviewExtractor, InterviewFlowManager
        print("✅ Successfully imported interview_extractor components")
        
        # Test basic functionality
        data = InterviewData()
        print(f"✅ InterviewData initialized: {len(data.get_missing_fields())} fields to collect")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def check_pipecat_components():
    """Check that required Pipecat components are available."""
    print("\n🔧 Checking Pipecat Components...")
    
    pipecat_imports = [
        ("pipecat.pipeline.parallel_pipeline", "ParallelPipeline"),
        ("pipecat.pipeline.pipeline", "Pipeline"),
        ("pipecat.processors.frame_processor", "FrameProcessor"),
        ("pipecat.frames.frames", "TextFrame"),
        ("pipecat.services.openai.llm", "OpenAILLMService"),
        ("pipecat.services.groq.stt", "GroqSTTService"),
        ("pipecat.services.groq.tts", "GroqTTSService"),
    ]
    
    missing_components = []
    
    for module_name, component_name in pipecat_imports:
        try:
            module = importlib.import_module(module_name)
            if hasattr(module, component_name):
                print(f"✅ Found: {module_name}.{component_name}")
            else:
                missing_components.append(f"{module_name}.{component_name}")
                print(f"❌ Missing component: {module_name}.{component_name}")
        except ImportError:
            missing_components.append(f"{module_name}.{component_name}")
            print(f"❌ Cannot import: {module_name}.{component_name}")
    
    if missing_components:
        print(f"\n⚠️  Missing {len(missing_components)} Pipecat components")
        print("Make sure you have the correct pipecat version installed:")
        print("   pip install 'pipecat-ai[webrtc,silero,groq,openai,cartesia,runner]>=0.0.77'")
        return False
    
    print("✅ All required Pipecat components are available")
    return True


def test_basic_functionality():
    """Test basic functionality without API calls."""
    print("\n🧪 Testing Basic Functionality...")
    
    try:
        # Test InterviewData
        from interview_extractor import InterviewData, InterviewFlowManager
        
        data = InterviewData()
        original_missing = len(data.get_missing_fields())
        print(f"✅ InterviewData: {original_missing} fields to collect initially")
        
        # Test FlowManager
        manager = InterviewFlowManager(data)
        guidance = manager.get_guidance_message()
        if guidance:
            print(f"✅ FlowManager: Generated guidance message")
        else:
            print("⚠️  FlowManager: No guidance message generated")
        
        print("✅ Basic functionality tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False


def main():
    """Run all validation checks."""
    print("🔍 Interview Bot Setup Validation")
    print("=" * 50)
    
    checks = [
        ("File Structure", check_file_structure),
        ("Environment Variables", check_environment_variables),
        ("Python Dependencies", check_python_dependencies),
        ("Module Imports", check_imports),
        ("Pipecat Components", check_pipecat_components),
        ("Basic Functionality", test_basic_functionality),
    ]
    
    results = []
    
    for check_name, check_function in checks:
        try:
            result = check_function()
            results.append((check_name, result))
        except Exception as e:
            print(f"❌ {check_name} check failed with error: {e}")
            results.append((check_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("VALIDATION SUMMARY")
    print("=" * 50)
    
    passed = 0
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{check_name}: {status}")
        if result:
            passed += 1
    
    total = len(results)
    print(f"\nOverall: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 All validation checks passed!")
        print("\nYou can now run the interview bot:")
        print("   python bot.py")
        print("\nRun tests:")
        print("   python test_mock_extraction.py  # No API keys required")
        print("   python test_extraction.py       # Requires API keys")
        
    else:
        print(f"\n⚠️  {total - passed} validation checks failed.")
        print("Please fix the issues above before running the bot.")
        
        if not any(result for name, result in results if name == "Environment Variables"):
            print("\n💡 Tip: Create a .env file with your API keys:")
            print("   GROQ_API_KEY=your_groq_key")
            print("   GOOGLE_API_KEY=your_gemini_key")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
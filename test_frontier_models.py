"""
Test script for Frontier models integration.
Verifies both Ollama and Anthropic provider configurations.

Usage:
    python test_frontier_models.py [provider]
    
    provider: "ollama" or "anthropic" (defaults to environment variable)
"""

import os
import sys
import requests
import json

BASE_URL = "http://localhost:8001"

def test_health(provider_name=None):
    """Test LLM provider health endpoint."""
    print(f"\n{'='*60}")
    print(f"Testing LLM Provider Health")
    print(f"{'='*60}")
    
    try:
        response = requests.get(f"{BASE_URL}/ollama/health", timeout=5)
        response.raise_for_status()
        data = response.json()
        
        print(f"\n✓ Provider: {data.get('provider', 'unknown')}")
        print(f"✓ Connected: {data.get('connected', False)}")
        
        if data.get('provider') == 'anthropic':
            print(f"✓ Model: {data.get('model', 'unknown')}")
        else:
            print(f"✓ Generator Model: {data.get('generator_model', 'unknown')}")
            print(f"✓ Critic Model: {data.get('critic_model', 'unknown')}")
        
        if 'error' in data:
            print(f"\n⚠ Error: {data['error']}")
            return False
        
        return data.get('connected', False)
        
    except Exception as e:
        print(f"\n✗ Health check failed: {e}")
        return False

def test_models_list():
    """Test models list endpoint."""
    print(f"\n{'='*60}")
    print(f"Testing Models List")
    print(f"{'='*60}")
    
    try:
        response = requests.get(f"{BASE_URL}/ollama/models", timeout=5)
        response.raise_for_status()
        data = response.json()
        
        print(f"\n✓ Provider: {data.get('provider', 'unknown')}")
        print(f"✓ Model Count: {data.get('count', 0)}")
        
        models = data.get('models', [])
        if models:
            print(f"\nAvailable models:")
            for model in models[:10]:  # Show first 10
                print(f"  - {model}")
            if len(models) > 10:
                print(f"  ... and {len(models) - 10} more")
        
        if 'note' in data:
            print(f"\nNote: {data['note']}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Models list failed: {e}")
        return False

def test_generation():
    """Test simple text generation."""
    print(f"\n{'='*60}")
    print(f"Testing Text Generation")
    print(f"{'='*60}")
    
    prompt = "Describe a mystical forest in exactly two sentences."
    
    try:
        response = requests.post(
            f"{BASE_URL}/ollama/generate",
            json={"prompt": prompt},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        print(f"\n✓ Provider: {data.get('provider', 'unknown')}")
        print(f"✓ Model: {data.get('model', 'unknown')}")
        print(f"\nPrompt: {prompt}")
        print(f"\nResponse:")
        print(f"{data.get('output', '(no output)')}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Generation failed: {e}")
        return False

def test_archetype_analysis():
    """Test archetype analysis with the configured provider."""
    print(f"\n{'='*60}")
    print(f"Testing Archetype Analysis")
    print(f"{'='*60}")
    
    payload = {
        "character_name": "Test Character",
        "description": "A brave warrior who protects the innocent",
        "style": "Fantasy"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/call/mythos_archetype_analysis",
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        print(f"\n✓ Primary Archetype: {data.get('primary_archetype', 'unknown')}")
        print(f"✓ Secondary Archetype: {data.get('secondary_archetype', 'unknown')}")
        print(f"✓ Confidence (Primary): {data.get('confidence_primary', 0):.3f}")
        print(f"✓ Confidence (Secondary): {data.get('confidence_secondary', 0):.3f}")
        print(f"✓ Tension Score: {data.get('tension_score', 0):.3f}")
        
        if data.get('low_signal_fallback'):
            print(f"\n⚠ Used low signal fallback (random selection)")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Archetype analysis failed: {e}")
        return False

def print_summary(results):
    """Print test summary."""
    print(f"\n{'='*60}")
    print(f"Test Summary")
    print(f"{'='*60}")
    
    total = len(results)
    passed = sum(results.values())
    
    print(f"\nTests Run: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status} - {test_name}")
    
    if passed == total:
        print(f"\n🎉 All tests passed!")
        return True
    else:
        print(f"\n⚠ Some tests failed. Check configuration and logs.")
        return False

def main():
    """Run all tests."""
    provider = sys.argv[1] if len(sys.argv) > 1 else os.getenv("MYTHOS_LLM_PROVIDER", "ollama")
    
    print(f"{'='*60}")
    print(f"Mythos Frontier Models Test Suite")
    print(f"{'='*60}")
    print(f"\nTarget: {BASE_URL}")
    print(f"Expected Provider: {provider}")
    print(f"\nNOTE: Make sure backend is running:")
    print(f"  docker compose up -d")
    
    results = {}
    
    # Test 1: Health check
    results["Health Check"] = test_health(provider)
    
    # Test 2: Models list
    results["Models List"] = test_models_list()
    
    # Test 3: Simple generation
    results["Text Generation"] = test_generation()
    
    # Test 4: Archetype analysis (uses LLM for semantic scoring)
    results["Archetype Analysis"] = test_archetype_analysis()
    
    # Print summary
    all_passed = print_summary(results)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())

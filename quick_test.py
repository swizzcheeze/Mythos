#!/usr/bin/env python3
"""Quick embedding test with timeout"""
import requests
import sys

print("Testing lore creation with embedding...")
try:
    r = requests.post(
        'http://localhost:8001/call/mythos_create_lore_entry',
        json={'topic': 'Quick Test', 'content': 'Testing embedding', 'world': 'quick_test'},
        timeout=10
    )
    print(f"Status: {r.status_code}")
    data = r.json()
    print(f"Embedded: {data.get('embedded')}")
    print(f"Entry ID: {data.get('entry_id')}")
    
    # Wait for background embedding to complete
    import time
    print("\nWaiting 2 seconds for embedding to complete...")
    time.sleep(2)
    
    # Try search
    print("\nTesting semantic search...")
    r2 = requests.post(
        'http://localhost:8001/call/mythos_semantic_lore_search',
        json={'query': 'testing', 'top_k': 3, 'world': 'quick_test'},
        timeout=10
    )
    print(f"Search status: {r2.status_code}")
    results = r2.json().get('results', [])
    print(f"Found {len(results)} results")
    
except requests.Timeout:
    print("ERROR: Request timed out!")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)

print("\n✓ Quick test passed!")

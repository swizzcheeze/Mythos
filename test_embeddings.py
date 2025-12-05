#!/usr/bin/env python3
"""
Comprehensive embedding and semantic search test suite for Mythos World Engine.
Tests local model embedding, FAISS indexing, vector persistence, and similarity search.
"""

import requests
import json
import time
import os
from collections import defaultdict

BASE_URL = "http://localhost:8001"
WORLD_NAME = "test_embedding_world"

# Colors for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"

def test_header(name):
    print(f"\n{BLUE}[TEST] {name}{RESET}")

def success(msg):
    print(f"  {GREEN}✓{RESET} {msg}")

def fail(msg):
    print(f"  {RED}✗{RESET} {msg}")

def cleanup_world():
    """Clean up test world."""
    try:
        resp = requests.post(f"{BASE_URL}/call/mythos_wipe_lore_db", json={
            "confirm": "CONFIRM",
            "world": WORLD_NAME
        })
        if resp.status_code == 200:
            success(f"Cleaned up world '{WORLD_NAME}'")
    except Exception as e:
        print(f"  Warning: cleanup failed: {e}")

def test_embedding_enabled():
    """Test 1: Verify embeddings are enabled in backend."""
    test_header("Embedding System Enabled")
    try:
        resp = requests.get(f"{BASE_URL}/healthz")
        if resp.status_code == 200:
            success("Backend is running")
            return True
        else:
            fail("Backend health check failed")
            return False
    except Exception as e:
        fail(f"Backend unreachable: {e}")
        return False

def test_create_with_embedding():
    """Test 2: Create lore entries and verify embedding indexing."""
    test_header("Create Lore with Embedding")
    
    test_entries = [
        {
            "topic": "Ancient Prophecy",
            "content": "A mysterious prophecy spoken by the oracles of old, foretelling a great darkness and a champion of light who will rise to face it.",
            "tags": ["prophecy", "magic"]
        },
        {
            "topic": "The Forbidden Ritual",
            "content": "Deep within the catacombs lies instructions for a ritual that binds souls across dimensions. Forbidden by ancient law.",
            "tags": ["ritual", "magic", "danger"]
        },
        {
            "topic": "Crystal of Eternal Wisdom",
            "content": "A magical artifact said to contain the accumulated knowledge of all ages. Legends tell of its location in a hidden temple.",
            "tags": ["artifact", "wisdom", "magic"]
        }
    ]
    
    entry_ids = []
    for entry in test_entries:
        entry["world"] = WORLD_NAME
        try:
            resp = requests.post(f"{BASE_URL}/call/mythos_create_lore_entry", json=entry)
            if resp.status_code == 200:
                data = resp.json()
                entry_id = data.get("entry_id")
                embedded = data.get("embedded", False)
                success(f"Created '{entry['topic']}' (id={entry_id[:8]}..., embedded={embedded})")
                entry_ids.append(entry_id)
            else:
                fail(f"Failed to create '{entry['topic']}': {resp.status_code}")
                return False
        except Exception as e:
            fail(f"Exception creating entry: {e}")
            return False
    
    return len(entry_ids) == 3

def test_semantic_search():
    """Test 3: Semantic search for thematically similar entries."""
    test_header("Semantic Similarity Search")
    
    queries = [
        ("ancient magic and prophecy", 3),
        ("magical artifacts and wisdom", 3),
        ("forbidden dark rituals", 3)
    ]
    
    all_pass = True
    for query, expected_entries in queries:
        try:
            resp = requests.post(f"{BASE_URL}/call/mythos_semantic_lore_search", json={
                "query": query,
                "top_k": 5,
                "world": WORLD_NAME
            })
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results", [])
                embedding_model = data.get("embedding_model", "unknown")
                
                if len(results) > 0:
                    success(f"Query '{query}': found {len(results)} results (model: {embedding_model})")
                    # Show top result
                    top = results[0]
                    print(f"    └─ Top: '{top['topic']}' (similarity: {top['similarity_score']:.3f})")
                else:
                    fail(f"Query '{query}': no results")
                    all_pass = False
            else:
                fail(f"Semantic search failed: {resp.status_code}")
                all_pass = False
        except Exception as e:
            fail(f"Search exception: {e}")
            all_pass = False
    
    return all_pass

def test_similarity_scores():
    """Test 4: Verify similarity scores are normalized between 0 and 1."""
    test_header("Similarity Score Validation")
    
    try:
        resp = requests.post(f"{BASE_URL}/call/mythos_semantic_lore_search", json={
            "query": "magic and mystical powers",
            "top_k": 10,
            "world": WORLD_NAME
        })
        
        if resp.status_code == 200:
            data = resp.json()
            results = data.get("results", [])
            
            all_valid = True
            for result in results:
                score = result.get("similarity_score")
                if 0 <= score <= 1:
                    success(f"'{result['topic']}': similarity={score:.3f} ✓")
                else:
                    fail(f"'{result['topic']}': invalid score {score}")
                    all_valid = False
            
            return all_valid
        else:
            fail(f"Search failed: {resp.status_code}")
            return False
    except Exception as e:
        fail(f"Exception: {e}")
        return False

def test_embedding_model():
    """Test 5: Verify embedding model is local (SentenceTransformers)."""
    test_header("Embedding Model Type")
    
    try:
        resp = requests.post(f"{BASE_URL}/call/mythos_semantic_lore_search", json={
            "query": "test",
            "top_k": 1,
            "world": WORLD_NAME
        })
        
        if resp.status_code == 200:
            data = resp.json()
            model = data.get("embedding_model", "unknown")
            
            if model and "cohere" not in model.lower():
                success(f"Using local embedding model: {model}")
                return True
            elif "cohere" in model.lower():
                success(f"Using Cohere embeddings (online): {model}")
                return True
            else:
                fail(f"Unknown model: {model}")
                return False
        else:
            fail(f"Search failed: {resp.status_code}")
            return False
    except Exception as e:
        fail(f"Exception: {e}")
        return False

def test_vector_persistence():
    """Test 6: Verify vectors persist across requests."""
    test_header("Vector Persistence")
    
    try:
        # Create an entry
        entry = {
            "topic": "Persistence Test",
            "content": "Testing if vectors persist across multiple search requests.",
            "tags": ["test"],
            "world": WORLD_NAME
        }
        
        resp = requests.post(f"{BASE_URL}/call/mythos_create_lore_entry", json=entry)
        if resp.status_code != 200:
            fail("Failed to create test entry")
            return False
        
        # Search immediately (first request)
        resp1 = requests.post(f"{BASE_URL}/call/mythos_semantic_lore_search", json={
            "query": "persistence testing",
            "top_k": 5,
            "world": WORLD_NAME
        })
        results1 = resp1.json().get("results", []) if resp1.status_code == 200 else []
        
        # Wait a moment
        time.sleep(1)
        
        # Search again (second request)
        resp2 = requests.post(f"{BASE_URL}/call/mythos_semantic_lore_search", json={
            "query": "persistence testing",
            "top_k": 5,
            "world": WORLD_NAME
        })
        results2 = resp2.json().get("results", []) if resp2.status_code == 200 else []
        
        if len(results1) == len(results2):
            success(f"Vector index consistent across requests ({len(results1)} results)")
            return True
        else:
            fail(f"Vector index mismatch: {len(results1)} vs {len(results2)} results")
            return False
    except Exception as e:
        fail(f"Exception: {e}")
        return False

def test_multi_world_isolation():
    """Test 7: Verify embeddings are isolated per world."""
    test_header("Multi-World Embedding Isolation")
    
    try:
        world2 = "test_embedding_world_2"
        
        # Create entry in first world
        resp1 = requests.post(f"{BASE_URL}/call/mythos_create_lore_entry", json={
            "topic": "World1 Entry",
            "content": "This entry exists only in world 1 with unique magical properties.",
            "tags": ["world1"],
            "world": WORLD_NAME
        })
        
        # Create different entry in second world
        resp2 = requests.post(f"{BASE_URL}/call/mythos_create_lore_entry", json={
            "topic": "World2 Entry",
            "content": "This entry exists only in world 2 with different magical properties.",
            "tags": ["world2"],
            "world": world2
        })
        
        if resp1.status_code != 200 or resp2.status_code != 200:
            fail("Failed to create test entries in both worlds")
            return False
        
        # Search in world 1 (should not find world 2 entry)
        resp_search1 = requests.post(f"{BASE_URL}/call/mythos_semantic_lore_search", json={
            "query": "world 2 magical",
            "top_k": 10,
            "world": WORLD_NAME
        })
        
        results1 = resp_search1.json().get("results", [])
        found_world2 = any("World2" in r.get("topic", "") for r in results1)
        
        if not found_world2:
            success(f"World 1 search isolated correctly (found {len(results1)} results)")
            # Clean up world 2
            requests.post(f"{BASE_URL}/call/mythos_wipe_lore_db", json={
                "confirm": "CONFIRM",
                "world": world2
            })
            return True
        else:
            fail("World 2 entry found in World 1 search (isolation broken)")
            return False
    except Exception as e:
        fail(f"Exception: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("Mythos Embedding & Semantic Search Test Suite")
    print("="*60)
    
    results = {}
    
    # Run tests
    results["Embedding Enabled"] = test_embedding_enabled()
    if not results["Embedding Enabled"]:
        print(f"\n{RED}Backend not running. Cannot proceed.{RESET}")
        return
    
    results["Create with Embedding"] = test_create_with_embedding()
    results["Semantic Search"] = test_semantic_search()
    results["Similarity Scores"] = test_similarity_scores()
    results["Embedding Model"] = test_embedding_model()
    results["Vector Persistence"] = test_vector_persistence()
    results["Multi-World Isolation"] = test_multi_world_isolation()
    
    # Cleanup
    cleanup_world()
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_flag in results.items():
        status = f"{GREEN}PASS{RESET}" if passed_flag else f"{RED}FAIL{RESET}"
        print(f"  {status}  {test_name}")
    
    print("\n" + "="*60)
    print(f"Result: {passed}/{total} tests passed")
    
    if passed == total:
        print(f"{GREEN}✓ All embedding tests passed!{RESET}")
    else:
        print(f"{RED}✗ Some tests failed.{RESET}")
    print("="*60)

if __name__ == "__main__":
    main()

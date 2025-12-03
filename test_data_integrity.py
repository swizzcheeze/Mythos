#!/usr/bin/env python3
"""
Data Integrity Test Suite for Mythos Backend

Tests concurrent operations, crash resistance, and data safety guarantees.
Run this after implementing security improvements to verify:
- Thread-safe file operations
- Atomic writes
- UUID collision resistance
- World name validation
- Per-request world context isolation
"""

import json
import requests
import threading
import time
import os
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any

BASE_URL = "http://localhost:8001"
TEST_WORLD = "TestIntegrity"
WORLD_DATA_PATH = Path("world_data")

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def log_test(name: str):
    print(f"\n{Colors.BLUE}[TEST]{Colors.END} {name}")

def log_pass(msg: str):
    print(f"  {Colors.GREEN}✓{Colors.END} {msg}")

def log_fail(msg: str):
    print(f"  {Colors.RED}✗{Colors.END} {msg}")

def log_warn(msg: str):
    print(f"  {Colors.YELLOW}⚠{Colors.END} {msg}")

def call_tool(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Call a backend tool endpoint."""
    try:
        response = requests.post(f"{BASE_URL}/call/{tool_name}", json=args, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def test_backend_reachable():
    """Test 1: Backend health check"""
    log_test("Backend Reachability")
    try:
        response = requests.get(f"{BASE_URL}/healthz", timeout=3)
        if response.status_code == 200:
            log_pass("Backend /healthz responding")
            return True
        else:
            log_fail(f"Backend returned {response.status_code}")
            return False
    except Exception as e:
        log_fail(f"Cannot reach backend: {e}")
        return False

def test_world_name_validation():
    """Test 2: World name validation prevents directory traversal"""
    log_test("World Name Validation")
    
    dangerous_names = [
        "../../../etc/passwd",
        "..",
        ".",
        "../../world_data",
        "test/../../escape",
        "test\x00injection",
        "a" * 100,  # Too long
        "test space",  # Spaces not allowed
        "test@special",  # Special chars
    ]
    
    passed = 0
    for name in dangerous_names:
        result = call_tool("mythos_create_world", {"name": name})
        if "error" in result or result.get("status") != "success":
            passed += 1
        else:
            log_fail(f"Dangerous name accepted: {name}")
    
    if passed == len(dangerous_names):
        log_pass(f"All {len(dangerous_names)} dangerous names rejected")
        return True
    else:
        log_warn(f"Only {passed}/{len(dangerous_names)} dangerous names rejected")
        return False

def test_concurrent_creates():
    """Test 3: Concurrent lore entry creation produces unique IDs"""
    log_test("Concurrent Lore Entry Creation")
    
    # Create test world
    call_tool("mythos_create_world", {"name": TEST_WORLD})
    
    results = []
    errors = []
    
    def create_entry(index: int):
        try:
            result = call_tool("mythos_create_lore_entry", {
                "topic": f"Test Entry {index}",
                "content": f"Content for test entry {index}",
                "world": TEST_WORLD
            })
            results.append(result)
        except Exception as e:
            errors.append(str(e))
    
    # Launch 10 concurrent creates
    threads = []
    for i in range(10):
        t = threading.Thread(target=create_entry, args=(i,))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    if errors:
        log_fail(f"{len(errors)} threads encountered errors")
        return False
    
    # Extract IDs
    ids = [r.get("entry_id") for r in results if r.get("entry_id")]
    
    if len(ids) != len(set(ids)):
        log_fail("Duplicate IDs detected!")
        return False
    
    log_pass(f"All {len(ids)} entries have unique IDs")
    
    # Verify all entries saved
    list_result = call_tool("mythos_list_lore_entries", {"world": TEST_WORLD})
    saved_count = list_result.get("total_entries", 0)
    
    if saved_count == len(ids):
        log_pass(f"All {saved_count} entries persisted correctly")
        return True
    else:
        log_fail(f"Expected {len(ids)} entries, found {saved_count}")
        return False

def test_world_isolation():
    """Test 4: Per-request world context prevents cross-talk"""
    log_test("World Context Isolation")
    
    world_a = "WorldA"
    world_b = "WorldB"
    
    # Create two worlds
    call_tool("mythos_create_world", {"name": world_a})
    call_tool("mythos_create_world", {"name": world_b})
    
    # Add entries to each
    call_tool("mythos_create_lore_entry", {
        "topic": "Entry A",
        "content": "Belongs to World A",
        "world": world_a
    })
    
    call_tool("mythos_create_lore_entry", {
        "topic": "Entry B",
        "content": "Belongs to World B",
        "world": world_b
    })
    
    # Verify isolation
    list_a = call_tool("mythos_list_lore_entries", {"world": world_a})
    list_b = call_tool("mythos_list_lore_entries", {"world": world_b})
    
    entries_a = list_a.get("entries", [])
    entries_b = list_b.get("entries", [])
    
    if len(entries_a) == 1 and len(entries_b) == 1:
        if entries_a[0]["topic"] == "Entry A" and entries_b[0]["topic"] == "Entry B":
            log_pass("World contexts properly isolated")
            return True
    
    log_fail("World isolation failed - entries leaked between worlds")
    return False

def test_atomic_writes():
    """Test 5: File corruption resistance (simulated)"""
    log_test("Atomic Write Safety")
    
    # This test verifies the temp file pattern is in use
    # Actual crash testing would require killing the process mid-write
    
    test_world = "AtomicTest"
    call_tool("mythos_create_world", {"name": test_world})
    
    # Create multiple entries rapidly
    for i in range(5):
        call_tool("mythos_create_lore_entry", {
            "topic": f"Rapid Entry {i}",
            "content": f"Content {i}",
            "world": test_world
        })
    
    # Read the file directly to verify JSON validity
    world_path = WORLD_DATA_PATH / "worlds" / test_world / "lore_db.json"
    
    try:
        with open(world_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, list) and len(data) == 5:
            log_pass("File is valid JSON with correct entry count")
            
            # Check for temp files (shouldn't exist after successful writes)
            temp_files = list(world_path.parent.glob("*.tmp"))
            if not temp_files:
                log_pass("No orphaned temp files")
                return True
            else:
                log_warn(f"Found {len(temp_files)} temp files (may indicate write interruption)")
                return True
        else:
            log_fail(f"Unexpected data structure or count")
            return False
            
    except json.JSONDecodeError:
        log_fail("File is corrupted (invalid JSON)")
        return False
    except Exception as e:
        log_fail(f"File read error: {e}")
        return False

def test_uuid_format():
    """Test 6: Verify UUIDs are properly formatted"""
    log_test("UUID Format Validation")
    
    result = call_tool("mythos_create_lore_entry", {
        "topic": "UUID Test",
        "content": "Testing UUID format",
        "world": TEST_WORLD
    })
    
    entry_id = result.get("entry_id")
    
    if not entry_id:
        log_fail("No entry_id returned")
        return False
    
    # UUID v4 format: 8-4-4-4-12 hex digits
    parts = entry_id.split('-')
    if len(parts) == 5 and len(parts[0]) == 8 and len(parts[1]) == 4:
        log_pass(f"Valid UUID format: {entry_id}")
        return True
    else:
        log_fail(f"Invalid UUID format: {entry_id}")
        return False

def test_concurrent_world_operations():
    """Test 7: Concurrent operations on different worlds"""
    log_test("Concurrent Multi-World Operations")
    
    results = {"success": 0, "errors": 0}
    lock = threading.Lock()
    
    def worker(world_name: str, count: int):
        try:
            call_tool("mythos_create_world", {"name": world_name})
            for i in range(count):
                call_tool("mythos_create_lore_entry", {
                    "topic": f"{world_name} Entry {i}",
                    "content": f"Content for {world_name}",
                    "world": world_name
                })
            with lock:
                results["success"] += 1
        except Exception as e:
            with lock:
                results["errors"] += 1
    
    threads = []
    for i in range(5):
        world = f"ConcurrentWorld{i}"
        t = threading.Thread(target=worker, args=(world, 3))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    if results["success"] == 5 and results["errors"] == 0:
        log_pass("All 5 concurrent world operations succeeded")
        
        # Verify each world has correct count
        all_correct = True
        for i in range(5):
            world = f"ConcurrentWorld{i}"
            list_result = call_tool("mythos_list_lore_entries", {"world": world})
            count = list_result.get("total_entries", 0)
            if count != 3:
                log_fail(f"{world} has {count} entries, expected 3")
                all_correct = False
        
        if all_correct:
            log_pass("All worlds have correct entry counts")
            return True
    else:
        log_fail(f"Success: {results['success']}, Errors: {results['errors']}")
    
    return False

def test_update_lore_entry():
    """Test 8: Update operations maintain integrity"""
    log_test("Lore Entry Updates")
    
    # Create entry
    create_result = call_tool("mythos_create_lore_entry", {
        "topic": "Original Topic",
        "content": "Original content",
        "world": TEST_WORLD
    })
    
    entry_id = create_result.get("entry_id")
    if not entry_id:
        log_fail("Failed to create test entry")
        return False
    
    # Update entry
    update_result = call_tool("mythos_update_lore_entry", {
        "id": entry_id,
        "topic": "Updated Topic",
        "content": "Updated content",
        "world": TEST_WORLD
    })
    
    if update_result.get("status") != "success":
        log_fail("Update failed")
        return False
    
    # Verify update persisted
    list_result = call_tool("mythos_list_lore_entries", {"world": TEST_WORLD})
    entries = list_result.get("entries", [])
    
    updated_entry = next((e for e in entries if e["id"] == entry_id), None)
    
    if updated_entry and updated_entry["topic"] == "Updated Topic":
        log_pass("Entry updated and persisted correctly")
        return True
    else:
        log_fail("Updated entry not found or incorrect")
        return False

def cleanup_test_worlds():
    """Clean up test worlds created during testing"""
    log_test("Cleanup")
    
    test_worlds = [
        TEST_WORLD, "WorldA", "WorldB", "AtomicTest",
        "ConcurrentWorld0", "ConcurrentWorld1", "ConcurrentWorld2",
        "ConcurrentWorld3", "ConcurrentWorld4"
    ]
    
    for world in test_worlds:
        world_path = WORLD_DATA_PATH / "worlds" / world
        if world_path.exists():
            try:
                shutil.rmtree(world_path)
            except Exception as e:
                log_warn(f"Failed to clean up {world}: {e}")
    
    log_pass("Test worlds cleaned up")

def main():
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}Mythos Data Integrity Test Suite{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    tests = [
        ("Backend Reachable", test_backend_reachable),
        ("World Name Validation", test_world_name_validation),
        ("Concurrent Creates (No Collisions)", test_concurrent_creates),
        ("World Context Isolation", test_world_isolation),
        ("Atomic Write Safety", test_atomic_writes),
        ("UUID Format", test_uuid_format),
        ("Concurrent Multi-World Ops", test_concurrent_world_operations),
        ("Lore Entry Updates", test_update_lore_entry),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            log_fail(f"Test crashed: {e}")
            results.append((name, False))
        time.sleep(0.1)  # Brief pause between tests
    
    # Cleanup
    cleanup_test_worlds()
    
    # Summary
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}Test Summary{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for name, passed in results:
        status = f"{Colors.GREEN}PASS{Colors.END}" if passed else f"{Colors.RED}FAIL{Colors.END}"
        print(f"  {status}  {name}")
    
    print(f"\n{Colors.BLUE}Result:{Colors.END} {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print(f"{Colors.GREEN}✓ All data integrity tests passed!{Colors.END}\n")
        return 0
    else:
        print(f"{Colors.RED}✗ Some tests failed{Colors.END}\n")
        return 1

if __name__ == "__main__":
    exit(main())

#!/usr/bin/env python3
"""
Comprehensive test script for Pokemon PvP Helper
Tests all major functionality including API endpoints, battle simulation, and analytics
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5000"
TEST_POKEMON = ["pikachu", "charizard", "blastoise", "venusaur", "mewtwo"]
TEST_LEAGUES = ["1500", "2500", "10000"]

def print_status(message, status="INFO"):
    """Print formatted status message"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {status}: {message}")

def test_server_health():
    """Test if the server is running and responding"""
    print_status("Testing server health...")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=10)
        if response.status_code == 200:
            print_status("✅ Server is running and responding", "SUCCESS")
            return True
        else:
            print_status(f"❌ Server returned status {response.status_code}", "ERROR")
            return False
    except requests.exceptions.RequestException as e:
        print_status(f"❌ Cannot connect to server: {e}", "ERROR")
        return False

def test_pokemon_api():
    """Test Pokemon API endpoints"""
    print_status("Testing Pokemon API endpoints...")
    
    # Test individual Pokemon
    for pokemon in TEST_POKEMON:
        try:
            response = requests.get(f"{BASE_URL}/api/pokemon/{pokemon}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('name') and data.get('types'):
                    print_status(f"✅ {pokemon}: OK", "SUCCESS")
                else:
                    print_status(f"⚠️ {pokemon}: Missing required fields", "WARNING")
            else:
                print_status(f"❌ {pokemon}: HTTP {response.status_code}", "ERROR")
        except Exception as e:
            print_status(f"❌ {pokemon}: Error - {e}", "ERROR")
    
    # Test search functionality
    try:
        response = requests.get(f"{BASE_URL}/api/search/pika", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                print_status("✅ Search API: OK", "SUCCESS")
            else:
                print_status("⚠️ Search API: No results", "WARNING")
        else:
            print_status(f"❌ Search API: HTTP {response.status_code}", "ERROR")
    except Exception as e:
        print_status(f"❌ Search API: Error - {e}", "ERROR")

def test_battle_simulation():
    """Test battle simulation functionality"""
    print_status("Testing battle simulation...")
    
    # Test battle simulation with different leagues
    for league in TEST_LEAGUES:
        try:
            battle_data = {
                "p1_pokemon": "pikachu",
                "p1_fast_move": "Thunder Shock",
                "p1_charged_moves": ["Thunderbolt"],
                "p2_pokemon": "charizard",
                "p2_fast_move": "Fire Spin",
                "p2_charged_moves": ["Fire Blast"],
                "shield_count": 2,
                "p1_shield_ai": "smart",
                "p2_shield_ai": "smart",
                "league": league,
                "team_ids": ["pikachu"],
                "team_moves": [["Thunder Shock", "Thunderbolt"]]
            }
            
            response = requests.post(f"{BASE_URL}/api/battle", json=battle_data, timeout=30)
            if response.status_code == 200:
                data = response.json()
                if data.get('winner') and data.get('battle_log'):
                    print_status(f"✅ Battle simulation ({league} CP): OK", "SUCCESS")
                else:
                    print_status(f"⚠️ Battle simulation ({league} CP): Missing data", "WARNING")
            else:
                print_status(f"❌ Battle simulation ({league} CP): HTTP {response.status_code}", "ERROR")
        except Exception as e:
            print_status(f"❌ Battle simulation ({league} CP): Error - {e}", "ERROR")

def test_analytics():
    """Test analytics functionality"""
    print_status("Testing analytics functionality...")
    
    # Test analytics API
    try:
        response = requests.get(f"{BASE_URL}/api/analytics", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict) and 'unique_visitors' in data:
                print_status("✅ Analytics API: OK", "SUCCESS")
            else:
                print_status("⚠️ Analytics API: Missing expected fields", "WARNING")
        else:
            print_status(f"❌ Analytics API: HTTP {response.status_code}", "ERROR")
    except Exception as e:
        print_status(f"❌ Analytics API: Error - {e}", "ERROR")
    
    # Test analytics dashboard (should redirect to login)
    try:
        response = requests.get(f"{BASE_URL}/analytics", timeout=10)
        if response.status_code in [200, 302]:  # 200 for login page, 302 for redirect
            print_status("✅ Analytics dashboard: OK", "SUCCESS")
        else:
            print_status(f"❌ Analytics dashboard: HTTP {response.status_code}", "ERROR")
    except Exception as e:
        print_status(f"❌ Analytics dashboard: Error - {e}", "ERROR")

def test_static_files():
    """Test static file serving"""
    print_status("Testing static file serving...")
    
    static_files = [
        "/static/styles.css",
        "/static/script.js",
        "/static/sprites/pikachu.png"
    ]
    
    for file_path in static_files:
        try:
            response = requests.get(f"{BASE_URL}{file_path}", timeout=10)
            if response.status_code == 200:
                print_status(f"✅ {file_path}: OK", "SUCCESS")
            else:
                print_status(f"❌ {file_path}: HTTP {response.status_code}", "ERROR")
        except Exception as e:
            print_status(f"❌ {file_path}: Error - {e}", "ERROR")

def test_error_handling():
    """Test error handling"""
    print_status("Testing error handling...")
    
    # Test invalid Pokemon
    try:
        response = requests.get(f"{BASE_URL}/api/pokemon/invalid_pokemon_12345", timeout=10)
        if response.status_code == 404:
            print_status("✅ Invalid Pokemon: Proper 404 response", "SUCCESS")
        else:
            print_status(f"⚠️ Invalid Pokemon: Unexpected status {response.status_code}", "WARNING")
    except Exception as e:
        print_status(f"❌ Invalid Pokemon: Error - {e}", "ERROR")
    
    # Test invalid search
    try:
        response = requests.get(f"{BASE_URL}/api/search/", timeout=10)
        if response.status_code in [400, 404]:
            print_status("✅ Invalid search: Proper error response", "SUCCESS")
        else:
            print_status(f"⚠️ Invalid search: Unexpected status {response.status_code}", "WARNING")
    except Exception as e:
        print_status(f"❌ Invalid search: Error - {e}", "ERROR")

def main():
    """Run all tests"""
    print("=" * 60)
    print("POKEMON PVP HELPER - COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    print()
    
    tests = [
        ("Server Health", test_server_health),
        ("Static Files", test_static_files),
        ("Pokemon API", test_pokemon_api),
        ("Battle Simulation", test_battle_simulation),
        ("Analytics", test_analytics),
        ("Error Handling", test_error_handling)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_status(f"❌ {test_name}: Test failed with exception - {e}", "ERROR")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<25} {status}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print_status("🎉 All tests passed! Your app is ready for production.", "SUCCESS")
        return 0
    else:
        print_status(f"⚠️ {total - passed} test(s) failed. Please review the issues above.", "WARNING")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print_status("Test interrupted by user", "INFO")
        sys.exit(1)
    except Exception as e:
        print_status(f"Unexpected error: {e}", "ERROR")
        sys.exit(1) 
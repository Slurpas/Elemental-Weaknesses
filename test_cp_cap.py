#!/usr/bin/env python3
"""
Test script to verify CP cap integration
"""

import json
import requests

def test_league_change():
    """Test changing leagues"""
    print("Testing league change functionality...")
    
    # Test switching to Ultra League
    response = requests.post('http://localhost:5000/api/league/2500')
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Successfully switched to CP {data['cp_cap']} league")
        print(f"   Message: {data['message']}")
    else:
        print(f"❌ Failed to switch league: {response.text}")
        return False
    
    # Test switching back to Great League
    response = requests.post('http://localhost:5000/api/league/1500')
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Successfully switched back to CP {data['cp_cap']} league")
        print(f"   Message: {data['message']}")
    else:
        print(f"❌ Failed to switch back: {response.text}")
        return False
    
    return True

def test_battle_with_cp_cap():
    """Test battle API with CP cap parameter"""
    print("\nTesting battle API with CP cap...")
    
    battle_data = {
        "p1_id": "clodsire",
        "p2_id": "lanturn", 
        "p1_moves": {
            "fast": "POISON_STING",
            "charged1": "EARTHQUAKE",
            "charged2": "STONE_EDGE"
        },
        "p2_moves": {
            "fast": "WATER_GUN",
            "charged1": "SURF",
            "charged2": "THUNDERBOLT"
        },
        "p1_shields": 2,
        "p2_shields": 2,
        "cp_cap": 1500
    }
    
    response = requests.post('http://localhost:5000/api/battle', json=battle_data)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Battle simulation successful")
        print(f"   CP Cap used: {data.get('cp_cap', 'Not specified')}")
        print(f"   Winner: {data.get('winner', 'Unknown')}")
        print(f"   Battle rating: {data.get('battle_rating', 'Unknown')}")
        return True
    else:
        print(f"❌ Battle simulation failed: {response.text}")
        return False

def test_invalid_cp_cap():
    """Test invalid CP cap validation"""
    print("\nTesting invalid CP cap validation...")
    
    response = requests.post('http://localhost:5000/api/league/1000')
    if response.status_code == 400:
        data = response.json()
        print(f"✅ Correctly rejected invalid CP cap: {data.get('error', 'Unknown error')}")
        return True
    else:
        print(f"❌ Should have rejected invalid CP cap, got status {response.status_code}")
        return False

if __name__ == "__main__":
    print("🧪 Testing CP Cap Integration")
    print("=" * 40)
    
    try:
        # Test league changes
        if not test_league_change():
            print("❌ League change tests failed")
            exit(1)
        
        # Test battle with CP cap
        if not test_battle_with_cp_cap():
            print("❌ Battle API tests failed")
            exit(1)
        
        # Test invalid CP cap
        if not test_invalid_cp_cap():
            print("❌ Invalid CP cap validation failed")
            exit(1)
        
        print("\n🎉 All tests passed! CP cap integration is working correctly.")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the application. Make sure it's running on http://localhost:5000")
        exit(1)
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        exit(1) 
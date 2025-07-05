#!/usr/bin/env python3
"""
Test script for Shield AI implementation
Tests different shield strategies and verifies they work correctly
"""

import requests
import json
import time

def test_shield_strategies():
    """Test different shield AI strategies"""
    base_url = "http://localhost:5000"
    
    print("🧪 Testing Shield AI Implementation")
    print("=" * 50)
    
    # Test 1: Get available shield strategies
    print("\n1. Testing shield strategies API...")
    try:
        response = requests.get(f"{base_url}/api/shield-strategies")
        if response.status_code == 200:
            strategies = response.json()
            print(f"✅ Available strategies: {list(strategies['strategies'].keys())}")
            print(f"✅ Default strategy: {strategies['default']}")
        else:
            print(f"❌ Failed to get shield strategies: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error getting shield strategies: {e}")
        return False
    
    # Test 2: Test battle with different shield strategies
    print("\n2. Testing battle with different shield strategies...")
    
    # Use Azumarill vs Altaria (common Great League matchup)
    battle_data = {
        "p1_id": "azumarill",
        "p2_id": "altaria", 
        "p1_moves": {
            "fast": "BUBBLE",
            "charged1": "ICE_BEAM",
            "charged2": "HYDRO_PUMP"
        },
        "p2_moves": {
            "fast": "DRAGON_BREATH",
            "charged1": "SKY_ATTACK",
            "charged2": "DRAGON_PULSE"
        },
        "p1_shields": 2,
        "p2_shields": 2,
        "cp_cap": 1500
    }
    
    # Test different shield AI combinations
    test_cases = [
        ("never", "always", "P1 never shields, P2 always shields"),
        ("always", "never", "P1 always shields, P2 never shields"),
        ("smart_20", "smart_50", "P1 shields at 20%, P2 shields at 50%"),
        ("conservative", "aggressive", "P1 conservative, P2 aggressive"),
        ("balanced", "balanced", "Both use balanced strategy")
    ]
    
    for p1_strategy, p2_strategy, description in test_cases:
        print(f"\n   Testing: {description}")
        
        battle_data["p1_shield_ai"] = p1_strategy
        battle_data["p2_shield_ai"] = p2_strategy
        
        try:
            response = requests.post(f"{base_url}/api/battle", json=battle_data)
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Battle completed successfully")
                print(f"   📊 Winner: {result.get('winner', 'Unknown')}")
                print(f"   🛡️ P1 shields used: {2 - result.get('p1_final_shields', 2)}")
                print(f"   🛡️ P2 shields used: {2 - result.get('p2_final_shields', 2)}")
                print(f"   ⚡ Battle rating: {result.get('battle_rating', 0):.2f}")
                
                # Check if shield strategies are in the result
                if result.get('p1_shield_ai') == p1_strategy and result.get('p2_shield_ai') == p2_strategy:
                    print(f"   ✅ Shield strategies correctly returned in result")
                else:
                    print(f"   ⚠️ Shield strategies not correctly returned in result")
                
            else:
                print(f"   ❌ Battle failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error in battle: {e}")
            return False
    
    # Test 3: Test invalid shield strategy
    print("\n3. Testing invalid shield strategy...")
    battle_data["p1_shield_ai"] = "invalid_strategy"
    battle_data["p2_shield_ai"] = "smart_30"
    
    try:
        response = requests.post(f"{base_url}/api/battle", json=battle_data)
        if response.status_code == 400:
            print("✅ Invalid shield strategy correctly rejected")
        else:
            print(f"❌ Invalid shield strategy should have been rejected: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing invalid strategy: {e}")
        return False
    
    print("\n🎉 All Shield AI tests passed!")
    return True

def test_shield_ai_edge_cases():
    """Test edge cases for shield AI"""
    base_url = "http://localhost:5000"
    
    print("\n🔍 Testing Shield AI Edge Cases")
    print("=" * 50)
    
    # Test with 0 shields
    print("\n1. Testing with 0 shields...")
    battle_data = {
        "p1_id": "azumarill",
        "p2_id": "altaria",
        "p1_moves": {"fast": "BUBBLE", "charged1": "ICE_BEAM"},
        "p2_moves": {"fast": "DRAGON_BREATH", "charged1": "SKY_ATTACK"},
        "p1_shields": 0,
        "p2_shields": 0,
        "p1_shield_ai": "always",
        "p2_shield_ai": "always",
        "cp_cap": 1500
    }
    
    try:
        response = requests.post(f"{base_url}/api/battle", json=battle_data)
        if response.status_code == 200:
            result = response.json()
            print("✅ Battle with 0 shields completed successfully")
            print(f"   📊 Winner: {result.get('winner', 'Unknown')}")
        else:
            print(f"❌ Battle with 0 shields failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error in 0 shields test: {e}")
        return False
    
    # Test with different CP caps
    print("\n2. Testing shield AI with different CP caps...")
    for cp_cap in [500, 1500, 2500]:
        battle_data["cp_cap"] = cp_cap
        battle_data["p1_shields"] = 2
        battle_data["p2_shields"] = 2
        
        try:
            response = requests.post(f"{base_url}/api/battle", json=battle_data)
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ CP {cp_cap} battle completed successfully")
            else:
                print(f"   ❌ CP {cp_cap} battle failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Error in CP {cp_cap} test: {e}")
            return False
    
    print("\n🎉 All Shield AI edge case tests passed!")
    return True

if __name__ == "__main__":
    print("Starting Shield AI tests...")
    
    # Wait a moment for server to be ready
    time.sleep(2)
    
    success = True
    success &= test_shield_strategies()
    success &= test_shield_ai_edge_cases()
    
    if success:
        print("\n🎉 All Shield AI tests completed successfully!")
        print("\nNext steps:")
        print("1. Test the frontend integration")
        print("2. Add shield strategy selection UI")
        print("3. Test with more complex battle scenarios")
    else:
        print("\n❌ Some Shield AI tests failed!")
        print("Check the server logs for more details.") 
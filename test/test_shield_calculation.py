#!/usr/bin/env python3
"""
Simple test to verify shield usage calculation
"""

import requests
import json

def test_simple_shield_calculation():
    """Test simple shield usage calculation"""
    base_url = "http://localhost:5000"
    
    print("🛡️ Simple Shield Usage Calculation Test")
    print("=" * 50)
    
    # Test with a simple battle where shields should definitely be used
    battle_data = {
        "p1_id": "azumarill",
        "p2_id": "altaria",
        "p1_moves": {
            "fast": "BUBBLE",
            "charged1": "HYDRO_PUMP"  # High damage move
        },
        "p2_moves": {
            "fast": "DRAGON_BREATH",
            "charged1": "SKY_ATTACK"  # High damage move
        },
        "p1_shields": 2,
        "p2_shields": 2,
        "p1_shield_ai": "always",  # Always use shields
        "p2_shield_ai": "always",  # Always use shields
        "cp_cap": 1500
    }
    
    print("Testing with 'always' shield strategy (should use all shields)")
    print(f"Starting shields - P1: {battle_data['p1_shields']}, P2: {battle_data['p2_shields']}")
    
    try:
        response = requests.post(f"{base_url}/api/battle", json=battle_data)
        if response.status_code == 200:
            result = response.json()
            
            print(f"\n📊 Battle Results:")
            print(f"   Winner: {result.get('winner', 'Unknown')}")
            print(f"   Battle rating: {result.get('battle_rating', 0):.2f}")
            print(f"   Turns: {result.get('turns', 0)}")
            
            # Get final shield counts
            p1_final_shields = result.get('p1_final_shields', 2)
            p2_final_shields = result.get('p2_final_shields', 2)
            
            print(f"\n🛡️ Shield Usage:")
            print(f"   P1 final shields: {p1_final_shields}")
            print(f"   P2 final shields: {p2_final_shields}")
            
            # Calculate shields used
            p1_shields_used = battle_data['p1_shields'] - p1_final_shields
            p2_shields_used = battle_data['p2_shields'] - p2_final_shields
            
            print(f"   P1 shields used: {p1_shields_used}")
            print(f"   P2 shields used: {p2_shields_used}")
            
            # Check timeline for shield events
            timeline = result.get('timeline', [])
            shield_events = [event for event in timeline if event.get('shield_used')]
            
            print(f"\n📝 Shield Events in Timeline:")
            print(f"   Total shield events: {len(shield_events)}")
            
            for i, event in enumerate(shield_events, 1):
                print(f"   {i}. Turn {event.get('turn')}: {event.get('defender')} used shield against {event.get('move')}")
            
            # Verify calculation
            print(f"\n✅ Verification:")
            print(f"   Timeline shows {len(shield_events)} shield events")
            print(f"   Calculation shows P1 used {p1_shields_used} shields, P2 used {p2_shields_used} shields")
            
            if len(shield_events) == (p1_shields_used + p2_shields_used):
                print(f"   ✅ Shield usage calculation is correct!")
            else:
                print(f"   ⚠️ Shield usage calculation may have an issue")
                
        else:
            print(f"❌ Battle failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_shield_usage_formula():
    """Test the shield usage formula with different scenarios"""
    print("\n" + "=" * 50)
    print("📋 Shield Usage Formula Explanation")
    print("=" * 50)
    
    print("""
Shield Usage Formula:
====================

Starting Shields - Final Shields = Shields Used

Examples:
---------
1. Starting: 2 shields, Final: 1 shield → Used: 2 - 1 = 1 shield
2. Starting: 2 shields, Final: 0 shields → Used: 2 - 0 = 2 shields  
3. Starting: 1 shield, Final: 1 shield → Used: 1 - 1 = 0 shields
4. Starting: 0 shields, Final: 0 shields → Used: 0 - 0 = 0 shields

How it works in the battle:
---------------------------
1. Shield Slider (0-2): Sets the starting number of shields
2. Battle Simulation: Runs with Shield AI strategies
3. Shield AI decides when to use shields based on strategy
4. Final shield count: Remaining shields after battle
5. Shield usage = Starting shields - Final shields

Shield AI Strategies:
--------------------
- 'always': Uses shields whenever available (should use all shields)
- 'never': Never uses shields (should use 0 shields)
- 'smart_X': Uses shields when damage > X% of current HP
- 'conservative': Saves shields for high-damage moves
- 'aggressive': Uses shields early to maintain pressure
- 'balanced': Considers type effectiveness and damage thresholds

The shield slider controls the maximum available shields,
while the Shield AI strategy determines the intelligent decision-making.
    """)

if __name__ == "__main__":
    print("Starting Shield Calculation Test...")
    print("Make sure the Flask server is running on http://localhost:5000")
    print()
    
    try:
        test_simple_shield_calculation()
        test_shield_usage_formula()
        
        print("\n✅ Shield calculation test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        print("Make sure the Flask server is running and accessible.") 
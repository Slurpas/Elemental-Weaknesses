#!/usr/bin/env python3
"""
Test script to demonstrate shield usage calculation and tracking
Shows how the shield slider (0-2) relates to actual shield usage in battles
"""

import requests
import json

def test_shield_usage_demonstration():
    """Demonstrate how shield usage is calculated and tracked"""
    base_url = "http://localhost:5000"
    
    print("🛡️ Shield Usage Demonstration")
    print("=" * 50)
    print("This test shows how shield usage is calculated and tracked in battles.")
    print("The shield slider (0-2) sets the starting number of shields for each Pokemon.")
    print("The Shield AI strategies determine when those shields are actually used.\n")
    
    # Test battle data - Azumarill vs Altaria
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
        "cp_cap": 1500
    }
    
    # Test different shield scenarios
    shield_scenarios = [
        (2, 2, "Both players start with 2 shields"),
        (1, 1, "Both players start with 1 shield"),
        (0, 0, "Both players start with 0 shields"),
        (2, 0, "P1 has 2 shields, P2 has 0 shields"),
        (0, 2, "P1 has 0 shields, P2 has 2 shields")
    ]
    
    # Test different shield AI strategies
    ai_strategies = [
        ("always", "always", "Both always shield"),
        ("never", "never", "Both never shield"),
        ("smart_30", "smart_30", "Both use smart 30% strategy"),
        ("always", "never", "P1 always shields, P2 never shields"),
        ("smart_20", "smart_50", "P1 aggressive (20%), P2 conservative (50%)")
    ]
    
    print("📊 Testing Shield Usage Scenarios")
    print("-" * 40)
    
    for p1_shields, p2_shields, scenario_desc in shield_scenarios:
        print(f"\n🔍 Scenario: {scenario_desc}")
        print(f"   Starting shields - P1: {p1_shields}, P2: {p2_shields}")
        
        for p1_strategy, p2_strategy, strategy_desc in ai_strategies:
            battle_data.update({
                "p1_shields": p1_shields,
                "p2_shields": p2_shields,
                "p1_shield_ai": p1_strategy,
                "p2_shield_ai": p2_strategy
            })
            
            try:
                response = requests.post(f"{base_url}/api/battle", json=battle_data)
                if response.status_code == 200:
                    result = response.json()
                    
                    # Calculate shields used
                    p1_shields_used = p1_shields - result.get('p1_final_shields', p1_shields)
                    p2_shields_used = p2_shields - result.get('p2_final_shields', p2_shields)
                    
                    print(f"   Strategy: {strategy_desc}")
                    print(f"     🛡️ P1 shields used: {p1_shields_used}/{p1_shields} (AI: {p1_strategy})")
                    print(f"     🛡️ P2 shields used: {p2_shields_used}/{p2_shields} (AI: {p2_strategy})")
                    print(f"     📊 Winner: {result.get('winner', 'Unknown')}")
                    print(f"     ⚡ Battle rating: {result.get('battle_rating', 0):.2f}")
                    
                    # Show shield usage percentage
                    if p1_shields > 0:
                        p1_usage_pct = (p1_shields_used / p1_shields) * 100
                        print(f"     📈 P1 shield usage: {p1_usage_pct:.0f}%")
                    if p2_shields > 0:
                        p2_usage_pct = (p2_shields_used / p2_shields) * 100
                        print(f"     📈 P2 shield usage: {p2_usage_pct:.0f}%")
                    
                else:
                    print(f"   ❌ Battle failed: {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("📋 Shield Usage Summary")
    print("=" * 50)
    print("""
Key Points:
1. Shield Slider (0-2): Sets the starting number of shields for each Pokemon
2. Shield AI Strategy: Determines when shields are actually used during battle
3. Shield Usage Calculation: Starting shields - Final shields = Shields used
4. Shield AI Strategies:
   - 'always': Uses shields whenever available
   - 'never': Never uses shields
   - 'smart_X': Uses shields when damage > X% of current HP
   - 'conservative': Saves shields for high-damage moves
   - 'aggressive': Uses shields early to maintain pressure
   - 'balanced': Considers type effectiveness and damage thresholds

The shield slider on the page controls the maximum number of shields available,
while the Shield AI strategies determine the intelligent decision-making for when
to actually use those shields during battle.
    """)

def test_shield_ai_thresholds():
    """Test different shield AI thresholds to show when shields are used"""
    base_url = "http://localhost:5000"
    
    print("\n🎯 Testing Shield AI Thresholds")
    print("=" * 50)
    print("This test shows how different damage thresholds affect shield usage.\n")
    
    # Use a high-damage move to test thresholds
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
        "cp_cap": 1500
    }
    
    # Test different smart thresholds
    thresholds = [
        ("smart_20", "20% damage threshold"),
        ("smart_30", "30% damage threshold"),
        ("smart_50", "50% damage threshold")
    ]
    
    for strategy, desc in thresholds:
        print(f"\n🔍 Testing {desc}")
        battle_data["p1_shield_ai"] = strategy
        battle_data["p2_shield_ai"] = strategy
        
        try:
            response = requests.post(f"{base_url}/api/battle", json=battle_data)
            if response.status_code == 200:
                result = response.json()
                
                p1_shields_used = 2 - result.get('p1_final_shields', 2)
                p2_shields_used = 2 - result.get('p2_final_shields', 2)
                
                print(f"   🛡️ P1 shields used: {p1_shields_used}/2")
                print(f"   🛡️ P2 shields used: {p2_shields_used}/2")
                print(f"   📊 Winner: {result.get('winner', 'Unknown')}")
                
                # Show timeline shield usage
                timeline = result.get('timeline', [])
                shield_events = [event for event in timeline if event.get('shield_used')]
                print(f"   📝 Shield events in timeline: {len(shield_events)}")
                
                for event in shield_events:
                    print(f"     Turn {event.get('turn')}: {event.get('defender')} used shield against {event.get('move')}")
                
            else:
                print(f"   ❌ Battle failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    print("Starting Shield Usage Tests...")
    print("Make sure the Flask server is running on http://localhost:5000")
    print()
    
    try:
        test_shield_usage_demonstration()
        test_shield_ai_thresholds()
        
        print("\n✅ Shield usage tests completed!")
        print("\n💡 Key Takeaways:")
        print("1. Shield slider (0-2) = Maximum available shields")
        print("2. Shield AI strategy = When to use those shields")
        print("3. Actual shield usage = Starting shields - Final shields")
        print("4. Different strategies result in different shield usage patterns")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        print("Make sure the Flask server is running and accessible.") 
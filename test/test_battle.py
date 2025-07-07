#!/usr/bin/env python3

from battle_sim import BattleSimulator
from poke_data import PokeData

def test_battle():
    poke_data = PokeData()
    sim = BattleSimulator(poke_data)
    
    # Get Pokémon data
    p1 = poke_data.get_by_species_id('altaria')
    p2 = poke_data.get_by_species_id('lanturn')
    
    print("Altaria types:", p1.get('types', []))
    print("Lanturn types:", p2.get('types', []))
    
    # Test with Moonblast ONLY
    print("\n=== Testing with Moonblast ONLY ===")
    p1_moves_moonblast = {
        'fast': 'DRAGON_BREATH',
        'charged1': 'MOONBLAST',  # Only Moonblast
        'charged2': 'MOONBLAST'   # Same move to ensure it's used
    }
    
    result1 = sim.simulate(p1, p2, p1_moves_moonblast, {
        'fast': 'WATER_GUN',
        'charged1': 'THUNDERBOLT',
        'charged2': 'SURF'
    }, 0, 0)
    
    print(f"Moonblast result - P1 HP: {result1['p1_final_hp']}, Battle rating: {result1['battle_rating']}")
    
    # Test with Dragon Pulse ONLY
    print("\n=== Testing with Dragon Pulse ONLY ===")
    p1_moves_dragon_pulse = {
        'fast': 'DRAGON_BREATH',
        'charged1': 'DRAGON_PULSE',  # Only Dragon Pulse
        'charged2': 'DRAGON_PULSE'   # Same move to ensure it's used
    }
    
    result2 = sim.simulate(p1, p2, p1_moves_dragon_pulse, {
        'fast': 'WATER_GUN',
        'charged1': 'THUNDERBOLT',
        'charged2': 'SURF'
    }, 0, 0)
    
    print(f"Dragon Pulse result - P1 HP: {result2['p1_final_hp']}, Battle rating: {result2['battle_rating']}")
    
    # Compare results
    if result1['p1_final_hp'] == result2['p1_final_hp']:
        print("❌ Results are identical! This indicates a bug.")
    else:
        print("✅ Results are different! This shows the moves are working correctly.")
        print(f"Difference in P1 HP: {result1['p1_final_hp'] - result2['p1_final_hp']}")
        print(f"Difference in battle rating: {result1['battle_rating'] - result2['battle_rating']}")

if __name__ == "__main__":
    test_battle() 
#!/usr/bin/env python3

from battle_sim import BattleSimulator
from poke_data import PokeData

def test_simple():
    poke_data = PokeData()
    sim = BattleSimulator(poke_data)
    
    # Get Pokémon data
    p1 = poke_data.get_by_species_id('altaria')
    p2 = poke_data.get_by_species_id('lanturn')
    
    print("=== Testing Dragon Pulse vs Sky Attack ===")
    
    # Test with Dragon Pulse and Sky Attack
    result = sim.simulate(p1, p2, {
        'fast': 'DRAGON_BREATH',
        'charged1': 'DRAGON_PULSE',
        'charged2': 'SKY_ATTACK'
    }, {
        'fast': 'WATER_GUN',
        'charged1': 'THUNDERBOLT',
        'charged2': 'SURF'
    }, 0, 0)
    
    print(f"Final HP: {result['p1_final_hp']}, Battle rating: {result['battle_rating']}")

if __name__ == "__main__":
    test_simple() 
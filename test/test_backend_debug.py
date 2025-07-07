#!/usr/bin/env python3

import json
import sys
import os

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from battle_sim import BattleSimulator
from poke_data import PokeData

def test_backend_battle():
    """Test the backend battle simulation with Dragon Pulse vs Moonblast"""
    
    # Initialize components
    pd = PokeData()
    sim = BattleSimulator(pd)
    
    # Get Altaria and Lanturn data
    altaria = pd.get_by_species_id('altaria')
    lanturn = pd.get_by_species_id('lanturn')
    
    if not altaria or not lanturn:
        print("Error: Could not find Altaria or Lanturn")
        return
    
    print("Testing Altaria vs Lanturn battle simulation")
    
    # Test with Moonblast (original)
    p1_moves_moonblast = {
        'fast': 'DRAGON_BREATH',
        'charged1': 'MOONBLAST',
        'charged2': 'SKY_ATTACK'
    }
    
    p2_moves = {
        'fast': 'WATER_GUN',
        'charged1': 'SURF',
        'charged2': 'THUNDERBOLT'
    }
    
    print("\n=== Testing with Moonblast ===")
    print("P1 moves:", p1_moves_moonblast)
    print("P2 moves:", p2_moves)
    
    result1 = sim.simulate(
        p1_data=altaria,
        p2_data=lanturn,
        p1_moves=p1_moves_moonblast,
        p2_moves=p2_moves,
        p1_shields=0,
        p2_shields=0
    )
    
    print("Moonblast result:", result1['battle_rating'])
    
    # Test with Dragon Pulse (new)
    p1_moves_dragon_pulse = {
        'fast': 'DRAGON_BREATH',
        'charged1': 'DRAGON_PULSE',
        'charged2': 'SKY_ATTACK'
    }
    
    print("\n=== Testing with Dragon Pulse ===")
    print("P1 moves:", p1_moves_dragon_pulse)
    print("P2 moves:", p2_moves)
    
    result2 = sim.simulate(
        p1_data=altaria,
        p2_data=lanturn,
        p1_moves=p1_moves_dragon_pulse,
        p2_moves=p2_moves,
        p1_shields=0,
        p2_shields=0
    )
    
    print("Dragon Pulse result:", result2['battle_rating'])
    
    print(f"\n=== Comparison ===")
    print(f"Moonblast: {result1['battle_rating']:.4f}")
    print(f"Dragon Pulse: {result2['battle_rating']:.4f}")
    print(f"Difference: {abs(result2['battle_rating'] - result1['battle_rating']):.4f}")
    
    if abs(result2['battle_rating'] - result1['battle_rating']) < 0.001:
        print("⚠️  WARNING: Results are identical! This suggests the moves are not being processed differently.")
    else:
        print("✅ Results are different, moves are being processed correctly.")

    # Test with only Water Pulse (no Stone Edge)
    clodsire = pd.get_by_species_id('clodsire')
    if not clodsire or not lanturn:
        print("Error: Could not find Clodsire or Lanturn")
        return
    p1_moves_waterpulse = {
        'fast': 'POISON_STING',
        'charged1': 'WATER_PULSE',
        'charged2': None  # No second charged move
    }
    print("\n--- Clodsire (Water Pulse only) vs Lanturn ---")
    result_waterpulse = sim.simulate(
        p1_data=clodsire,
        p2_data=lanturn,
        p1_moves=p1_moves_waterpulse,
        p2_moves=p2_moves,
        p1_shields=0,
        p2_shields=0
    )
    print("Result (Water Pulse only):", result_waterpulse['battle_rating'])

if __name__ == "__main__":
    test_backend_battle() 
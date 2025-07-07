#!/usr/bin/env python3

import json
import sys
import os

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from poke_data import PokeData

def test_move_validation():
    """Test move validation for Altaria with Dragon Pulse"""
    
    # Initialize PokeData
    pd = PokeData()
    
    # Get Altaria's moves
    altaria_moves = pd.get_pokemon_moves('altaria')
    print("Altaria available moves:")
    print("Fast moves:", [m['id'] for m in altaria_moves['fast_moves']])
    print("Charged moves:", [m['id'] for m in altaria_moves['charged_moves']])
    
    # Test the moveset that the frontend is sending
    test_moveset = {
        'fast': 'DRAGON_BREATH',
        'charged1': 'DRAGON_PULSE',
        'charged2': 'SKY_ATTACK'
    }
    
    print("\nTesting moveset:", test_moveset)
    
    # Check if each move is in the available moves
    fast_move_ids = [m['id'] for m in altaria_moves['fast_moves']]
    charged_move_ids = [m['id'] for m in altaria_moves['charged_moves']]
    
    print(f"Fast move '{test_moveset['fast']}' in available: {test_moveset['fast'] in fast_move_ids}")
    print(f"Charged move '{test_moveset['charged1']}' in available: {test_moveset['charged1'] in charged_move_ids}")
    print(f"Charged move '{test_moveset['charged2']}' in available: {test_moveset['charged2'] in charged_move_ids}")
    
    # Test the validation function
    def _validate_moveset(moveset, available_moves):
        """Validate that a moveset only uses available moves"""
        if 'fast' not in moveset:
            return False
        
        # Check fast move
        fast_move_ids = [m['id'] for m in available_moves.get('fast_moves', [])]
        if moveset['fast'] not in fast_move_ids:
            print(f"Fast move validation failed: {moveset['fast']} not in {fast_move_ids}")
            return False
        
        # Check charged moves
        charged_move_ids = [m['id'] for m in available_moves.get('charged_moves', [])]
        for i in range(1, 3):
            key = f'charged{i}'
            if key in moveset and moveset[key] not in charged_move_ids:
                print(f"Charged move validation failed: {moveset[key]} not in {charged_move_ids}")
                return False
        
        return True
    
    is_valid = _validate_moveset(test_moveset, altaria_moves)
    print(f"\nMoveset validation result: {is_valid}")

if __name__ == "__main__":
    test_move_validation() 
import json
import os
from typing import List, Dict, Any, Optional

# Path to the gamemaster.json file
GAMEMASTER_PATH = os.path.join(
    os.path.dirname(__file__), 'pvpoke', 'src', 'data', 'gamemaster.json'
)

# Path to the moves.json file
MOVES_PATH = os.path.join(
    os.path.dirname(__file__), 'pvpoke', 'src', 'data', 'gamemaster', 'moves.json'
)

class PokeData:
    def __init__(self, gamemaster_path: str = GAMEMASTER_PATH, moves_path: str = MOVES_PATH):
        with open(gamemaster_path, encoding='utf-8') as f:
            data = json.load(f)
        # Find the list of Pokémon entries (skip settings/cups)
        self.pokemon = self._extract_pokemon_list(data)
        
        # Load move data
        with open(moves_path, encoding='utf-8') as f:
            self.moves = json.load(f)
        
        # Create move lookup by ID
        self.moves_by_id = {move['moveId']: move for move in self.moves}

    def _extract_pokemon_list(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        # The Pokémon entries are after the initial settings/cups, as a list
        # Find the first list in the JSON that contains dicts with 'speciesId'
        for key, value in data.items():
            if isinstance(value, list) and len(value) > 0:
                if isinstance(value[0], dict) and 'speciesId' in value[0]:
                    return value
        return []

    def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get Pokémon by species name (case-insensitive)"""
        name_lower = name.lower()
        for p in self.pokemon:
            if p.get('speciesName', '').lower() == name_lower:
                return p
        return None

    def get_by_species_id(self, species_id: str) -> Optional[Dict[str, Any]]:
        """Get Pokémon by species ID (case-insensitive)"""
        species_id_lower = species_id.lower()
        for p in self.pokemon:
            if p.get('speciesId', '').lower() == species_id_lower:
                return p
        return None

    def get_by_type(self, type_name: str) -> List[Dict[str, Any]]:
        """Get all Pokémon of a specific type"""
        type_lower = type_name.lower()
        return [p for p in self.pokemon if type_lower in [t.lower() for t in p.get('types', [])]]

    def get_by_move(self, move_id: str) -> List[Dict[str, Any]]:
        """Get all Pokémon that can learn a specific move"""
        move_lower = move_id.lower()
        result = []
        for p in self.pokemon:
            fast_moves = [m.lower() for m in p.get('fastMoves', [])]
            charged_moves = [m.lower() for m in p.get('chargedMoves', [])]
            if move_lower in fast_moves or move_lower in charged_moves:
                result.append(p)
        return result

    def get_all_types(self) -> List[str]:
        """Get all unique types"""
        types = set()
        for p in self.pokemon:
            types.update(p.get('types', []))
        return sorted(list(types))

    def get_all_moves(self) -> List[str]:
        """Get all unique move IDs"""
        moves = set()
        for p in self.pokemon:
            moves.update(p.get('fastMoves', []))
            moves.update(p.get('chargedMoves', []))
        return sorted(list(moves))

    def get_move_details(self, move_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed move information by move ID"""
        return self.moves_by_id.get(move_id)

    def get_pokemon_moves(self, species_id: str) -> Dict[str, Any]:
        """Get all available moves for a Pokémon"""
        p = self.get_by_species_id(species_id)
        if not p:
            return {}
        
        fast_moves = []
        charged_moves = []
        
        for move_id in p.get('fastMoves', []):
            move_details = self.get_move_details(move_id)
            if move_details:
                fast_moves.append({
                    'id': move_id,
                    'name': move_details['name'],
                    'type': move_details['type'],
                    'power': move_details['power'],
                    'energy': move_details['energy'],
                    'energyGain': move_details['energyGain'],
                    'cooldown': move_details['cooldown'],
                    'turns': move_details.get('turns', 1)
                })
        
        for move_id in p.get('chargedMoves', []):
            move_details = self.get_move_details(move_id)
            if move_details:
                charged_moves.append({
                    'id': move_id,
                    'name': move_details['name'],
                    'type': move_details['type'],
                    'power': move_details['power'],
                    'energy': move_details['energy'],
                    'energyGain': move_details['energyGain'],
                    'cooldown': move_details['cooldown'],
                    'buffs': move_details.get('buffs'),
                    'buffTarget': move_details.get('buffTarget'),
                    'buffApplyChance': move_details.get('buffApplyChance'),
                    'turns': move_details.get('turns', 1)
                })
        
        return {
            'fast_moves': fast_moves,
            'charged_moves': charged_moves
        }

# Example usage:
if __name__ == '__main__':
    pd = PokeData()
    print('All types:', pd.get_all_types())
    print('All moves:', pd.get_all_moves()[:10])  # Print first 10 moves
    print('Find by name:', pd.get_by_name('Charizard'))
    print('Find by type fire:', [p['speciesName'] for p in pd.get_by_type('fire')[:5]])
    print('Find by move BLAST_BURN:', [p['speciesName'] for p in pd.get_by_move('BLAST_BURN')])
    print('Move details:', pd.get_move_details('BLAST_BURN'))
    print('Moves for Charizard:', pd.get_pokemon_moves('Charizard')) 
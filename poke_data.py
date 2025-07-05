import json
import os
from typing import List, Dict, Any, Optional

# Path templates for PvPoke data
GAMEMASTER_PATH = os.path.join(
    os.path.dirname(__file__), 'pvpoke', 'src', 'data', 'gamemaster.json'
)
MOVES_PATH = os.path.join(
    os.path.dirname(__file__), 'pvpoke', 'src', 'data', 'gamemaster', 'moves.json'
)
RANK1_PATH_TEMPLATE = os.path.join(
    os.path.dirname(__file__), 'pvpoke', 'src', 'data', 'rankings', 'all', 'overall', 'rankings-{}.json'
)

class PokeData:
    def __init__(self, gamemaster_path: str = GAMEMASTER_PATH, moves_path: str = MOVES_PATH, cp_cap: int = 1500):
        with open(gamemaster_path, encoding='utf-8') as f:
            data = json.load(f)
        self.pokemon = self._extract_pokemon_list(data)
        with open(moves_path, encoding='utf-8') as f:
            self.moves = json.load(f)
        self.moves_by_id = {move['moveId']: move for move in self.moves}
        # Load rank 1 stats for the selected CP cap
        self.cp_cap = cp_cap
        self.rank1_stats = self._load_rank1_stats(self._get_rank1_path(cp_cap))
        self.rank1_ivs = self._extract_rank1_ivs_from_gamemaster(self.pokemon, cp_cap)
        print(f"[DEBUG] Loaded PvPoke rank 1 stats for CP cap: {cp_cap}")

    def _get_rank1_path(self, cp_cap: int) -> str:
        # For Master League (no CP cap), use the 10000 CP rankings
        if cp_cap == 0:
            return RANK1_PATH_TEMPLATE.format(10000)
        return RANK1_PATH_TEMPLATE.format(cp_cap)

    def _extract_pokemon_list(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
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

    def _load_rank1_stats(self, path: str) -> Dict[str, Any]:
        if not os.path.exists(path):
            print(f"[DEBUG] Rank 1 stats file not found for path: {path}")
            return {}
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
        stats = {}
        for entry in data:
            sid = entry.get('speciesId')
            s = entry.get('stats', {})
            ivs = entry.get('ivs', {}) if 'ivs' in entry else {
                'atk': entry.get('iv_atk', None),
                'def': entry.get('iv_def', None),
                'sta': entry.get('iv_sta', None)
            }
            stats[sid] = {
                'atk': s.get('atk'),
                'def': s.get('def'),
                'hp': s.get('hp'),
                'product': s.get('product'),
                'ivs': ivs
            }
        return stats

    def _extract_rank1_ivs_from_gamemaster(self, pokemon_list, cp_cap: int):
        stats = {}
        # For Master League (no CP cap), use level 50 with perfect IVs
        if cp_cap == 0:
            for p in pokemon_list:
                sid = p.get('speciesId')
                stats[sid] = {
                    'level': 50,
                    'iv_atk': 15,
                    'iv_def': 15,
                    'iv_sta': 15
                }
        else:
            cp_key = f'cp{cp_cap}'
            for p in pokemon_list:
                sid = p.get('speciesId')
                default_ivs = p.get('defaultIVs', {})
                cp_entry = default_ivs.get(cp_key)
                if cp_entry and len(cp_entry) == 4:
                    stats[sid] = {
                        'level': cp_entry[0],
                        'iv_atk': cp_entry[1],
                        'iv_def': cp_entry[2],
                        'iv_sta': cp_entry[3]
                    }
        return stats

    def get_rank1_stats(self, species_id: str) -> Optional[Dict[str, Any]]:
        sid = species_id.lower()
        stats = self.rank1_stats.get(sid)
        ivs = self.rank1_ivs.get(sid)
        if stats:
            if ivs:
                stats = stats.copy()
                stats['level'] = ivs['level']
                stats['iv_atk'] = ivs['iv_atk']
                stats['iv_def'] = ivs['iv_def']
                stats['iv_sta'] = ivs['iv_sta']
            return stats
        elif ivs:
            return ivs
        return None

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
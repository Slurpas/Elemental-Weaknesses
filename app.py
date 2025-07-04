from flask import Flask, render_template, request, jsonify
import requests
import json
from datetime import datetime, timedelta
import re
import csv
import threading
from poke_data import PokeData
from battle_sim import BattleSimulator

app = Flask(__name__)

# Initialize local Pokémon data
poke_data = PokeData()

# Cache for Pokemon data to reduce API calls
pokemon_cache = {}
type_cache = {}  # Cache for type effectiveness data
cache_duration = timedelta(hours=1)

# --- CSV Parsing for PvP Rankings ---
pvp_moves_by_name = {}

def load_pvp_csv():
    global pvp_moves_by_name
    try:
        with open('cp1500_all_overall_rankings.csv', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Normalize name for lookup (lowercase, remove spaces, handle forms)
                name = row['Pokemon'].strip().lower().replace(' (galarian)', '-galar').replace(' (alolan)', '-alola').replace(' (shadow)', '-shadow').replace(' (hisuian)', '-hisui').replace(' ', '').replace("(", '').replace(")", '')
                pvp_moves_by_name[name] = {
                    'score': row['Score'],
                    'type_1': row['Type 1'],
                    'type_2': row['Type 2'],
                    'fast_move': row['Fast Move'],
                    'charged_move_1': row['Charged Move 1'],
                    'charged_move_2': row['Charged Move 2'],
                }
    except Exception as e:
        print(f"Error loading PvP CSV: {e}")

# Call at startup
load_pvp_csv()

move_type_cache = {}
move_type_cache_lock = threading.Lock()

def get_move_type_and_class(move_name):
    key = move_name.lower().replace(' ', '-').replace('_', '-')
    with move_type_cache_lock:
        if key in move_type_cache:
            return move_type_cache[key]
    # Fetch from PokeAPI
    url = f'https://pokeapi.co/api/v2/move/{key}'
    resp = requests.get(url)
    if resp.status_code == 200:
        data = resp.json()
        move_type = data['type']['name']
        move_class = data['damage_class']['name']
        with move_type_cache_lock:
            move_type_cache[key] = (move_type, move_class)
        return move_type, move_class
    return None, None

def get_pvp_moves_for_pokemon(name):
    # Try direct match, then try removing dashes/spaces, then fallback
    key = name.lower().replace(' ', '').replace('_', '-').replace('.', '').replace("'", "").replace('é', 'e')
    if key in pvp_moves_by_name:
        row = pvp_moves_by_name[key]
    else:
        for k in pvp_moves_by_name:
            if key in k:
                row = pvp_moves_by_name[k]
                break
        else:
            return []
    moves = []
    for move_name, move_class in [
        (row['fast_move'], 'fast'),
        (row['charged_move_1'], 'charged'),
        (row['charged_move_2'], 'charged')
    ]:
        if move_name and move_name.lower() != 'none':
            # Use poke_data to get move type
            move_id = move_name.upper().replace(' ', '_')
            move_type = None
            for p in poke_data.pokemon:
                if move_id in p.get('fastMoves', []) or move_id in p.get('chargedMoves', []):
                    for t in p.get('types', []):
                        if t and t != 'none':
                            move_type = t
                            break
                if move_type:
                    break
            moves.append({
                'name': move_name,
                'type': move_type or '',
                'move_class': move_class
            })
    return moves

def get_cached_pokemon(name):
    """Get Pokemon data from cache if it's still valid"""
    if name in pokemon_cache:
        cached_data, timestamp = pokemon_cache[name]
        if datetime.now() - timestamp < cache_duration:
            return cached_data
    return None

def cache_pokemon(name, data):
    """Cache Pokemon data with timestamp"""
    pokemon_cache[name] = (data, datetime.now())

@app.route('/')
def index():
    """Serve the main webpage"""
    return render_template('index.html')

def get_move_effectiveness(move_type, defender_types):
    # Use get_type_effectiveness to get the effectiveness dict for the defender
    eff = get_type_effectiveness(defender_types)
    multiplier = eff['effectiveness'].get(move_type, 1.0)
    if multiplier == 0:
        label = 'Immune'
    elif multiplier > 1:
        label = 'Super Effective'
    elif multiplier < 1:
        label = 'Not Very Effective'
    else:
        label = 'Neutral'
    return multiplier, label

@app.route('/api/pokemon/<name>')
def get_pokemon(name):
    """API endpoint to get Pokemon data (local gamemaster.json version)"""
    try:
        # Check cache first
        cached_data = get_cached_pokemon(name.lower())
        if cached_data:
            return jsonify(cached_data)

        # Try to match by speciesId first, then by name
        p = poke_data.get_by_species_id(name)
        if not p:
            p = poke_data.get_by_name(name)
        if not p:
            return jsonify({'error': f'Pokemon not found: {name}'}), 404

        # Get types
        types = [t for t in p.get('types', []) if t and t != 'none']

        # Get type effectiveness using static chart
        effectiveness = get_fallback_effectiveness(types)

        # Get moves (fast and charged)
        moves = []
        for move_id in p.get('fastMoves', []) + p.get('chargedMoves', []):
            # Try to infer move type from move_id (e.g., "FIRE_BLAST" -> "fire")
            move_type = None
            for t in poke_data.all_types():
                if t in move_id.lower():
                    move_type = t
                    break
            moves.append({
                'name': move_id,
                'type': move_type or '',
                'move_class': 'fast' if move_id in p.get('fastMoves', []) else 'charged'
            })

        # Get PvP moves from CSV (if still desired)
        pvp_moves = get_pvp_moves_for_pokemon(name)
        for move in pvp_moves:
            if move['type']:
                mult, label = get_move_effectiveness(move['type'], types)
                move['effectiveness'] = {'multiplier': mult, 'label': label}
            else:
                move['effectiveness'] = {'multiplier': 1.0, 'label': 'Neutral'}

        # Local sprite path
        sprite_url = f"/static/sprites/{p.get('speciesId')}.png"

        # Format the response
        formatted_data = {
            'id': p.get('dex'),
            'name': p.get('speciesName'),
            'types': types,
            'stats': p.get('baseStats', {}),
            'effectiveness': effectiveness,
            'moves': moves,
            'pvp_moves': pvp_moves,
            'sprite': sprite_url
        }

        # Cache the data
        cache_pokemon(name.lower(), formatted_data)

        return jsonify(formatted_data)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search/<query>')
def search_pokemon(query):
    """API endpoint to search for Pokemon by name, including all forms (local gamemaster.json version)"""
    try:
        # Use local data for all Pokémon
        all_pokemon = poke_data.pokemon

        # Build readable names for forms
        def readable_name(species_name):
            # e.g. "Stunfisk (Galarian)" or "Charizard (Mega X)"
            if '(' in species_name:
                return species_name
            # Try to infer from speciesId
            return species_name

        normalized_query = query.lower().replace(' ', '').replace('-', '')
        def norm(s):
            return s.lower().replace(' ', '').replace('-', '')
        matching_pokemon = [
            {
                'name': p['speciesId'],
                'readable_name': readable_name(p['speciesName'])
            }
            for p in all_pokemon
            if normalized_query in norm(p.get('speciesName', '')) or normalized_query in norm(p.get('speciesId', ''))
        ]
        if not matching_pokemon and all_pokemon:
            # fallback: return the closest match
            best = min(all_pokemon, key=lambda p: abs(len(norm(p.get('speciesName', ''))) - len(normalized_query)))
            matching_pokemon = [{
                'name': best['speciesId'],
                'readable_name': readable_name(best['speciesName'])
            }]
        matching_pokemon = matching_pokemon[:10]  # Limit to 10 results
        return jsonify(matching_pokemon)

    except Exception as e:
        print(f"Search error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

def get_type_effectiveness(types):
    """Calculate type effectiveness for given Pokemon types using PokeAPI"""
    try:
        # Check if we have cached type data
        type_key = '-'.join(sorted(types))
        if type_key in type_cache:
            cached_data, timestamp = type_cache[type_key]
            if datetime.now() - timestamp < cache_duration:
                return cached_data
        
        print(f"DEBUG: Processing types: {types}")
        
        # Get type effectiveness from PokeAPI for each type
        combined_effectiveness = {}
        all_types = ['normal', 'fire', 'water', 'electric', 'grass', 'ice', 'fighting', 
                     'poison', 'ground', 'flying', 'psychic', 'bug', 'rock', 'ghost', 
                     'dragon', 'dark', 'steel', 'fairy']
        
        # Initialize all types with 1.0 multiplier
        for attacking_type in all_types:
            combined_effectiveness[attacking_type] = 1.0
        
        # Get effectiveness data for each defending type
        for defending_type in types:
            print(f"DEBUG: Processing defending type: {defending_type}")
            
            # Check if type data is cached
            if defending_type in type_cache:
                type_data = type_cache[defending_type][0]
                print(f"DEBUG: Using cached data for {defending_type}")
            else:
                response = requests.get(f'https://pokeapi.co/api/v2/type/{defending_type}')
                if response.status_code == 200:
                    type_data = response.json()
                    # Cache the type data
                    type_cache[defending_type] = (type_data, datetime.now())
                    print(f"DEBUG: Fetched fresh data for {defending_type}")
                else:
                    print(f"DEBUG: Failed to fetch data for {defending_type}")
                    continue
            
            # Process damage relations
            print(f"DEBUG: Damage relations for {defending_type}: {type_data['damage_relations']}")
            
            for relation_name, type_list in type_data['damage_relations'].items():
                print(f"DEBUG: Processing {relation_name} for {defending_type}")
                if relation_name == 'double_damage_from':
                    for attacking_type_info in type_list:
                        attacking_type_name = attacking_type_info['name']
                        if attacking_type_name in combined_effectiveness:
                            old_value = combined_effectiveness[attacking_type_name]
                            combined_effectiveness[attacking_type_name] *= 2
                            print(f"DEBUG: {attacking_type_name} vs {defending_type}: {old_value} -> {combined_effectiveness[attacking_type_name]}")
                elif relation_name == 'half_damage_from':
                    for attacking_type_info in type_list:
                        attacking_type_name = attacking_type_info['name']
                        if attacking_type_name in combined_effectiveness:
                            old_value = combined_effectiveness[attacking_type_name]
                            combined_effectiveness[attacking_type_name] *= 0.5
                            print(f"DEBUG: {attacking_type_name} vs {defending_type}: {old_value} -> {combined_effectiveness[attacking_type_name]}")
                elif relation_name == 'no_damage_from':
                    for attacking_type_info in type_list:
                        attacking_type_name = attacking_type_info['name']
                        if attacking_type_name in combined_effectiveness:
                            old_value = combined_effectiveness[attacking_type_name]
                            combined_effectiveness[attacking_type_name] *= 0
                            print(f"DEBUG: {attacking_type_name} vs {defending_type}: {old_value} -> {combined_effectiveness[attacking_type_name]}")
        
        print(f"DEBUG: Final effectiveness: {combined_effectiveness}")
        
        # Return detailed effectiveness with multipliers
        result = {
            'effectiveness': combined_effectiveness,
            'weaknesses': [(type_name, mult) for type_name, mult in combined_effectiveness.items() if mult > 1],
            'resistances': [(type_name, mult) for type_name, mult in combined_effectiveness.items() if mult < 1 and mult > 0],
            'immunities': [(type_name, mult) for type_name, mult in combined_effectiveness.items() if mult == 0]
        }
        
        # Cache the result
        type_cache[type_key] = (result, datetime.now())
        
        return result
        
    except Exception as e:
        print(f"Error getting type effectiveness: {e}")
        import traceback
        traceback.print_exc()
        # Fallback to simplified chart if API fails
        return get_fallback_effectiveness(types)

def get_fallback_effectiveness(types):
    """Fallback effectiveness calculation if API fails"""
    # Complete type effectiveness chart
    effectiveness_chart = {
        'normal': {'rock': 0.5, 'ghost': 0, 'steel': 0.5},
        'fire': {'fire': 0.5, 'water': 0.5, 'grass': 2, 'ice': 2, 'bug': 2, 'rock': 0.5, 'dragon': 0.5, 'steel': 2},
        'water': {'fire': 2, 'water': 0.5, 'grass': 0.5, 'ground': 2, 'rock': 2, 'dragon': 0.5},
        'electric': {'water': 2, 'electric': 0.5, 'grass': 0.5, 'ground': 0, 'flying': 2, 'dragon': 0.5},
        'grass': {'fire': 0.5, 'water': 2, 'grass': 0.5, 'poison': 0.5, 'ground': 2, 'flying': 0.5, 'bug': 0.5, 'rock': 2, 'dragon': 0.5, 'steel': 0.5},
        'ice': {'fire': 0.5, 'water': 0.5, 'grass': 2, 'ice': 0.5, 'ground': 2, 'flying': 2, 'dragon': 2, 'steel': 0.5},
        'fighting': {'normal': 2, 'ice': 2, 'poison': 0.5, 'flying': 0.5, 'psychic': 0.5, 'bug': 0.5, 'rock': 2, 'ghost': 0, 'steel': 2, 'fairy': 0.5},
        'poison': {'grass': 2, 'poison': 0.5, 'ground': 0.5, 'rock': 0.5, 'ghost': 0.5, 'steel': 0, 'fairy': 2},
        'ground': {'fire': 2, 'electric': 2, 'grass': 0.5, 'poison': 2, 'flying': 0, 'bug': 0.5, 'rock': 2, 'steel': 2},
        'flying': {'electric': 0.5, 'grass': 2, 'fighting': 2, 'bug': 2, 'rock': 0.5, 'steel': 0.5},
        'psychic': {'fighting': 2, 'poison': 2, 'psychic': 0.5, 'dark': 0, 'steel': 0.5},
        'bug': {'fire': 0.5, 'grass': 2, 'fighting': 0.5, 'poison': 0.5, 'flying': 0.5, 'psychic': 2, 'ghost': 0.5, 'dark': 2, 'steel': 0.5, 'fairy': 0.5},
        'rock': {'fire': 2, 'ice': 2, 'fighting': 0.5, 'ground': 0.5, 'flying': 2, 'bug': 2, 'steel': 0.5},
        'ghost': {'normal': 0, 'psychic': 2, 'ghost': 2, 'dark': 0.5},
        'dragon': {'dragon': 2, 'steel': 0.5, 'fairy': 0},
        'dark': {'fighting': 0.5, 'psychic': 2, 'ghost': 2, 'dark': 0.5, 'fairy': 0.5},
        'steel': {'fire': 0.5, 'water': 0.5, 'electric': 0.5, 'ice': 2, 'rock': 2, 'steel': 0.5, 'fairy': 2},
        'fairy': {'fighting': 2, 'poison': 0.5, 'dragon': 2, 'dark': 2, 'steel': 0.5}
    }
    
    # Calculate combined effectiveness
    combined_effectiveness = {}
    all_types = ['normal', 'fire', 'water', 'electric', 'grass', 'ice', 'fighting', 
                 'poison', 'ground', 'flying', 'psychic', 'bug', 'rock', 'ghost', 
                 'dragon', 'dark', 'steel', 'fairy']
    
    for attacking_type in all_types:
        multiplier = 1.0
        for defending_type in types:
            if attacking_type in effectiveness_chart and defending_type in effectiveness_chart[attacking_type]:
                multiplier *= effectiveness_chart[attacking_type][defending_type]
        combined_effectiveness[attacking_type] = multiplier
    
    # Return detailed effectiveness with multipliers
    return {
        'effectiveness': combined_effectiveness,
        'weaknesses': [(type_name, mult) for type_name, mult in combined_effectiveness.items() if mult > 1],
        'resistances': [(type_name, mult) for type_name, mult in combined_effectiveness.items() if mult < 1 and mult > 0],
        'immunities': [(type_name, mult) for type_name, mult in combined_effectiveness.items() if mult == 0]
    }

@app.route('/api/matchup', methods=['POST'])
def matchup():
    data = request.get_json()
    opponent_name = data.get('opponent')
    team = data.get('team', [])  # list of up to 3 names
    
    # Get opponent PvP moves
    opponent_info = get_pokemon(opponent_name).json
    opponent_types = None
    if 'types' in opponent_info:
        opponent_types = opponent_info['types']
    elif 'effectiveness' in opponent_info:
        # fallback: try to get types from effectiveness
        opponent_types = opponent_info.get('effectiveness', {}).get('types', [])
    else:
        opponent_types = []
    opponent_pvp_moves = opponent_info.get('pvp_moves', [])

    # Get team info
    team_infos = []
    for name in team:
        info = get_pokemon(name).json
        team_infos.append(info)

    # For each opponent move, calculate effectiveness vs each team member
    opponent_moves_vs_team = []
    for move in opponent_pvp_moves:
        move_row = {
            'move': move,
            'vs_team': []
        }
        for t in team_infos:
            t_types = t.get('types', [])
            multiplier, label = get_move_effectiveness(move['type'], t_types)
            move_row['vs_team'].append({'pokemon': t['name'], 'effectiveness': {'multiplier': multiplier, 'label': label}})
        opponent_moves_vs_team.append(move_row)

    # For each team member, get their PvP moves and effectiveness vs opponent
    team_moves_vs_opponent = []
    for t in team_infos:
        t_moves = t.get('pvp_moves', [])
        t_row = {
            'pokemon': t['name'],
            'moves': []
        }
        for move in t_moves:
            multiplier, label = get_move_effectiveness(move['type'], opponent_types)
            t_row['moves'].append({
                'move': move,
                'effectiveness': {'multiplier': multiplier, 'label': label}
            })
        team_moves_vs_opponent.append(t_row)

    return jsonify({
        'opponent': opponent_name,
        'team': team,
        'opponent_moves_vs_team': opponent_moves_vs_team,
        'team_moves_vs_opponent': team_moves_vs_opponent
    })

battle_simulator = BattleSimulator(poke_data)

@app.route('/api/battle', methods=['POST'])
def api_battle():
    """Simulate a battle between two Pokémon with movesets and shields."""
    try:
        data = request.get_json()
        p1_id = data.get('p1_id')
        p2_id = data.get('p2_id')
        p1_moves = data.get('p1_moves')  # {'fast': ..., 'charged1': ..., 'charged2': ...}
        p2_moves = data.get('p2_moves')
        p1_shields = data.get('p1_shields', 2)
        p2_shields = data.get('p2_shields', 2)
        settings = data.get('settings', {})
        
        # Validate input
        if not p1_id or not p2_id or not p1_moves or not p2_moves:
            return jsonify({'error': 'Missing required parameters'}), 400
        
        # Get Pokémon data
        p1 = poke_data.get_by_species_id(p1_id)
        p2 = poke_data.get_by_species_id(p2_id)
        
        if not p1 or not p2:
            return jsonify({'error': 'Pokemon not found'}), 404
        
        # Validate moves
        p1_available_moves = poke_data.get_pokemon_moves(p1_id)
        p2_available_moves = poke_data.get_pokemon_moves(p2_id)
        
        # Check if selected moves are valid
        if not _validate_moveset(p1_moves, p1_available_moves):
            return jsonify({'error': f'Invalid moveset for {p1_id}'}), 400
        if not _validate_moveset(p2_moves, p2_available_moves):
            return jsonify({'error': f'Invalid moveset for {p2_id}'}), 400
        
        # Run battle simulation
        result = battle_simulator.simulate(
            p1_data=p1,
            p2_data=p2,
            p1_moves=p1_moves,
            p2_moves=p2_moves,
            p1_shields=p1_shields,
            p2_shields=p2_shields,
            settings=settings
        )
        
        # Add Pokémon names to result for frontend
        result['p1_name'] = p1['speciesName']
        result['p2_name'] = p2['speciesName']
        result['p1_species_id'] = p1['speciesId']
        result['p2_species_id'] = p2['speciesId']
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'Battle simulation failed: {str(e)}'}), 500

def _validate_moveset(moveset, available_moves):
    """Validate that a moveset only uses available moves"""
    if 'fast' not in moveset:
        return False
    
    # Check fast move
    fast_move_ids = [m['id'] for m in available_moves.get('fast_moves', [])]
    if moveset['fast'] not in fast_move_ids:
        return False
    
    # Check charged moves
    charged_move_ids = [m['id'] for m in available_moves.get('charged_moves', [])]
    for i in range(1, 3):
        key = f'charged{i}'
        if key in moveset and moveset[key] not in charged_move_ids:
            return False
    
    return True

@app.route('/api/pokemon/<name>/moves')
def get_pokemon_moves(name):
    """Get all available moves and best moveset for a Pokémon."""
    try:
        # Try to match by speciesId first, then by name
        p = poke_data.get_by_species_id(name)
        if not p:
            p = poke_data.get_by_species_id(name)
        if not p:
            return jsonify({'error': 'Pokemon not found'}), 404
        
        # Get all available moves
        moves_data = poke_data.get_pokemon_moves(p['speciesId'])
        
        # Get best moveset from PvP CSV (if available)
        best_moveset = get_pvp_moves_for_pokemon(p['speciesName'])
        
        # If no best moveset found, use first available moves
        if not best_moveset:
            best_moveset = {
                'fast': moves_data['fast_moves'][0]['id'] if moves_data['fast_moves'] else None,
                'charged1': moves_data['charged_moves'][0]['id'] if moves_data['charged_moves'] else None,
                'charged2': moves_data['charged_moves'][1]['id'] if len(moves_data['charged_moves']) > 1 else None
            }
        
        return jsonify({
            'pokemon': {
                'species_id': p['speciesId'],
                'species_name': p['speciesName'],
                'types': p.get('types', []),
                'sprite': f"/static/sprites/{p['speciesId']}.png"
            },
            'fast_moves': moves_data['fast_moves'],
            'charged_moves': moves_data['charged_moves'],
            'best_moveset': best_moveset
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get moves: {str(e)}'}), 500

if __name__ == '__main__':
    print("Starting Pokemon PvP Analyzer...")
    print("Open your browser and go to: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000) 
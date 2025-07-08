from flask import Flask, render_template, request, jsonify, session, request, redirect, url_for, render_template_string
import requests
import json
from datetime import datetime, timedelta
import re
import csv
import threading
import html
import secrets
import os
from poke_data import PokeData
from battle_sim import BattleSimulator
from analytics import analytics

app = Flask(__name__)

# Security: Generate a secret key for session management and CSRF protection
app.secret_key = os.environ.get('SECRET_KEY') or secrets.token_hex(32)

# Security: Disable debug mode in production
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

# Initialize local Pokémon data
poke_data = PokeData()

# Cache for Pokemon data to reduce API calls
pokemon_cache = {}
type_cache = {}  # Cache for type effectiveness data
cache_duration = timedelta(hours=1)

# --- PvPoke Rankings Data Loading ---
pvp_rankings_by_species = {}

def load_pvp_rankings(cp_cap=1500):
    """Load PvPoke rankings data for the specified CP cap"""
    global pvp_rankings_by_species
    try:
        # Use the rankings file for the specified CP cap
        rankings_path = f'pvpoke/src/data/rankings/all/overall/rankings-{cp_cap}.json'
        print(f"[DEBUG] Loading PvP rankings for CP cap {cp_cap} from {rankings_path}")
        
        with open(rankings_path, encoding='utf-8') as f:
            rankings_data = json.load(f)
            
        # Index by speciesId for fast lookup
        for pokemon in rankings_data:
            species_id = pokemon['speciesId']
            pvp_rankings_by_species[species_id] = {
                'speciesName': pokemon['speciesName'],
                'rating': pokemon.get('rating', 0),
                'score': pokemon.get('score', 0),
                'moves': pokemon.get('moves', {}),
                'moveset': pokemon.get('moveset', []),
                'stats': pokemon.get('stats', {}),
                'matchups': pokemon.get('matchups', []),
                'counters': pokemon.get('counters', [])
            }
            
        print(f"[DEBUG] Loaded {len(pvp_rankings_by_species)} Pokemon from PvPoke rankings for CP {cp_cap}")
        
    except Exception as e:
        print(f"Error loading PvPoke rankings for CP {cp_cap}: {e}")
        # Fallback to CSV if PvPoke data is not available
        load_pvp_csv_fallback()

def load_pvp_csv_fallback():
    """Fallback to CSV loading if PvPoke data is not available"""
    global pvp_rankings_by_species
    try:
        with open('cp1500_all_overall_rankings.csv', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Normalize name for lookup (lowercase, remove spaces, handle forms)
                name = row['Pokemon'].strip().lower().replace(' (galarian)', '-galar').replace(' (alolan)', '-alola').replace(' (shadow)', '-shadow').replace(' (hisuian)', '-hisui').replace(' ', '').replace("(", '').replace(")", '')
                pvp_rankings_by_species[name] = {
                    'speciesName': row['Pokemon'],
                    'score': row['Score'],
                    'moveset': [row['Fast Move'], row['Charged Move 1'], row['Charged Move 2']],
                    'moves': {
                        'fastMoves': [{'moveId': row['Fast Move'], 'uses': 100000}],
                        'chargedMoves': [
                            {'moveId': row['Charged Move 1'], 'uses': 50000},
                            {'moveId': row['Charged Move 2'], 'uses': 50000}
                        ]
                    }
                }
        print(f"[DEBUG] Loaded {len(pvp_rankings_by_species)} Pokemon from CSV fallback")
    except Exception as e:
        print(f"Error loading PvP CSV fallback: {e}")

# Call at startup - load Great League (1500 CP) by default
load_pvp_rankings(1500)

def reload_pvp_rankings_for_cap(cp_cap):
    """Reload PvP rankings for a different CP cap"""
    global pvp_rankings_by_species
    pvp_rankings_by_species.clear()  # Clear existing data
    load_pvp_rankings(cp_cap)
    print(f"[DEBUG] Reloaded PvP rankings for CP cap {cp_cap}")

# Security: Input validation and sanitization functions
def sanitize_input(input_str):
    """Sanitize user input to prevent XSS and injection attacks"""
    if not input_str:
        return ""
    # HTML escape to prevent XSS
    return html.escape(str(input_str).strip())

def sanitize_pokemon_name(name):
    """Sanitize Pokemon name for lookup (no HTML escaping needed)"""
    if not name:
        return ""
    # Just strip whitespace for Pokemon name lookup
    return str(name).strip()

def validate_pokemon_name(name):
    """Validate Pokemon name to prevent path traversal and injection"""
    if not name:
        return False
    # Allow alphanumeric, hyphens, underscores, spaces, and apostrophes for Pokemon names
    if not re.match(r'^[a-zA-Z0-9\-\_\s\']+$', name):
        return False
    # Prevent path traversal attempts
    if '..' in name or '/' in name or '\\' in name:
        return False
    return True

def validate_search_query(query):
    """Validate search query input"""
    if not query:
        return False
    # Allow alphanumeric, spaces, hyphens, and common Pokemon name characters
    if not re.match(r'^[a-zA-Z0-9\-\_\s\']+$', query):
        return False
    # Prevent path traversal
    if '..' in query or '/' in query or '\\' in query:
        return False
    return True

# Note: get_move_type_and_class() function removed - using PvPoke data instead

# Note: get_pvp_moves_for_pokemon() function removed - using poke_data.get_pokemon_moves() instead

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
    # Track page visit
    analytics.track_visit(request.remote_addr, request.headers.get('User-Agent', ''))
    return render_template('index.html')

def get_move_effectiveness(move_type, defender_types):
    # Use get_type_effectiveness to get the effectiveness dict for the defender
    eff = get_type_effectiveness(defender_types)
    multiplier = eff['effectiveness'].get(move_type, 1.0)
    if multiplier > 1:
        label = 'Super Effective'
    elif multiplier < 1:
        label = 'Not Very Effective'
    else:
        label = 'Neutral'
    print(f"[DEBUG] get_move_effectiveness: move_type={move_type}, defender_types={defender_types}, multiplier={multiplier}, label={label}")
    return multiplier, label

@app.route('/api/pokemon/<name>')
def get_pokemon(name):
    """API endpoint to get Pokemon data (local gamemaster.json version)"""
    try:
        # Security: Validate and sanitize input
        if not validate_pokemon_name(name):
            print(f"DEBUG: Invalid Pokemon name: {name}")
            return jsonify({'error': 'Invalid Pokemon name'}), 400
        
        sanitized_name = sanitize_pokemon_name(name)
        print(f"DEBUG: Looking for Pokemon: {sanitized_name}")
        
        # Check cache first (but skip for now to ensure fresh data)
        # cached_data = get_cached_pokemon(sanitized_name.lower())
        # if cached_data:
        #     return jsonify(cached_data)

        # Try to match by speciesId first, then by name
        p = poke_data.get_by_species_id(sanitized_name)
        if not p:
            print(f"DEBUG: Not found by speciesId, trying by name")
            p = poke_data.get_by_name(sanitized_name)
        if not p:
            print(f"DEBUG: Pokemon not found: {sanitized_name}")
            return jsonify({'error': 'Pokemon not found'}), 404
        
        print(f"DEBUG: Found Pokemon: {p.get('speciesName', 'Unknown')} (ID: {p.get('speciesId', 'Unknown')})")

        # Get types
        types = [t for t in p.get('types', []) if t and t != 'none']

        # Get type effectiveness using static chart
        effectiveness = get_fallback_effectiveness(types)

        # Get moves (fast and charged)
        moves = []
        for move_id in p.get('fastMoves', []) + p.get('chargedMoves', []):
            # Try to infer move type from move_id (e.g., "FIRE_BLAST" -> "fire")
            move_type = None
            for t in poke_data.get_all_types():
                if t in move_id.lower():
                    move_type = t
                    break
            moves.append({
                'name': move_id,
                'type': move_type or '',
                'move_class': 'fast' if move_id in p.get('fastMoves', []) else 'charged'
            })

        # Get PvP moves using poke_data
        pvp_moves_data = poke_data.get_pokemon_moves(p.get('speciesId', sanitized_name))
        pvp_moves = []
        
        # Convert to the expected format
        for move in pvp_moves_data.get('fast_moves', []) + pvp_moves_data.get('charged_moves', []):
            pvp_moves.append({
                'name': move['name'],
                'type': move['type'],
                'move_class': move.get('move_class', 'fast' if move in pvp_moves_data.get('fast_moves', []) else 'charged'),
                'dpe': None,  # Will be calculated below
                'power': move.get('power', 0),
                'energy': move.get('energy', 0)
            })
        
        for move in pvp_moves:
            if move['type']:
                mult, label = get_move_effectiveness(move['type'], types)
                move['effectiveness'] = {'multiplier': mult, 'label': label}
            else:
                move['effectiveness'] = {'multiplier': 1.0, 'label': 'Neutral'}

        # Local sprite path
        sprite_url = f"/static/sprites/{p.get('speciesId')}.png"

        # Get PvPoke rankings data for this Pokémon
        species_id = p.get('speciesId', '').lower()
        pvpoke_data = pvp_rankings_by_species.get(species_id, {})
        print(f"[DEBUG] Looking up PvPoke data for {species_id}: {pvpoke_data.get('moveset', 'Not found')}")
        
        # Format the response
        formatted_data = {
            'id': p.get('dex'),
            'name': p.get('speciesName'),
            'speciesId': p.get('speciesId'),
            'types': types,
            'stats': p.get('baseStats', {}),
            'effectiveness': effectiveness,
            'moves': moves,
            'pvp_moves': pvp_moves,
            'pvpoke_moveset': pvpoke_data.get('moveset', []),  # Best moveset from PvPoke
            'pvpoke_rating': pvpoke_data.get('rating', 0),     # PvPoke rating
            'pvpoke_score': pvpoke_data.get('score', 0),       # PvPoke score
            'sprite': sprite_url
        }

        # Cache the data
        cache_pokemon(sanitized_name.lower(), formatted_data)

        return jsonify(formatted_data)

    except Exception as e:
        # Security: Don't expose internal error details in production
        if app.config['DEBUG']:
            return jsonify({'error': str(e)}), 500
        else:
            return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/search/<query>')
def search_pokemon(query):
    """API endpoint to search for Pokemon by name, including all forms (local gamemaster.json version)"""
    try:
        # Security: Validate and sanitize input
        if not validate_search_query(query):
            return jsonify({'error': 'Invalid search query'}), 400
        
        sanitized_query = sanitize_pokemon_name(query)
        
        # Use local data for all Pokémon
        all_pokemon = poke_data.pokemon

        normalized_query = sanitized_query.lower().replace(' ', '').replace('-', '')
        def norm(s):
            return s.lower().replace(' ', '').replace('-', '')
        
        matching_pokemon = [
            {
                'name': p['speciesId'],
                'readable_name': p['speciesName'],
                'sprite': f"/static/sprites/{p['speciesId']}.png",
                'types': p.get('types', [])
            }
            for p in all_pokemon
            if normalized_query in norm(p.get('speciesName', '')) or normalized_query in norm(p.get('speciesId', ''))
        ]
        
        if not matching_pokemon and all_pokemon:
            # fallback: return the closest match
            best = min(all_pokemon, key=lambda p: abs(len(norm(p.get('speciesName', ''))) - len(normalized_query)))
            matching_pokemon = [{
                'name': best['speciesId'],
                'readable_name': best['speciesName'],
                'sprite': f"/static/sprites/{best['speciesId']}.png",
                'types': best.get('types', [])
            }]
        
        matching_pokemon = matching_pokemon[:10]  # Limit to 10 results
        
        # Track search if we found results
        if matching_pokemon:
            analytics.track_search(sanitized_query)
        
        return jsonify(matching_pokemon)

    except Exception as e:
        print(f"Search error: {e}")
        if app.config['DEBUG']:
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500
        else:
            return jsonify({'error': 'Internal server error'}), 500

def get_type_effectiveness(types):
    """Calculate type effectiveness for given Pokemon types using PvP multipliers (no immunities in Go PvP)"""
    try:
        # Check if we have cached type data
        type_key = '-'.join(sorted(types))
        if type_key in type_cache:
            cached_data, timestamp = type_cache[type_key]
            if datetime.now() - timestamp < cache_duration:
                return cached_data
        print(f"DEBUG: Processing types: {types}")
        # PvP multipliers
        PVP_WEAK = 1.6
        PVP_RESIST = 0.625
        PVP_DOUBLE_RESIST = 0.391
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
            if 'damage_relations' in type_data:
                print(f"DEBUG: Damage relations for {defending_type}: {type_data['damage_relations']}")
                for relation_name, type_list in type_data['damage_relations'].items():
                    print(f"DEBUG: Processing {relation_name} for {defending_type}")
                    if relation_name == 'double_damage_from':
                        for attacking_type_info in type_list:
                            attacking_type_name = attacking_type_info['name']
                            if attacking_type_name in combined_effectiveness:
                                old_value = combined_effectiveness[attacking_type_name]
                                combined_effectiveness[attacking_type_name] *= PVP_WEAK
                                print(f"DEBUG: {attacking_type_name} vs {defending_type}: {old_value} -> {combined_effectiveness[attacking_type_name]} (WEAK)")
                    elif relation_name == 'half_damage_from':
                        for attacking_type_info in type_list:
                            attacking_type_name = attacking_type_info['name']
                            if attacking_type_name in combined_effectiveness:
                                old_value = combined_effectiveness[attacking_type_name]
                                combined_effectiveness[attacking_type_name] *= PVP_RESIST
                                print(f"DEBUG: {attacking_type_name} vs {defending_type}: {old_value} -> {combined_effectiveness[attacking_type_name]} (RESIST)")
                    # Do NOT process 'no_damage_from' as immunity in Go PvP
            else:
                print(f"ERROR: No 'damage_relations' found for type {defending_type}. type_data: {type_data}")
                continue
        # After processing all types, adjust for double resistance
        for atk_type in all_types:
            # If multiplier is exactly PVP_RESIST * PVP_RESIST, set to PVP_DOUBLE_RESIST
            if abs(combined_effectiveness[atk_type] - (PVP_RESIST * PVP_RESIST)) < 0.01:
                combined_effectiveness[atk_type] = PVP_DOUBLE_RESIST
        print(f"DEBUG: Final effectiveness: {combined_effectiveness}")
        result = {
            'effectiveness': combined_effectiveness,
            'weaknesses': [(type_name, mult) for type_name, mult in combined_effectiveness.items() if mult > 1],
            'resistances': [(type_name, mult) for type_name, mult in combined_effectiveness.items() if mult < 1 and mult > PVP_DOUBLE_RESIST],
            'double_resistances': [(type_name, mult) for type_name, mult in combined_effectiveness.items() if mult <= PVP_DOUBLE_RESIST]
        }
        type_cache[type_key] = (result, datetime.now())
        return result
    except Exception as e:
        print(f"Error getting type effectiveness: {e}")
        import traceback
        traceback.print_exc()
        return get_fallback_effectiveness(types)

def get_fallback_effectiveness(types):
    """Fallback effectiveness calculation if API fails (PvP multipliers, no immunities)"""
    # PvP multipliers
    PVP_WEAK = 1.6
    PVP_NEUTRAL = 1.0
    PVP_RESIST = 0.625
    PVP_DOUBLE_RESIST = 0.391
    PVP_TRIPLE_RESIST = 0.244
    all_types = ['normal', 'fire', 'water', 'electric', 'grass', 'ice', 'fighting', 'poison', 'ground', 'flying', 'psychic', 'bug', 'rock', 'ghost', 'dragon', 'dark', 'steel', 'fairy']
    # Type chart: attacking_type -> defending_type -> multiplier
    effectiveness_chart = {
        'normal': {'rock': PVP_RESIST, 'ghost': PVP_RESIST, 'steel': PVP_RESIST},
        'fire': {'fire': PVP_RESIST, 'water': PVP_RESIST, 'grass': PVP_WEAK, 'ice': PVP_WEAK, 'bug': PVP_WEAK, 'rock': PVP_RESIST, 'dragon': PVP_RESIST, 'steel': PVP_WEAK},
        'water': {'fire': PVP_WEAK, 'water': PVP_RESIST, 'grass': PVP_RESIST, 'ground': PVP_WEAK, 'rock': PVP_WEAK, 'dragon': PVP_RESIST},
        'electric': {'water': PVP_WEAK, 'electric': PVP_RESIST, 'grass': PVP_RESIST, 'ground': PVP_RESIST, 'flying': PVP_WEAK, 'dragon': PVP_RESIST},
        'grass': {'fire': PVP_RESIST, 'water': PVP_WEAK, 'grass': PVP_RESIST, 'poison': PVP_RESIST, 'ground': PVP_WEAK, 'flying': PVP_RESIST, 'bug': PVP_RESIST, 'rock': PVP_WEAK, 'dragon': PVP_RESIST, 'steel': PVP_RESIST},
        'ice': {'fire': PVP_RESIST, 'water': PVP_RESIST, 'grass': PVP_WEAK, 'ice': PVP_RESIST, 'ground': PVP_WEAK, 'flying': PVP_WEAK, 'dragon': PVP_WEAK, 'steel': PVP_RESIST},
        'fighting': {'normal': PVP_WEAK, 'ice': PVP_WEAK, 'rock': PVP_WEAK, 'dark': PVP_WEAK, 'steel': PVP_WEAK, 'poison': PVP_RESIST, 'flying': PVP_RESIST, 'psychic': PVP_RESIST, 'bug': PVP_RESIST, 'fairy': PVP_RESIST},
        'poison': {'grass': PVP_WEAK, 'fairy': PVP_WEAK, 'poison': PVP_RESIST, 'ground': PVP_RESIST, 'rock': PVP_RESIST, 'ghost': PVP_RESIST, 'steel': PVP_RESIST},
        'ground': {'fire': PVP_WEAK, 'electric': PVP_WEAK, 'poison': PVP_WEAK, 'rock': PVP_WEAK, 'steel': PVP_WEAK, 'grass': PVP_RESIST, 'ice': PVP_RESIST, 'bug': PVP_RESIST},
        'flying': {'electric': PVP_RESIST, 'grass': PVP_WEAK, 'fighting': PVP_WEAK, 'bug': PVP_WEAK, 'rock': PVP_RESIST, 'steel': PVP_RESIST},
        'psychic': {'fighting': PVP_WEAK, 'poison': PVP_WEAK, 'psychic': PVP_RESIST, 'steel': PVP_RESIST, 'dark': PVP_RESIST},
        'bug': {'fire': PVP_RESIST, 'grass': PVP_WEAK, 'fighting': PVP_RESIST, 'poison': PVP_RESIST, 'flying': PVP_RESIST, 'psychic': PVP_WEAK, 'ghost': PVP_RESIST, 'dark': PVP_WEAK, 'steel': PVP_RESIST, 'fairy': PVP_RESIST},
        'rock': {'fire': PVP_WEAK, 'ice': PVP_WEAK, 'fighting': PVP_RESIST, 'ground': PVP_RESIST, 'flying': PVP_WEAK, 'bug': PVP_WEAK, 'steel': PVP_RESIST},
        'ghost': {'normal': PVP_RESIST, 'psychic': PVP_WEAK, 'ghost': PVP_WEAK, 'dark': PVP_RESIST},
        'dragon': {'dragon': PVP_WEAK, 'steel': PVP_RESIST, 'fairy': PVP_RESIST},
        'dark': {'fighting': PVP_RESIST, 'psychic': PVP_WEAK, 'ghost': PVP_WEAK, 'dark': PVP_RESIST, 'fairy': PVP_RESIST},
        'steel': {'fire': PVP_RESIST, 'water': PVP_RESIST, 'electric': PVP_RESIST, 'ice': PVP_WEAK, 'rock': PVP_WEAK, 'fairy': PVP_WEAK, 'steel': PVP_RESIST},
        'fairy': {'fire': PVP_RESIST, 'fighting': PVP_WEAK, 'poison': PVP_RESIST, 'dragon': PVP_WEAK, 'dark': PVP_WEAK, 'steel': PVP_RESIST},
    }
    # Start with 1.0 for all types
    combined_effectiveness = {t: 1.0 for t in all_types}
    for defending_type in types:
        for attacking_type in all_types:
            mult = effectiveness_chart.get(attacking_type, {}).get(defending_type, 1.0)
            combined_effectiveness[attacking_type] *= mult
    # Categorize by closest PvP multiplier
    categories = {
        'weaknesses': [],
        'triple_resistances': [],
        'double_resistances': [],
        'resistances': [],
        'neutral': []
    }
    def closest_category(mult):
        # Order: triple, double, single, neutral, weakness
        pvp_vals = [
            (PVP_TRIPLE_RESIST, 'triple_resistances'),
            (PVP_DOUBLE_RESIST, 'double_resistances'),
            (PVP_RESIST, 'resistances'),
            (PVP_NEUTRAL, 'neutral'),
            (PVP_WEAK, 'weaknesses')
        ]
        closest = min(pvp_vals, key=lambda x: abs(mult - x[0]))
        return closest[1], closest[0]
    for t, mult in combined_effectiveness.items():
        cat, val = closest_category(mult)
        categories[cat].append((t, mult))
    print(f"[DEBUG] get_fallback_effectiveness: types={types}\n  combined_effectiveness={combined_effectiveness}\n  weaknesses={categories['weaknesses']}\n  resistances={categories['resistances']}\n  double_resistances={categories['double_resistances']}\n  triple_resistances={categories['triple_resistances']}")
    return {
        'effectiveness': combined_effectiveness,
        'weaknesses': categories['weaknesses'],
        'resistances': categories['resistances'],
        'double_resistances': categories['double_resistances'],
        'triple_resistances': categories['triple_resistances']
    }

@app.route('/api/matchup', methods=['POST'])
def matchup():
    """API endpoint to get matchup analysis between opponent and team"""
    try:
        data = request.get_json()
        opponent_name = data.get('opponent')
        team = data.get('team', [])  # list of up to 3 names
        
        if not opponent_name or not team:
            return jsonify({'error': 'Missing opponent or team data'}), 400
        
        print(f"DEBUG: Matchup request - opponent: {opponent_name}, team: {team}")
        
        # Get opponent data directly from poke_data
        opponent_data = poke_data.get_by_species_id(opponent_name)
        print(f"DEBUG: Opponent data for {opponent_name}: {opponent_data}")
        if not opponent_data:
            opponent_data = poke_data.get_by_name(opponent_name)
            print(f"DEBUG: (Fallback) Opponent data for {opponent_name}: {opponent_data}")
        if not opponent_data:
            return jsonify({'error': f'Opponent not found: {opponent_name}'}), 404
        
        opponent_types = opponent_data.get('types', [])
        print(f"DEBUG: Opponent types: {opponent_types}")
        
        # Get opponent moves
        opponent_moves = poke_data.get_pokemon_moves(opponent_data['speciesId'])
        pvpoke_moveset = pvp_rankings_by_species.get(opponent_data['speciesId'].lower(), {}).get('moveset', [])
        # Normalize PvPoke moveset for matching (upper, lower, underscores, spaces)
        def normalize_move_name(name):
            return name.lower().replace('_', '').replace(' ', '')
        pvpoke_moveset_norm = set([normalize_move_name(m) for m in pvpoke_moveset])
        opponent_pvp_moves = []
        for move in opponent_moves.get('fast_moves', []) + opponent_moves.get('charged_moves', []):
            # Try to match by id or name
            move_id_norm = normalize_move_name(move.get('id', move.get('name', '')))
            move_name_norm = normalize_move_name(move.get('name', ''))
            if move_id_norm in pvpoke_moveset_norm or move_name_norm in pvpoke_moveset_norm:
                opponent_pvp_moves.append({
                    'name': move['name'],
                    'type': move['type'],
                    'move_class': 'fast' if move in opponent_moves.get('fast_moves', []) else 'charged',
                    'power': move.get('power'),
                    'energy': move.get('energy'),
                    'energyGain': move.get('energyGain')
                })
        
        print(f"DEBUG: Opponent moves: {len(opponent_moves.get('fast_moves', []))} fast, {len(opponent_moves.get('charged_moves', []))} charged")

        # Get opponent effectiveness (full type chart)
        opponent_effectiveness = get_fallback_effectiveness(opponent_types)
        
        # Get team info directly from poke_data
        team_infos = []
        for name in team:
            team_data = poke_data.get_by_species_id(name)
            print(f"DEBUG: Team data for {name}: {team_data}")
            if not team_data:
                team_data = poke_data.get_by_name(name)
                print(f"DEBUG: (Fallback) Team data for {name}: {team_data}")
            if team_data:
                team_moves = poke_data.get_pokemon_moves(team_data['speciesId'])
                print(f"DEBUG: Team moves for {team_data['speciesId']}: {team_moves}")
                pvp_moves = []
                for move in team_moves.get('fast_moves', []) + team_moves.get('charged_moves', []):
                    pvp_moves.append({
                        'name': move['name'],
                        'type': move['type'],
                        'move_class': 'fast' if move in team_moves.get('fast_moves', []) else 'charged',
                        'power': move.get('power'),
                        'energy': move.get('energy'),
                        'energyGain': move.get('energyGain')
                    })
                # Add full effectiveness for each team member
                team_effectiveness = get_fallback_effectiveness(team_data.get('types', []))
                team_infos.append({
                    'name': team_data['speciesName'],
                    'types': team_data.get('types', []),
                    'pvp_moves': pvp_moves,
                    'effectiveness': team_effectiveness
                })
            else:
                team_infos.append({
                    'name': name,
                    'types': [],
                    'pvp_moves': [],
                    'effectiveness': get_fallback_effectiveness([])
                })

        # For each opponent move, calculate effectiveness vs each team member
        opponent_moves_vs_team = []
        for move in opponent_pvp_moves:
            move_row = {
                'move': move,
                'vs_team': []
            }
            for t in team_infos:
                t_types = t.get('types', [])
                try:
                    multiplier, label = get_move_effectiveness(move['type'], t_types)
                    move_row['vs_team'].append({
                        'pokemon': t['name'], 
                        'effectiveness': {'multiplier': multiplier, 'label': label}
                    })
                except Exception as move_error:
                    print(f"DEBUG: Error calculating move effectiveness for {move['type']} vs {t_types}: {move_error}")
                    move_row['vs_team'].append({
                        'pokemon': t['name'], 
                        'effectiveness': {'multiplier': 1.0, 'label': 'Neutral'}
                    })
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
                try:
                    multiplier, label = get_move_effectiveness(move['type'], opponent_types)
                    t_row['moves'].append({
                        'move': move,
                        'effectiveness': {'multiplier': multiplier, 'label': label}
                    })
                except Exception as move_error:
                    print(f"DEBUG: Error calculating move effectiveness for {move['type']} vs {opponent_types}: {move_error}")
                    t_row['moves'].append({
                        'move': move,
                        'effectiveness': {'multiplier': 1.0, 'label': 'Neutral'}
                    })
            team_moves_vs_opponent.append(t_row)

        return jsonify({
            'opponent': opponent_name,
            'opponent_types': opponent_types,
            'opponent_effectiveness': opponent_effectiveness,
            'team': team,
            'team_infos': team_infos,
            'opponent_moves_vs_team': opponent_moves_vs_team,
            'team_moves_vs_opponent': team_moves_vs_opponent
        })
        
    except Exception as e:
        print(f"ERROR in matchup: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

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
        p1_shield_ai = data.get('p1_shield_ai', 'smart_30')  # Default shield AI strategy
        p2_shield_ai = data.get('p2_shield_ai', 'smart_30')  # Default shield AI strategy
        settings = data.get('settings', {})
        cp_cap = data.get('cp_cap', 1500)  # Default to Great League
        
        # Validate input
        if not p1_id or not p2_id or not p1_moves or not p2_moves:
            return jsonify({'error': 'Missing required parameters'}), 400
        
        # Validate CP cap
        if cp_cap not in [0, 500, 1500, 2500]:
            return jsonify({'error': 'Invalid CP cap. Supported values: 0 (Master League), 500, 1500, 2500'}), 400
        
        # Validate shield AI strategies
        valid_shield_strategies = ['never', 'always', 'smart_20', 'smart_30', 'smart_50', 'conservative', 'aggressive', 'balanced']
        if p1_shield_ai not in valid_shield_strategies:
            return jsonify({'error': f'Invalid p1_shield_ai strategy. Supported values: {valid_shield_strategies}'}), 400
        if p2_shield_ai not in valid_shield_strategies:
            return jsonify({'error': f'Invalid p2_shield_ai strategy. Supported values: {valid_shield_strategies}'}), 400
        
        # Get Pokémon data
        p1 = poke_data.get_by_species_id(p1_id)
        p2 = poke_data.get_by_species_id(p2_id)
        
        if not p1 or not p2:
            return jsonify({'error': 'Pokemon not found'}), 404
        
        # Validate moves
        p1_available_moves = poke_data.get_pokemon_moves(p1_id)
        p2_available_moves = poke_data.get_pokemon_moves(p2_id)
        
        print(f"[DEBUG] P1 available moves: {p1_available_moves}")
        print(f"[DEBUG] P2 available moves: {p2_available_moves}")
        print(f"[DEBUG] P1 moves received: {p1_moves}")
        print(f"[DEBUG] P2 moves received: {p2_moves}")
        
        # Check if selected moves are valid
        if not _validate_moveset(p1_moves, p1_available_moves):
            print(f"[DEBUG] P1 moveset validation failed: {p1_moves}")
            print(f"[DEBUG] P1 available move IDs: {[m['id'] for m in p1_available_moves.get('fast_moves', []) + p1_available_moves.get('charged_moves', [])]}")
            return jsonify({'error': f'Invalid moveset for {p1_id}'}), 400
        if not _validate_moveset(p2_moves, p2_available_moves):
            print(f"[DEBUG] P2 moveset validation failed: {p2_moves}")
            print(f"[DEBUG] P2 available move IDs: {[m['id'] for m in p2_available_moves.get('fast_moves', []) + p2_available_moves.get('charged_moves', [])]}")
            return jsonify({'error': f'Invalid moveset for {p2_id}'}), 400
        
        # Update settings with shield AI strategies
        battle_settings = settings.copy()
        battle_settings['p1_shield_ai'] = p1_shield_ai
        battle_settings['p2_shield_ai'] = p2_shield_ai
        
        # Run battle simulation
        print(f"[DEBUG] Running battle simulation for CP cap: {cp_cap}")
        print(f"[DEBUG] P1 shield AI: {p1_shield_ai}, P2 shield AI: {p2_shield_ai}")
        print(f"[DEBUG] P1 moves received: {p1_moves}")
        print(f"[DEBUG] P2 moves received: {p2_moves}")
        result = battle_simulator.simulate(
            p1_data=p1,
            p2_data=p2,
            p1_moves=p1_moves,
            p2_moves=p2_moves,
            p1_shields=p1_shields,
            p2_shields=p2_shields,
            settings=battle_settings
        )
        
        # Track unique battle (full team vs opponent, including moves and league)
        team_ids = data.get('team_ids') or [p1_id]  # Try to get full team from frontend, fallback to just p1_id
        team_moves = data.get('team_moves') or {p1_id: p1_moves}  # Dict of {id: moves}
        opponent_moves = p2_moves
        # If team_ids not provided, try to infer from context (for now, just use p1_id)
        analytics.track_unique_battle(
            team=team_ids,
            team_moves=team_moves,
            opponent=p2_id,
            opponent_moves=opponent_moves,
            league=f"CP{cp_cap}" if cp_cap > 0 else "Master League",
            ip=request.remote_addr
        )
        
        # Add Pokémon names, CP cap, and shield AI strategies to result for frontend
        result['p1_name'] = p1['speciesName']
        result['p2_name'] = p2['speciesName']
        result['p1_species_id'] = p1['speciesId']
        result['p2_species_id'] = p2['speciesId']
        result['cp_cap'] = cp_cap
        result['p1_shield_ai'] = p1_shield_ai
        result['p2_shield_ai'] = p2_shield_ai
        
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
        # Security: Validate and sanitize input
        if not validate_pokemon_name(name):
            return jsonify({'error': 'Invalid Pokemon name'}), 400
        
        sanitized_name = sanitize_pokemon_name(name)
        
        # Try to match by speciesId first, then by name
        p = poke_data.get_by_species_id(sanitized_name)
        if not p:
            p = poke_data.get_by_species_id(sanitized_name)
        if not p:
            return jsonify({'error': 'Pokemon not found'}), 404
        
        # Get all available moves
        moves_data = poke_data.get_pokemon_moves(p['speciesId'])
        
        # Get best moveset from PvPoke rankings
        pvpoke_data = pvp_rankings_by_species.get(p['speciesId'].lower(), {})
        best_moveset = pvpoke_data.get('moveset', [])
        
        # Convert PvPoke moveset to the expected format
        formatted_best_moveset = {}
        if best_moveset and len(best_moveset) >= 3:
            # PvPoke format: ["FAST_MOVE", "CHARGED_MOVE1", "CHARGED_MOVE2"]
            formatted_best_moveset = {
                'fast': best_moveset[0].lower().replace('_', ' '),
                'charged1': best_moveset[1].lower().replace('_', ' '),
                'charged2': best_moveset[2].lower().replace('_', ' ')
            }
        else:
            # Fallback to first available moves
            formatted_best_moveset = {
                'fast': moves_data['fast_moves'][0]['name'] if moves_data['fast_moves'] else None,
                'charged1': moves_data['charged_moves'][0]['name'] if moves_data['charged_moves'] else None,
                'charged2': moves_data['charged_moves'][1]['name'] if len(moves_data['charged_moves']) > 1 else None
            }
        
        # Calculate DPE for charged moves
        for move in moves_data['charged_moves']:
            if 'power' in move and 'energy' in move and move['energy'] > 0:
                move['dpe'] = round(move['power'] / move['energy'], 2)
        
        return jsonify({
            'pokemon': {
                'species_id': p['speciesId'],
                'species_name': p['speciesName'],
                'types': p.get('types', []),
                'sprite': f"/static/sprites/{p['speciesId']}.png"
            },
            'fast_moves': moves_data['fast_moves'],
            'charged_moves': moves_data['charged_moves'],
            'best_moveset': formatted_best_moveset
        })
        
    except Exception as e:
        # Security: Don't expose internal error details in production
        if app.config['DEBUG']:
            return jsonify({'error': f'Failed to get moves: {str(e)}'}), 500
        else:
            return jsonify({'error': 'Failed to get moves'}), 500

@app.route('/api/shield-strategies')
def get_shield_strategies():
    """Get available shield AI strategies"""
    from battle_sim import ShieldAI
    return jsonify({
        'strategies': ShieldAI.STRATEGIES,
        'default': 'smart_30'
    })

@app.route('/api/pokemon/<name>/update-moves', methods=['POST'])
def update_pokemon_moves(name):
    """Update moves for a Pokémon and return updated data"""
    try:
        # Security: Validate and sanitize input
        if not validate_pokemon_name(name):
            return jsonify({'error': 'Invalid Pokemon name'}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        new_moves = data.get('moves', {})
        pokemon_type = data.get('type', 'team')  # 'team' or 'opponent'
        
        sanitized_name = sanitize_pokemon_name(name)
        
        # Get Pokémon data
        p = poke_data.get_by_species_id(sanitized_name)
        if not p:
            p = poke_data.get_by_name(sanitized_name)
        if not p:
            return jsonify({'error': 'Pokemon not found'}), 404
        
        # Get all available moves
        moves_data = poke_data.get_pokemon_moves(p['speciesId'])
        
        # Validate the new moves
        if not _validate_moveset(new_moves, moves_data):
            return jsonify({'error': 'Invalid moveset'}), 400
        
        # Get types
        types = [t for t in p.get('types', []) if t and t != 'none']
        
        # Get type effectiveness
        effectiveness = get_fallback_effectiveness(types)
        
        # Get PvP moves with the new moveset
        pvp_moves = []
        for move in moves_data.get('fast_moves', []) + moves_data.get('charged_moves', []):
            pvp_moves.append({
                'name': move['name'],
                'type': move['type'],
                'move_class': move.get('move_class', 'fast' if move in moves_data.get('fast_moves', []) else 'charged'),
                'dpe': None,
                'power': move.get('power', 0),
                'energy': move.get('energy', 0)
            })
        
        # Calculate effectiveness for each move
        for move in pvp_moves:
            if move['type']:
                mult, label = get_move_effectiveness(move['type'], types)
                move['effectiveness'] = {'multiplier': mult, 'label': label}
            else:
                move['effectiveness'] = {'multiplier': 1.0, 'label': 'Neutral'}
        
        # Get PvPoke rankings data
        pvpoke_data = pvp_rankings_by_species.get(p.get('speciesId', '').lower(), {})
        
        # Format the response
        formatted_data = {
            'id': p.get('dex'),
            'name': p.get('speciesName'),
            'speciesId': p.get('speciesId'),
            'types': types,
            'stats': p.get('baseStats', {}),
            'effectiveness': effectiveness,
            'moves': [],  # Basic moves list
            'pvp_moves': pvp_moves,
            'pvpoke_moveset': pvpoke_data.get('moveset', []),
            'pvpoke_rating': pvpoke_data.get('rating', 0),
            'pvpoke_score': pvpoke_data.get('score', 0),
            'sprite': f"/static/sprites/{p.get('speciesId')}.png",
            'custom_moveset': new_moves  # Store the custom moveset
        }
        
        return jsonify(formatted_data)
        
    except Exception as e:
        if app.config['DEBUG']:
            return jsonify({'error': f'Failed to update moves: {str(e)}'}), 500
        else:
            return jsonify({'error': 'Failed to update moves'}), 500

@app.route('/api/league/<cp_cap>', methods=['POST'])
def change_league(cp_cap):
    """API endpoint to change the CP cap/league and reload PvP data"""
    try:
        # Validate CP cap
        try:
            cp_cap_int = int(cp_cap)
            if cp_cap_int not in [0, 500, 1500, 2500]:
                return jsonify({'error': 'Invalid CP cap. Supported values: 0 (Master League), 500, 1500, 2500'}), 400
        except ValueError:
            return jsonify({'error': 'Invalid CP cap format'}), 400
        
        # Reload PvP rankings for the new CP cap
        reload_pvp_rankings_for_cap(cp_cap_int)
        
        # Also reload PokeData with the new CP cap
        global poke_data, battle_simulator
        poke_data = PokeData(cp_cap=cp_cap_int)
        
        # Update the battle simulator with the new PokeData
        battle_simulator = BattleSimulator(poke_data)
        
        return jsonify({
            'success': True,
            'cp_cap': cp_cap_int,
            'message': f'Switched to CP {cp_cap_int} league'
        })
        
    except Exception as e:
        print(f"Error changing league to CP {cp_cap}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/analytics')
def get_analytics():
    """Get analytics statistics (admin only)"""
    try:
        # For now, allow access to analytics (you can add authentication later)
        stats = analytics.get_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': f'Failed to get analytics: {str(e)}'}), 500

ANALYTICS_PASSWORD = os.environ.get("ANALYTICS_PASSWORD", "changeme")

@app.route('/analytics', methods=['GET', 'POST'])
def analytics_dashboard():
    error = None
    if session.get('analytics_auth'):
        return render_template('analytics.html')
    if request.method == 'POST':
        if request.form.get('password') == ANALYTICS_PASSWORD:
            session['analytics_auth'] = True
            return redirect(url_for('analytics_dashboard'))
        else:
            error = 'Wrong password!'
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Analytics Login</title>
    <link rel="icon" type="image/svg+xml" href="{{ url_for('static', filename='favicon.svg') }}">
    <style>
        body {
            background: #f4f6fa;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0;
        }
        .modal {
            background: white;
            border-radius: 16px;
            box-shadow: 0 8px 32px rgba(44,62,80,0.15);
            padding: 2.5rem 2rem 2rem 2rem;
            max-width: 350px;
            width: 100%;
            text-align: center;
            position: relative;
        }
        .modal h2 {
            margin-top: 0;
            color: #2c3e50;
            font-size: 1.5rem;
            margin-bottom: 1.2rem;
        }
        .modal form {
            display: flex;
            flex-direction: column;
            gap: 1.2rem;
        }
        .modal input[type="password"] {
            padding: 0.7rem 1rem;
            border-radius: 8px;
            border: 1px solid #d1d5db;
            font-size: 1rem;
            outline: none;
            transition: border 0.2s;
        }
        .modal input[type="password"]:focus {
            border: 1.5px solid #3498db;
        }
        .modal button {
            background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.7rem 1rem;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s;
        }
        .modal button:hover {
            background: linear-gradient(135deg, #2980b9 0%, #3498db 100%);
        }
        .error {
            color: #e74c3c;
            margin-bottom: 0.5rem;
            font-size: 1rem;
        }
        .modal .lock {
            font-size: 2.5rem;
            color: #3498db;
            margin-bottom: 0.5rem;
        }
    </style>
</head>
<body>
    <div class="modal">
        <div class="lock">🔒</div>
        <h2>Analytics Login</h2>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        <form method="post">
            <input type="password" name="password" placeholder="Enter password" autofocus required>
            <button type="submit">Unlock</button>
        </form>
    </div>
</body>
</html>
''', error=error)

# Security: Add security headers
@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: blob:;"
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response

if __name__ == '__main__':
    print("Starting Pokemon PvP Helper...")
    print("Open your browser and go to: http://localhost:5000")
    # Security: Use environment variable for debug mode
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=5000) 
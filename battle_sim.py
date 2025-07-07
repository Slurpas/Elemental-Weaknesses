import math
import random
from typing import Dict, Any, List, Optional, Tuple
from poke_data import PokeData

class ShieldAI:
    """Intelligent shield decision making for PvP battles"""
    
    STRATEGIES = {
        'never': 'Never shield',
        'always': 'Always shield charged moves',
        'smart_20': 'Shield if damage > 20% of current HP',
        'smart_30': 'Shield if damage > 30% of current HP', 
        'smart_50': 'Shield if damage > 50% of current HP',
        'conservative': 'Conservative - shield if damage > 40% of current HP or if low on HP',
        'aggressive': 'Aggressive - shield if damage > 25% of current HP or if move is super effective',
        'balanced': 'Balanced - shield if damage > 35% of current HP or if move is super effective'
    }
    
    def __init__(self, strategy: str = 'smart_30'):
        """
        Initialize shield AI with a strategy
        
        Args:
            strategy: One of the STRATEGIES keys
        """
        if strategy not in self.STRATEGIES:
            raise ValueError(f"Invalid shield strategy: {strategy}. Valid options: {list(self.STRATEGIES.keys())}")
        
        self.strategy = strategy
    
    def should_shield(self, damage: int, current_hp: int, max_hp: int, 
                     move_type: str, defender_types: List[str], 
                     remaining_shields: int, is_charged_move: bool = True) -> bool:
        """
        Decide whether to use a shield
        
        Args:
            damage: Incoming damage
            current_hp: Current HP of the defender
            max_hp: Maximum HP of the defender
            move_type: Type of the incoming move
            defender_types: Types of the defender
            remaining_shields: Number of shields left
            is_charged_move: Whether this is a charged move (always True for shield decisions)
        
        Returns:
            True if should shield, False otherwise
        """
        if remaining_shields <= 0 or not is_charged_move:
            return False
        
        # Calculate damage as percentage of current HP
        damage_percent = (damage / current_hp) * 100 if current_hp > 0 else 0
        hp_percent = (current_hp / max_hp) * 100 if max_hp > 0 else 0
        
        # Check type effectiveness
        effectiveness = TypeChart.get_effectiveness(move_type, defender_types)
        is_super_effective = effectiveness > 1.0
        
        if self.strategy == 'never':
            return False
        
        elif self.strategy == 'always':
            return True
        
        elif self.strategy == 'smart_20':
            return damage_percent > 20
        
        elif self.strategy == 'smart_30':
            return damage_percent > 30
        
        elif self.strategy == 'smart_50':
            return damage_percent > 50
        
        elif self.strategy == 'conservative':
            # Shield if damage > 40% of current HP or if low on HP (< 30%) and damage > 20%
            return damage_percent > 40 or (hp_percent < 30 and damage_percent > 20)
        
        elif self.strategy == 'aggressive':
            # Shield if damage > 25% of current HP or if move is super effective and damage > 15%
            return damage_percent > 25 or (is_super_effective and damage_percent > 15)
        
        elif self.strategy == 'balanced':
            # Shield if damage > 35% of current HP or if move is super effective and damage > 20%
            return damage_percent > 35 or (is_super_effective and damage_percent > 20)
        
        # Default fallback
        return damage_percent > 30

class DamageMultiplier:
    """PvPoke damage multipliers"""
    BONUS = 1.2999999523162841796875
    SUPER_EFFECTIVE = 1.60000002384185791015625
    RESISTED = 0.625
    DOUBLE_RESISTED = 0.390625  # 0.625 * 0.625 (no immunities in Go PvP)
    STAB = 1.2000000476837158203125
    SHADOW_ATK = 1.2
    SHADOW_DEF = 0.83333331

class TypeChart:
    """PvPoke type effectiveness chart"""
    TYPE_TRAITS = {
        # Note: In Pokémon Go PvP, there are no immunities - only resistances and double resistances
        "normal": {"weaknesses": ["fighting"], "resistances": [], "double_resistances": ["ghost"]},
        "fighting": {"weaknesses": ["flying", "psychic", "fairy"], "resistances": ["rock", "bug", "dark"], "double_resistances": []},
        "flying": {"weaknesses": ["rock", "electric", "ice"], "resistances": ["fighting", "bug", "grass"], "double_resistances": ["ground"]},
        "poison": {"weaknesses": ["ground", "psychic"], "resistances": ["fighting", "poison", "bug", "fairy", "grass"], "double_resistances": []},
        "ground": {"weaknesses": ["water", "grass", "ice"], "resistances": ["poison", "rock"], "double_resistances": ["electric"]},
        "rock": {"weaknesses": ["fighting", "ground", "steel", "water", "grass"], "resistances": ["normal", "flying", "poison", "fire"], "double_resistances": []},
        "bug": {"weaknesses": ["flying", "rock", "fire"], "resistances": ["fighting", "ground", "grass"], "double_resistances": []},
        "ghost": {"weaknesses": ["ghost", "dark"], "resistances": ["poison", "bug"], "double_resistances": ["normal", "fighting"]},
        "steel": {"weaknesses": ["fighting", "ground", "fire"], "resistances": ["normal", "flying", "rock", "bug", "steel", "grass", "psychic", "ice", "dragon", "fairy"], "double_resistances": ["poison"]},
        "fire": {"weaknesses": ["ground", "rock", "water"], "resistances": ["bug", "steel", "fire", "grass", "ice", "fairy"], "double_resistances": []},
        "water": {"weaknesses": ["grass", "electric"], "resistances": ["steel", "fire", "water", "ice"], "double_resistances": []},
        "grass": {"weaknesses": ["flying", "poison", "bug", "fire", "ice"], "resistances": ["ground", "water", "grass", "electric"], "double_resistances": []},
        "electric": {"weaknesses": ["ground"], "resistances": ["flying", "steel", "electric"], "double_resistances": []},
        "psychic": {"weaknesses": ["bug", "ghost", "dark"], "resistances": ["fighting", "psychic"], "double_resistances": []},
        "ice": {"weaknesses": ["fighting", "fire", "steel", "rock"], "resistances": ["ice"], "double_resistances": []},
        "dragon": {"weaknesses": ["dragon", "ice", "fairy"], "resistances": ["fire", "water", "grass", "electric"], "double_resistances": []},
        "dark": {"weaknesses": ["fighting", "fairy", "bug"], "resistances": ["ghost", "dark"], "double_resistances": ["psychic"]},
        "fairy": {"weaknesses": ["poison", "steel"], "resistances": ["fighting", "bug", "dark"], "double_resistances": ["dragon"]}
    }

    @classmethod
    def get_effectiveness(cls, move_type: str, target_types: List[str]) -> float:
        """Calculate type effectiveness multiplier"""
        effectiveness = 1.0
        move_type = move_type.lower()
        
        for target_type in target_types:
            target_type = target_type.lower()
            if target_type not in cls.TYPE_TRAITS:
                continue
                
            traits = cls.TYPE_TRAITS[target_type]
            
            if move_type in traits["weaknesses"]:
                effectiveness *= DamageMultiplier.SUPER_EFFECTIVE
            elif move_type in traits["resistances"]:
                effectiveness *= DamageMultiplier.RESISTED
            elif move_type in traits["double_resistances"]:
                effectiveness *= DamageMultiplier.DOUBLE_RESISTED
                
        return effectiveness

class BattlePokemon:
    """Represents a Pokémon in battle with current state"""
    def __init__(self, pokemon_data: Dict[str, Any], moves: Dict[str, str], shields: int = 2, poke_data: PokeData = None):
        self.data = pokemon_data
        self.moves = moves
        self.shields = shields
        self.poke_data = poke_data or PokeData()
        print(f"[DEBUG] BattlePokemon created: {self.data.get('speciesId', 'unknown')} id={id(self)} shields={self.shields}")

        # Use PvPoke rank 1 stats if available
        self.species_id = self.data.get('speciesId') or self.data.get('name', '').lower().replace(' ', '_')
        self.rank1_stats = self.poke_data.get_rank1_stats(self.species_id)
        print(f"[DEBUG] Rank1 stats for {self.species_id}: {self.rank1_stats}")
        if self.rank1_stats:
            if 'atk' not in self.rank1_stats:
                print(f"[ERROR] Missing 'atk' key in rank1_stats for {self.species_id}. Available keys: {list(self.rank1_stats.keys())}")
                # Fallback to old calculation
                base_stats = self.data.get("baseStats", {})
                hp_base = base_stats.get("hp", 100)
                atk_base = base_stats.get("atk", 100)
                defense_base = base_stats.get("def", 100)
                hp_iv = atk_iv = defense_iv = 15
                level = 40
                self.atk = (atk_base + atk_iv) * (0.5 + level * 0.01)
                self.defense = (defense_base + defense_iv) * (0.5 + level * 0.01)
                self.hp = int((hp_base + hp_iv) * (0.5 + level * 0.01))
                self.max_hp = self.hp
                self.ivs = {'atk': atk_iv, 'def': defense_iv, 'sta': hp_iv}
                self.stat_product = self.atk * self.defense * self.hp
                self.level = level
                self.iv_atk = atk_iv
                self.iv_def = defense_iv
                self.iv_sta = hp_iv
                print(f"[DEBUG] Using fallback stats for {self.species_id}: ATK={self.atk}, DEF={self.defense}, HP={self.hp}, Level={self.level}, IVs=({self.iv_atk}/{self.iv_def}/{self.iv_sta}), Stat Product={self.stat_product}")
            else:
                self.atk = self.rank1_stats['atk']
                self.defense = self.rank1_stats['def']
                self.hp = self.rank1_stats['hp']
                self.max_hp = self.hp
                self.ivs = self.rank1_stats.get('ivs', {})
                self.stat_product = self.rank1_stats.get('product')
                self.level = self.rank1_stats.get('level')
                self.iv_atk = self.rank1_stats.get('iv_atk')
                self.iv_def = self.rank1_stats.get('iv_def')
                self.iv_sta = self.rank1_stats.get('iv_sta')
                print(f"[DEBUG] Using PvPoke rank 1 stats for {self.species_id}: ATK={self.atk}, DEF={self.defense}, HP={self.hp}, Level={self.level}, IVs=({self.iv_atk}/{self.iv_def}/{self.iv_sta}), Stat Product={self.stat_product}")
        else:
            # Fallback to old calculation
            base_stats = self.data.get("baseStats", {})
            hp_base = base_stats.get("hp", 100)
            atk_base = base_stats.get("atk", 100)
            defense_base = base_stats.get("def", 100)
            hp_iv = atk_iv = defense_iv = 15
            level = 40
            self.atk = (atk_base + atk_iv) * (0.5 + level * 0.01)
            self.defense = (defense_base + defense_iv) * (0.5 + level * 0.01)
            self.hp = int((hp_base + hp_iv) * (0.5 + level * 0.01))
            self.max_hp = self.hp
            self.ivs = {'atk': atk_iv, 'def': defense_iv, 'sta': hp_iv}
            self.stat_product = self.atk * self.defense * self.hp
            self.level = level
            self.iv_atk = atk_iv
            self.iv_def = defense_iv
            self.iv_sta = hp_iv
            print(f"[DEBUG] Using fallback stats for {self.species_id}: ATK={self.atk}, DEF={self.defense}, HP={self.hp}, Level={self.level}, IVs=({self.iv_atk}/{self.iv_def}/{self.iv_sta}), Stat Product={self.stat_product}")

        # Battle state
        self.energy = 0
        self.max_energy = 100
        # Stats with buffs/debuffs
        self.atk_buffs = 0  # -4 to +4
        self.def_buffs = 0  # -4 to +4
        # Shadow multipliers
        self.shadow_atk_mult = 1.0
        self.shadow_def_mult = 1.0
        if "shadow" in pokemon_data.get("tags", []):
            self.shadow_atk_mult = DamageMultiplier.SHADOW_ATK
            self.shadow_def_mult = DamageMultiplier.SHADOW_DEF
        # Move objects
        self.fast_move = None
        self.charged_moves = []
        self._initialize_moves()
    
    def _initialize_moves(self):
        """Initialize move objects from move IDs"""
        print(f"[DEBUG] Initializing moves for {self.data['speciesId']}: {self.moves}")
        
        if "fast" in self.moves:
            self.fast_move = self.poke_data.get_move_details(self.moves["fast"])
            print(f"[DEBUG] Fast move: {self.moves['fast']} -> {self.fast_move['name'] if self.fast_move else 'NOT FOUND'}")
            if self.fast_move:
                print(f"[DEBUG] Fast move details: power={self.fast_move.get('power', 'N/A')}, energy={self.fast_move.get('energy', 'N/A')}, energyGain={self.fast_move.get('energyGain', 'N/A')}")
        
        for i in range(1, 3):
            key = f"charged{i}"
            if key in self.moves:
                move_data = self.poke_data.get_move_details(self.moves[key])
                if move_data:
                    self.charged_moves.append(move_data)
                    print(f"[DEBUG] Charged move {i}: {self.moves[key]} -> {move_data['name']} (power: {move_data.get('power', 'N/A')}, energy: {move_data.get('energy', 'N/A')})")
                else:
                    print(f"[DEBUG] Charged move {i}: {self.moves[key]} -> NOT FOUND")
                    print(f"[DEBUG] Available move IDs: {list(self.poke_data.moves_by_id.keys())[:10]}...")  # Show first 10 for debugging
        
        print(f"[DEBUG] Final charged moves for {self.data['speciesId']}: {[m['name'] for m in self.charged_moves]}")
        print(f"[DEBUG] Final charged moves details for {self.data['speciesId']}: {[(m['name'], m.get('power', 'N/A'), m.get('energy', 'N/A')) for m in self.charged_moves]}")
    
    def get_effective_atk(self) -> float:
        """Get effective attack stat with buffs and shadow multiplier"""
        buff_mult = self._get_buff_multiplier(self.atk_buffs)
        return self.atk * self.shadow_atk_mult * buff_mult
    
    def get_effective_def(self) -> float:
        """Get effective defense stat with buffs and shadow multiplier"""
        buff_mult = self._get_buff_multiplier(self.def_buffs)
        return self.defense * self.shadow_def_mult * buff_mult
    
    def _get_buff_multiplier(self, buff_stage: int) -> float:
        """Get stat multiplier from buff stage (-4 to +4)"""
        if buff_stage >= 0:
            return (2 + buff_stage) / 2
        else:
            return 2 / (2 - buff_stage)
    
    def apply_buff(self, atk_change: int, def_change: int):
        """Apply buff/debuff to stats"""
        self.atk_buffs = max(-4, min(4, self.atk_buffs + atk_change))
        self.def_buffs = max(-4, min(4, self.def_buffs + def_change))
    
    def take_damage(self, damage: int):
        """Take damage and update HP"""
        old_hp = self.hp
        self.hp = max(0, self.hp - damage)
        print(f"[DEBUG] {self.data['speciesId']} took {damage} damage: {old_hp} -> {self.hp} HP")
    
    def gain_energy(self, energy: int):
        """Gain energy"""
        self.energy = min(self.max_energy, self.energy + energy)
    
    def use_energy(self, energy: int):
        """Use energy for charged move"""
        self.energy = max(0, self.energy - energy)
    
    def use_shield(self):
        """Use a shield"""
        if self.shields > 0:
            old_shields = self.shields
            self.shields -= 1
            print(f"[DEBUG] {self.data['speciesId']} used shield: {old_shields} -> {self.shields} (id={id(self)})")
            return True
        print(f"[DEBUG] {self.data['speciesId']} tried to use shield but has {self.shields} shields (id={id(self)})")
        return False
    
    def is_fainted(self) -> bool:
        """Check if Pokémon is fainted"""
        return self.hp <= 0
    
    def get_available_charged_moves(self) -> List[Dict[str, Any]]:
        """Get charged moves that can be used with current energy"""
        return [move for move in self.charged_moves if self.energy >= move["energy"]]

class BattleSimulator:
    def __init__(self, poke_data: PokeData):
        self.poke_data = poke_data
        # Default shield AI strategies for each player
        self.p1_shield_ai = ShieldAI('smart_30')
        self.p2_shield_ai = ShieldAI('smart_30')

    def simulate(self, p1_data: Dict[str, Any], p2_data: Dict[str, Any],
                 p1_moves: Dict[str, str], p2_moves: Dict[str, str],
                 p1_shields: int = 2, p2_shields: int = 2,
                 settings: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Simulate a full PvP battle between two Pokémon.
        
        Args:
            p1_data, p2_data: Pokémon dicts from poke_data
            p1_moves, p2_moves: {'fast': move_id, 'charged1': move_id, 'charged2': move_id}
            p1_shields, p2_shields: Number of shields for each Pokémon
            settings: Battle settings (CP cap, level, etc.)
        
        Returns:
            Detailed battle result with winner, timeline, stats, etc.
        """
        print(f"[BATTLE SIM DEBUG] Starting simulation with moves:")
        print(f"[BATTLE SIM DEBUG] P1 moves: {p1_moves}")
        print(f"[BATTLE SIM DEBUG] P2 moves: {p2_moves}")
        
        # Get shield AI strategies from settings
        p1_shield_strategy = settings.get('p1_shield_ai', 'smart_30') if settings else 'smart_30'
        p2_shield_strategy = settings.get('p2_shield_ai', 'smart_30') if settings else 'smart_30'
        
        # Update shield AI strategies
        self.p1_shield_ai = ShieldAI(p1_shield_strategy)
        self.p2_shield_ai = ShieldAI(p2_shield_strategy)
        
        # Initialize battle Pokémon with poke_data for rank 1 stats
        p1 = BattlePokemon(p1_data, p1_moves, p1_shields, poke_data=self.poke_data)
        p2 = BattlePokemon(p2_data, p2_moves, p2_shields, poke_data=self.poke_data)
        
        # Store references to determine which player is which
        self.p1_pokemon = p1
        self.p2_pokemon = p2
        print(f"[DEBUG] BattleSimulator: p1 id={id(p1)}, p2 id={id(p2)}")
        
        # Battle state
        turn = 0
        timeline = []
        
        # Main battle loop
        while not p1.is_fainted() and not p2.is_fainted():
            turn += 1
            print(f"[BATTLE SIM DEBUG] Turn {turn} - P1 HP: {p1.hp}, P2 HP: {p2.hp}")
            
            # Process fast moves
            p1_fast_result = self._process_fast_move(p1, p2, turn)
            p2_fast_result = self._process_fast_move(p2, p1, turn)
            
            timeline.extend([p1_fast_result, p2_fast_result])
            
            # Check for fainting after fast moves
            if p1.is_fainted() or p2.is_fainted():
                break
            
            # Process charged moves (AI decision)
            p1_charged_result = self._process_charged_move(p1, p2, turn)
            p2_charged_result = self._process_charged_move(p2, p1, turn)
            
            if p1_charged_result:
                timeline.append(p1_charged_result)
                print(f"[BATTLE SIM DEBUG] P1 used charged move: {p1_charged_result.get('move', 'Unknown')}")
            if p2_charged_result:
                timeline.append(p2_charged_result)
                print(f"[BATTLE SIM DEBUG] P2 used charged move: {p2_charged_result.get('move', 'Unknown')}")
            
            # Check for fainting after charged moves
            if p1.is_fainted() or p2.is_fainted():
                break
        
        # Determine winner and calculate battle rating
        winner, battle_rating = self._determine_winner(p1, p2)
        print(f"[DEBUG] Battle finished. Winner: {winner}, P1 HP: {p1.hp}/{p1.max_hp}, P2 HP: {p2.hp}/{p2.max_hp}, Battle rating: {battle_rating}")
        # Debug: Show final shield counts
        print(f"[DEBUG] Final shield counts - P1 ({p1.data['speciesId']} id={id(p1)}): {p1.shields}, P2 ({p2.data['speciesId']} id={id(p2)}): {p2.shields}")
        return {
            "winner": winner,
            "p1_final_hp": p1.hp,
            "p2_final_hp": p2.hp,
            "p1_max_hp": p1.max_hp,
            "p2_max_hp": p2.max_hp,
            "p1_final_energy": p1.energy,
            "p2_final_energy": p2.energy,
            "p1_final_shields": p1.shields,
            "p2_final_shields": p2.shields,
            "turns": turn,
            "timeline": timeline,
            "battle_rating": battle_rating,
            "p1_final_buffs": {"atk": p1.atk_buffs, "def": p1.def_buffs},
            "p2_final_buffs": {"atk": p2.atk_buffs, "def": p2.def_buffs}
        }
    
    def _process_fast_move(self, attacker: BattlePokemon, defender: BattlePokemon, turn: int) -> Dict[str, Any]:
        """Process a fast move and return timeline entry"""
        if not attacker.fast_move:
            return {"turn": turn, "type": "fast", "attacker": attacker.data["speciesId"], "error": "No fast move"}
        
        move = attacker.fast_move
        
        # Calculate damage
        damage = self._calculate_damage(attacker, defender, move)
        
        # Apply damage
        defender.take_damage(damage)
        
        # Gain energy
        attacker.gain_energy(move["energyGain"])
        
        # Apply buffs if any
        buff_applied = False
        if move.get("buffs") and move.get("buffTarget") == "self":
            chance = float(move.get("buffApplyChance", "0"))
            if random.random() < chance:
                attacker.apply_buff(move["buffs"][0], move["buffs"][1])
                buff_applied = True
        
        return {
            "turn": turn,
            "type": "fast",
            "attacker": attacker.data["speciesId"],
            "defender": defender.data["speciesId"],
            "move": move["name"],
            "damage": damage,
            "energy_gained": move["energyGain"],
            "defender_hp_remaining": defender.hp,
            "attacker_energy": attacker.energy,
            "buff_applied": buff_applied
        }
    
    def _process_charged_move(self, attacker: BattlePokemon, defender: BattlePokemon, turn: int) -> Optional[Dict[str, Any]]:
        """Process a charged move (AI decision) and return timeline entry"""
        available_moves = attacker.get_available_charged_moves()
        if not available_moves:
            return None
        
        print(f"[DEBUG] {attacker.data['speciesId']} has {len(available_moves)} available charged moves: {[m['name'] for m in available_moves]}")
        print(f"[DEBUG] {attacker.data['speciesId']} available moves details: {[(m['name'], m.get('power', 'N/A'), m.get('energy', 'N/A')) for m in available_moves]}")
        
        # Get ALL charged moves (not just available ones) to compare DPE
        all_charged_moves = attacker.charged_moves
        print(f"[DEBUG] {attacker.data['speciesId']} all charged moves: {[(m['name'], m.get('power', 'N/A'), m.get('energy', 'N/A')) for m in all_charged_moves]}")
        
        # Calculate DPE for all moves (using effective power after type effectiveness)
        move_dpe = {}
        for move in all_charged_moves:
            # Calculate effective power considering type effectiveness and STAB
            move_type = move["type"]
            defender_types = defender.data.get("types", [])
            effectiveness = TypeChart.get_effectiveness(move_type, defender_types)
            stab = DamageMultiplier.STAB if move_type in attacker.data.get("types", []) else 1.0
            
            effective_power = move["power"] * effectiveness * stab
            effective_dpe = effective_power / move["energy"] if move["energy"] > 0 else 0
            move_dpe[move["name"]] = effective_dpe
            print(f"[DEBUG] {attacker.data['speciesId']} move {move['name']}: power={move['power']}, energy={move['energy']}, effectiveness={effectiveness}, stab={stab}, effective_power={effective_power:.1f}, dpe={effective_dpe:.2f}")
        
        # Find the move with the highest DPE
        best_move_name = max(move_dpe.keys(), key=lambda k: move_dpe[k])
        best_dpe = move_dpe[best_move_name]
        best_move = next(m for m in all_charged_moves if m["name"] == best_move_name)
        current_energy = attacker.energy

        # Print DPE for all available charged moves at this moment
        print(f"[DEBUG] {attacker.data['speciesId']} available charged moves and DPE:")
        for move in available_moves:
            print(f"    {move['name']}: DPE={move_dpe[move['name']]:.2f} (energy: {move['energy']}, effective power: {move['power']})")
        print(f"[DEBUG] {attacker.data['speciesId']} best move by DPE: {best_move_name} (dpe: {best_dpe:.2f}, energy: {best_move['energy']})")
        print(f"[DEBUG] {attacker.data['speciesId']} current energy: {current_energy}")

        # If the best move is available, use it
        if current_energy >= best_move["energy"]:
            move = best_move
            print(f"[DEBUG] {attacker.data['speciesId']} using best move: {move['name']} (energy: {move['energy']}, dpe: {move_dpe[move['name']]:.2f})")
        else:
            # Check if we should wait for the best move
            should_wait = True
            # Don't wait if we're in danger (low HP)
            if defender.hp < defender.max_hp * 0.3:
                should_wait = False
                print(f"[DEBUG] {attacker.data['speciesId']} not waiting - opponent is low HP")
            if attacker.hp < attacker.max_hp * 0.3:
                should_wait = False
                print(f"[DEBUG] {attacker.data['speciesId']} not waiting - we're low HP")
            if best_move["energy"] > current_energy * 1.5:
                should_wait = False
                print(f"[DEBUG] {attacker.data['speciesId']} not waiting - best move too expensive")
            if best_move["energy"] - current_energy <= 3:
                should_wait = False
                print(f"[DEBUG] {attacker.data['speciesId']} not waiting - close to best move")
            if should_wait:
                print(f"[DEBUG] {attacker.data['speciesId']} waiting for better move - skipping charged move")
                return None  # Skip this turn, wait for better move
            else:
                # Pick the available move with the highest DPE
                best_available = max(available_moves, key=lambda m: move_dpe[m["name"]])
                move = best_available
                print(f"[DEBUG] {attacker.data['speciesId']} using best available move: {move['name']} (energy: {move['energy']}, dpe: {move_dpe[move['name']]:.2f})")
        
        # Calculate damage
        damage = self._calculate_damage(attacker, defender, move)
        
        # Determine which shield AI to use based on which player is defending
        if defender is self.p1_pokemon:
            shield_ai = self.p1_shield_ai
        elif defender is self.p2_pokemon:
            shield_ai = self.p2_shield_ai
        else:
            # Fallback to p1 strategy if we can't determine
            shield_ai = self.p1_shield_ai
        
        # Check if defender uses shield using intelligent AI
        shield_used = False
        if defender.shields > 0 and damage > 0:
            should_shield = shield_ai.should_shield(
                damage=damage,
                current_hp=defender.hp,
                max_hp=defender.max_hp,
                move_type=move["type"],
                defender_types=defender.data.get("types", []),
                remaining_shields=defender.shields,
                is_charged_move=True
            )
            
            if should_shield:
                shield_used = defender.use_shield()
                damage = 0
                print(f"[DEBUG] {defender.data['speciesId']} used shield (strategy: {shield_ai.strategy})")
        
        # Apply damage
        if not shield_used:
            defender.take_damage(damage)
        
        # Use energy
        attacker.use_energy(move["energy"])
        print(f"[DEBUG] {attacker.data['speciesId']} current energy: {attacker.energy}")
        
        # Apply buffs if any
        buff_applied = False
        if move.get("buffs"):
            chance = float(move.get("buffApplyChance", "0"))
            if random.random() < chance:
                if move.get("buffTarget") == "self":
                    attacker.apply_buff(move["buffs"][0], move["buffs"][1])
                else:  # opponent
                    defender.apply_buff(move["buffs"][0], move["buffs"][1])
                buff_applied = True
        
        return {
            "turn": turn,
            "type": "charged",
            "attacker": attacker.data["speciesId"],
            "defender": defender.data["speciesId"],
            "move": move["name"],
            "damage": damage,
            "shield_used": shield_used,
            "energy_used": move["energy"],
            "defender_hp_remaining": defender.hp,
            "attacker_energy": attacker.energy,
            "buff_applied": buff_applied,
            "shield_strategy": shield_ai.strategy if shield_used else None
        }
    
    def _calculate_damage(self, attacker: BattlePokemon, defender: BattlePokemon, move: Dict[str, Any]) -> int:
        """Calculate damage using PvPoke's formula"""
        # Get move type effectiveness
        move_type = move["type"]
        defender_types = defender.data.get("types", [])
        effectiveness = TypeChart.get_effectiveness(move_type, defender_types)
        
        # Check for STAB
        stab = DamageMultiplier.STAB if move_type in attacker.data.get("types", []) else 1.0
        
        # Calculate damage using PvPoke formula
        raw_damage = (
            move["power"] * 
            stab * 
            (attacker.get_effective_atk() / defender.get_effective_def()) * 
            effectiveness * 
            0.5 * 
            DamageMultiplier.BONUS
        )
        damage = math.floor(raw_damage) + 1
        
        # Debug logging
        print(f"[DEBUG] Damage calc for {move['name']}: power={move['power']}, stab={stab}, atk={attacker.get_effective_atk():.1f}, def={defender.get_effective_def():.1f}, effectiveness={effectiveness}, raw_damage={raw_damage:.3f}, final_damage={damage}")
        
        return max(1, damage)  # Minimum 1 damage
    
    def _determine_winner(self, p1: BattlePokemon, p2: BattlePokemon) -> Tuple[str, float]:
        """Determine winner and calculate battle rating"""
        if p1.is_fainted() and p2.is_fainted():
            return "tie", 0.5
        elif p1.is_fainted():
            # P2 wins
            battle_rating = min(1.0, p2.hp / p2.max_hp)  # Cap at 100%
            return p2.data["speciesId"], battle_rating
        else:
            # P1 wins
            battle_rating = min(1.0, p1.hp / p1.max_hp)  # Cap at 100%
            return p1.data["speciesId"], battle_rating 
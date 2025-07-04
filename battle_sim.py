import math
import random
from typing import Dict, Any, List, Optional, Tuple
from poke_data import PokeData

class DamageMultiplier:
    """PvPoke damage multipliers"""
    BONUS = 1.2999999523162841796875
    SUPER_EFFECTIVE = 1.60000002384185791015625
    RESISTED = 0.625
    DOUBLE_RESISTED = 0.390625
    STAB = 1.2000000476837158203125
    SHADOW_ATK = 1.2
    SHADOW_DEF = 0.83333331

class TypeChart:
    """PvPoke type effectiveness chart"""
    TYPE_TRAITS = {
        "normal": {"weaknesses": ["fighting"], "resistances": [], "immunities": ["ghost"]},
        "fighting": {"weaknesses": ["flying", "psychic", "fairy"], "resistances": ["rock", "bug", "dark"], "immunities": []},
        "flying": {"weaknesses": ["rock", "electric", "ice"], "resistances": ["fighting", "bug", "grass"], "immunities": ["ground"]},
        "poison": {"weaknesses": ["ground", "psychic"], "resistances": ["fighting", "poison", "bug", "fairy", "grass"], "immunities": []},
        "ground": {"weaknesses": ["water", "grass", "ice"], "resistances": ["poison", "rock"], "immunities": ["electric"]},
        "rock": {"weaknesses": ["fighting", "ground", "steel", "water", "grass"], "resistances": ["normal", "flying", "poison", "fire"], "immunities": []},
        "bug": {"weaknesses": ["flying", "rock", "fire"], "resistances": ["fighting", "ground", "grass"], "immunities": []},
        "ghost": {"weaknesses": ["ghost", "dark"], "resistances": ["poison", "bug"], "immunities": ["normal", "fighting"]},
        "steel": {"weaknesses": ["fighting", "ground", "fire"], "resistances": ["normal", "flying", "rock", "bug", "steel", "grass", "psychic", "ice", "dragon", "fairy"], "immunities": ["poison"]},
        "fire": {"weaknesses": ["ground", "rock", "water"], "resistances": ["bug", "steel", "fire", "grass", "ice", "fairy"], "immunities": []},
        "water": {"weaknesses": ["grass", "electric"], "resistances": ["steel", "fire", "water", "ice"], "immunities": []},
        "grass": {"weaknesses": ["flying", "poison", "bug", "fire", "ice"], "resistances": ["ground", "water", "grass", "electric"], "immunities": []},
        "electric": {"weaknesses": ["ground"], "resistances": ["flying", "steel", "electric"], "immunities": []},
        "psychic": {"weaknesses": ["bug", "ghost", "dark"], "resistances": ["fighting", "psychic"], "immunities": []},
        "ice": {"weaknesses": ["fighting", "fire", "steel", "rock"], "resistances": ["ice"], "immunities": []},
        "dragon": {"weaknesses": ["dragon", "ice", "fairy"], "resistances": ["fire", "water", "grass", "electric"], "immunities": []},
        "dark": {"weaknesses": ["fighting", "fairy", "bug"], "resistances": ["ghost", "dark"], "immunities": ["psychic"]},
        "fairy": {"weaknesses": ["poison", "steel"], "resistances": ["fighting", "bug", "dark"], "immunities": ["dragon"]}
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
            elif move_type in traits["immunities"]:
                effectiveness *= DamageMultiplier.DOUBLE_RESISTED
                
        return effectiveness

class BattlePokemon:
    """Represents a Pokémon in battle with current state"""
    def __init__(self, pokemon_data: Dict[str, Any], moves: Dict[str, str], shields: int = 2):
        self.data = pokemon_data
        self.moves = moves
        self.shields = shields
        
        # Battle state
        self.hp = self._calculate_hp()
        self.max_hp = self.hp
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
    
    def _calculate_hp(self) -> int:
        """Calculate HP from base stats and IVs"""
        base_stats = self.data.get("baseStats", {})
        hp_base = base_stats.get("hp", 100)
        # For now, use default IVs (15/15/15)
        hp_iv = 15
        level = 40  # Default level
        return int((hp_base + hp_iv) * (0.5 + level * 0.01))
    
    def _initialize_moves(self):
        """Initialize move objects from move IDs"""
        from poke_data import PokeData
        poke_data = PokeData()
        
        if "fast" in self.moves:
            self.fast_move = poke_data.get_move_details(self.moves["fast"])
        
        for i in range(1, 3):
            key = f"charged{i}"
            if key in self.moves:
                move_data = poke_data.get_move_details(self.moves[key])
                if move_data:
                    self.charged_moves.append(move_data)
    
    def get_effective_atk(self) -> float:
        """Get effective attack stat with buffs and shadow multiplier"""
        base_stats = self.data.get("baseStats", {})
        atk_base = base_stats.get("atk", 100)
        atk_iv = 15  # Default IV
        level = 40  # Default level
        base_atk = (atk_base + atk_iv) * (0.5 + level * 0.01)
        
        # Apply buff multiplier
        buff_mult = self._get_buff_multiplier(self.atk_buffs)
        
        return base_atk * self.shadow_atk_mult * buff_mult
    
    def get_effective_def(self) -> float:
        """Get effective defense stat with buffs and shadow multiplier"""
        base_stats = self.data.get("baseStats", {})
        def_base = base_stats.get("def", 100)
        def_iv = 15  # Default IV
        level = 40  # Default level
        base_def = (def_base + def_iv) * (0.5 + level * 0.01)
        
        # Apply buff multiplier
        buff_mult = self._get_buff_multiplier(self.def_buffs)
        
        return base_def * self.shadow_def_mult * buff_mult
    
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
        self.hp = max(0, self.hp - damage)
    
    def gain_energy(self, energy: int):
        """Gain energy"""
        self.energy = min(self.max_energy, self.energy + energy)
    
    def use_energy(self, energy: int):
        """Use energy for charged move"""
        self.energy = max(0, self.energy - energy)
    
    def use_shield(self):
        """Use a shield"""
        if self.shields > 0:
            self.shields -= 1
            return True
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
        # Initialize battle Pokémon
        p1 = BattlePokemon(p1_data, p1_moves, p1_shields)
        p2 = BattlePokemon(p2_data, p2_moves, p2_shields)
        
        # Battle state
        turn = 0
        timeline = []
        
        # Main battle loop
        while not p1.is_fainted() and not p2.is_fainted():
            turn += 1
            
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
            if p2_charged_result:
                timeline.append(p2_charged_result)
            
            # Check for fainting after charged moves
            if p1.is_fainted() or p2.is_fainted():
                break
        
        # Determine winner and calculate battle rating
        winner, battle_rating = self._determine_winner(p1, p2)
        
        return {
            "winner": winner,
            "p1_final_hp": p1.hp,
            "p2_final_hp": p2.hp,
            "p1_final_energy": p1.energy,
            "p2_final_energy": p2.energy,
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
        
        # Simple AI: use the most expensive move available
        move = max(available_moves, key=lambda m: m["energy"])
        
        # Calculate damage
        damage = self._calculate_damage(attacker, defender, move)
        
        # Check if defender uses shield
        shield_used = False
        if defender.shields > 0 and damage > 0:
            # Simple AI: shield if damage is high
            if damage > defender.hp * 0.3:  # Shield if damage > 30% of current HP
                shield_used = defender.use_shield()
                damage = 0
        
        # Apply damage
        if not shield_used:
            defender.take_damage(damage)
        
        # Use energy
        attacker.use_energy(move["energy"])
        
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
            "buff_applied": buff_applied
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
        damage = math.floor(
            move["power"] * 
            stab * 
            (attacker.get_effective_atk() / defender.get_effective_def()) * 
            effectiveness * 
            0.5 * 
            DamageMultiplier.BONUS
        ) + 1
        
        return max(1, damage)  # Minimum 1 damage
    
    def _determine_winner(self, p1: BattlePokemon, p2: BattlePokemon) -> Tuple[str, float]:
        """Determine winner and calculate battle rating"""
        if p1.is_fainted() and p2.is_fainted():
            return "tie", 0.5
        elif p1.is_fainted():
            # P2 wins
            battle_rating = p2.hp / p2.max_hp
            return p2.data["speciesId"], battle_rating
        else:
            # P1 wins
            battle_rating = p1.hp / p1.max_hp
            return p1.data["speciesId"], battle_rating 
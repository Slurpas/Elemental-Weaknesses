#!/usr/bin/env python3

def get_type_effectiveness(attacking_type, defending_types):
    """Calculate type effectiveness multiplier"""
    
    # Type effectiveness chart
    effectiveness = {
        'normal': {'rock': 0.5, 'ghost': 0, 'steel': 0.5},
        'fire': {'fire': 0.5, 'water': 0.5, 'grass': 2, 'ice': 2, 'bug': 2, 'rock': 0.5, 'dragon': 0.5, 'steel': 2},
        'water': {'fire': 2, 'water': 0.5, 'grass': 0.5, 'ground': 2, 'rock': 2, 'dragon': 0.5},
        'electric': {'water': 2, 'electric': 0.5, 'grass': 0.5, 'ground': 0, 'flying': 2, 'dragon': 0.5},
        'grass': {'fire': 0.5, 'water': 2, 'grass': 0.5, 'poison': 0.5, 'ground': 2, 'flying': 0.5, 'bug': 0.5, 'rock': 2, 'dragon': 0.5, 'steel': 0.5},
        'ice': {'fire': 0.5, 'water': 0.5, 'grass': 2, 'ice': 0.5, 'ground': 2, 'flying': 2, 'dragon': 2, 'steel': 0.5},
        'fighting': {'normal': 2, 'ice': 2, 'poison': 0.5, 'flying': 0.5, 'psychic': 0.5, 'bug': 0.5, 'rock': 2, 'ghost': 0, 'steel': 2, 'grass': 0.5, 'fairy': 0.5},
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
    
    if attacking_type not in effectiveness:
        return 1.0
    
    multiplier = 1.0
    for defending_type in defending_types:
        if defending_type in effectiveness[attacking_type]:
            multiplier *= effectiveness[attacking_type][defending_type]
    
    return multiplier

def test_dragon_pulse_vs_lanturn():
    """Test Dragon Pulse effectiveness against Lanturn"""
    
    # Dragon Pulse is Dragon type
    attacking_type = 'dragon'
    
    # Lanturn is Water/Electric type
    defending_types = ['water', 'electric']
    
    effectiveness = get_type_effectiveness(attacking_type, defending_types)
    
    print(f"Dragon Pulse (Dragon) vs Lanturn (Water/Electric)")
    print(f"Type effectiveness: {effectiveness}x")
    
    # Calculate DPE with type effectiveness
    base_dpe = 90 / 60  # 1.50
    effective_dpe = base_dpe * effectiveness
    
    print(f"Base DPE: {base_dpe:.2f}")
    print(f"Effective DPE: {effective_dpe:.2f}")
    
    # Compare with Sky Attack
    sky_attack_base_dpe = 85 / 55  # 1.55
    sky_attack_effectiveness = get_type_effectiveness('flying', defending_types)
    sky_attack_effective_dpe = sky_attack_base_dpe * sky_attack_effectiveness
    
    print(f"\nSky Attack (Flying) vs Lanturn (Water/Electric)")
    print(f"Type effectiveness: {sky_attack_effectiveness}x")
    print(f"Base DPE: {sky_attack_base_dpe:.2f}")
    print(f"Effective DPE: {sky_attack_effective_dpe:.2f}")
    
    print(f"\nComparison:")
    print(f"Dragon Pulse effective DPE: {effective_dpe:.2f}")
    print(f"Sky Attack effective DPE: {sky_attack_effective_dpe:.2f}")
    
    if effective_dpe > sky_attack_effective_dpe:
        print("✅ Dragon Pulse should be preferred")
    else:
        print("⚠️  Sky Attack should be preferred")

if __name__ == "__main__":
    test_dragon_pulse_vs_lanturn() 
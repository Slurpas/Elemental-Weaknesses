import requests
import json

def test_master_league():
    """Test Master League functionality"""
    base_url = "http://localhost:5000"
    
    print("🧪 Testing Master League Functionality")
    print("=" * 50)
    
    # Test 1: Check if server is running
    try:
        response = requests.get(f"{base_url}/")
        print("✅ Server is running")
    except Exception as e:
        print(f"❌ Server not running: {e}")
        return
    
    # Test 2: Get a Pokémon in Master League (0 CP cap)
    print("\n📊 Testing Pokémon stats in Master League...")
    
    # Test with Mewtwo (should have very high stats in Master League)
    try:
        response = requests.get(f"{base_url}/api/pokemon/mewtwo")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Mewtwo data retrieved")
            print(f"   Name: {data.get('name', 'N/A')}")
            print(f"   Types: {data.get('types', [])}")
            print(f"   Stats: {data.get('stats', {})}")
            
            # Check if stats are high (Master League should have high stats)
            stats = data.get('stats', {})
            if stats.get('hp', 0) > 200:  # Master League HP should be high
                print(f"   ✅ High HP ({stats.get('hp')}) - Master League stats detected")
            else:
                print(f"   ⚠️  Low HP ({stats.get('hp')}) - May not be Master League stats")
        else:
            print(f"❌ Failed to get Mewtwo data: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting Mewtwo data: {e}")
    
    # Test 3: Test battle simulation with Master League CP cap
    print("\n⚔️ Testing battle simulation with Master League...")
    
    battle_data = {
        "p1_id": "mewtwo",
        "p2_id": "dialga", 
        "p1_moves": {
            "fast": "PSYCHO_CUT",
            "charged1": "PSYSTRIKE",
            "charged2": "FOCUS_BLAST"
        },
        "p2_moves": {
            "fast": "DRAGON_BREATH",
            "charged1": "DRACO_METEOR",
            "charged2": "IRON_HEAD"
        },
        "p1_shields": 2,
        "p2_shields": 2,
        "p1_shield_ai": "smart_30",
        "p2_shield_ai": "smart_30",
        "cp_cap": 0  # Master League
    }
    
    try:
        response = requests.post(f"{base_url}/api/battle", json=battle_data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Battle simulation successful")
            print(f"   Winner: {result.get('winner', 'N/A')}")
            print(f"   Battle Rating: {result.get('battle_rating', 'N/A')}")
            print(f"   P1 Final HP: {result.get('p1_final_hp', 'N/A')}")
            print(f"   P2 Final HP: {result.get('p2_final_hp', 'N/A')}")
            print(f"   Turns: {result.get('turns', 'N/A')}")
            print(f"   CP Cap Used: {result.get('cp_cap', 'N/A')}")
            
            # Check if HP values are high (Master League should have high HP)
            p1_hp = result.get('p1_final_hp', 0)
            p2_hp = result.get('p2_final_hp', 0)
            if p1_hp > 200 or p2_hp > 200:
                print(f"   ✅ High HP values - Master League battle confirmed")
            else:
                print(f"   ⚠️  Low HP values - May not be Master League battle")
                
        else:
            print(f"❌ Battle simulation failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error in battle simulation: {e}")
    
    # Test 4: Test matchup API with Master League
    print("\n🎯 Testing matchup API with Master League...")
    
    matchup_data = {
        "opponent": "mewtwo",
        "team": ["dialga", "rayquaza", "giratina_origin"]
    }
    
    try:
        response = requests.post(f"{base_url}/api/matchup", json=matchup_data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Matchup analysis successful")
            print(f"   Opponent moves vs team: {len(result.get('opponent_moves_vs_team', []))}")
            print(f"   Team moves vs opponent: {len(result.get('team_moves_vs_opponent', []))}")
            
            # Check if moves are found
            if len(result.get('opponent_moves_vs_team', [])) > 0:
                print(f"   ✅ Moves found - Master League matchup working")
            else:
                print(f"   ⚠️  No moves found - May be an issue")
        else:
            print(f"❌ Matchup analysis failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error in matchup analysis: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Master League testing complete!")

if __name__ == "__main__":
    test_master_league() 
#!/usr/bin/env python3
"""
Test script to verify matchup API functionality
"""

import requests
import json

def test_matchup_api():
    """Test the matchup API with species IDs"""
    
    # Test data - using species IDs
    test_data = {
        "opponent": "azumarill",  # species ID
        "team": ["altaria", "stunfisk_galarian"]  # species IDs
    }
    
    print("🧪 Testing Matchup API")
    print("=" * 50)
    print(f"Opponent: {test_data['opponent']}")
    print(f"Team: {test_data['team']}")
    print()
    
    try:
        # Make API request
        response = requests.post(
            "http://localhost:5000/api/matchup",
            headers={"Content-Type": "application/json"},
            json=test_data
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API request successful!")
            print()
            
            # Check opponent moves vs team
            opponent_moves = data.get('opponent_moves_vs_team', [])
            print(f"📊 Opponent moves vs team: {len(opponent_moves)} moves")
            
            if opponent_moves:
                print("   Opponent moves:")
                for move_data in opponent_moves:
                    move = move_data['move']
                    print(f"   - {move['name']} ({move['type']} {move['move_class']})")
                    for i, vs_team in enumerate(move_data['vs_team']):
                        effectiveness = vs_team['effectiveness']
                        print(f"     vs {data['team'][i]}: {effectiveness['label']} ({effectiveness['multiplier']}x)")
                print()
            else:
                print("   ❌ No opponent moves data")
            
            # Check team moves vs opponent
            team_moves = data.get('team_moves_vs_opponent', [])
            print(f"📊 Team moves vs opponent: {len(team_moves)} team members")
            
            if team_moves:
                for team_member in team_moves:
                    pokemon = team_member['pokemon']
                    moves = team_member['moves']
                    print(f"   {pokemon}: {len(moves)} moves")
                    for move_data in moves:
                        move = move_data['move']
                        effectiveness = move_data['effectiveness']
                        print(f"     - {move['name']} ({move['type']} {move['move_class']}): {effectiveness['label']} ({effectiveness['multiplier']}x)")
                print()
            else:
                print("   ❌ No team moves data")
                
        else:
            print(f"❌ API request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure app.py is running.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_matchup_api() 
import requests
import json

# Test the matchup API with some sample data
def test_matchup_api():
    url = "http://localhost:5000/api/matchup"
    
    # Sample data - using species IDs
    data = {
        "opponent": "bulbasaur",  # species ID
        "team": ["charmander", "squirtle", "pikachu"]  # species IDs
    }
    
    print("Testing matchup API...")
    print(f"URL: {url}")
    print(f"Data: {json.dumps(data, indent=2)}")
    print("-" * 50)
    
    try:
        response = requests.post(url, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_matchup_api() 
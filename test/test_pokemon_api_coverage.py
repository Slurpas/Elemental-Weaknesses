import json
import requests

POKEMON_JSON = 'pvpoke/src/data/gamemaster/pokemon.json'
API_URL = 'http://localhost:5000/api/pokemon/'


def main():
    with open(POKEMON_JSON, encoding='utf-8') as f:
        data = json.load(f)
    
    failed = []
    total = 0
    for entry in data:
        species_id = entry.get('speciesId')
        if not species_id:
            continue
        total += 1
        url = API_URL + species_id
        try:
            resp = requests.get(url)
            if resp.status_code != 200:
                print(f"FAIL: {species_id} - HTTP {resp.status_code} - {resp.text}")
                failed.append((species_id, resp.status_code, resp.text))
        except Exception as e:
            print(f"ERROR: {species_id} - {e}")
            failed.append((species_id, 'EXCEPTION', str(e)))
    print(f"\nChecked {total} Pokémon. Failures: {len(failed)}")
    if failed:
        print("Failed speciesIds:")
        for sid, code, msg in failed:
            print(f"  {sid}: {code} - {msg[:100]}")

if __name__ == '__main__':
    main() 
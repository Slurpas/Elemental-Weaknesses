import os
import requests
from poke_data import PokeData

SPRITE_DIR = os.path.join('static', 'sprites')
BASE_URL = 'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/'
FORM_URL = 'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/'

os.makedirs(SPRITE_DIR, exist_ok=True)

poke_data = PokeData()

missing = []

def get_sprite_url(p):
    # Try to use the official artwork for all forms
    # For default forms, use dex number
    dex = p.get('dex')
    species_id = p.get('speciesId')
    # Try to get form number if available (PokéAPI uses - for forms, e.g., 25 for Pikachu, 25-ash for Ash Hat Pikachu)
    # But most forms are not in the main set, so fallback to official artwork or default
    # We'll use official artwork for all forms if possible
    # Compose filename: {dex}.png or {dex}-{form}.png
    # For PvPoke, speciesId is usually the best unique key
    # Try to use the official artwork for all forms
    # If not found, fallback to default
    if '-' in species_id:
        # Try to use the form artwork (not all forms exist)
        url = f'{FORM_URL}{species_id}.png'
    else:
        url = f'{FORM_URL}{dex}.png'
    return url

def download_sprite(p):
    species_id = p.get('speciesId')
    sprite_path = os.path.join(SPRITE_DIR, f'{species_id}.png')
    if os.path.exists(sprite_path):
        return True
    url = get_sprite_url(p)
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200 and r.content:
            with open(sprite_path, 'wb') as f:
                f.write(r.content)
            print(f'Downloaded {species_id} from {url}')
            return True
        else:
            # Try fallback to default sprite
            fallback_url = f'{BASE_URL}{p.get("dex")}.png'
            r2 = requests.get(fallback_url, timeout=10)
            if r2.status_code == 200 and r2.content:
                with open(sprite_path, 'wb') as f:
                    f.write(r2.content)
                print(f'Downloaded {species_id} (fallback) from {fallback_url}')
                return True
            else:
                print(f'No sprite found for {species_id} (tried {url} and {fallback_url})')
                missing.append(species_id)
                return False
    except Exception as e:
        print(f'Error downloading {species_id}: {e}')
        missing.append(species_id)
        return False

if __name__ == '__main__':
    for p in poke_data.pokemon:
        download_sprite(p)
    if missing:
        print(f'Could not find sprites for {len(missing)} Pokémon:')
        for m in missing:
            print(m)
    else:
        print('All sprites downloaded successfully!') 
import json

def matches_location(locations):
    for loc in locations:
        l = loc.lower()
        if any(kw in l for kw in ('new york', 'nyc', 'manhattan', 'brooklyn')):
            return True
        if 'remote' in l:
            return True
    return False

with open('.github/scripts/listings.json') as f:
    listings = json.load(f)

filtered = [
    entry for entry in listings
    if entry.get('season') in ('Fall', 'Winter')
    and matches_location(entry.get('locations', []))
]

with open('.github/scripts/listings.json', 'w') as f:
    json.dump(filtered, f, indent=2)

print(f"Filtered: {len(listings)} -> {len(filtered)} listings")

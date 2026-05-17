import json

def is_phd(entry):
    title = (entry.get('title') or '').lower()
    return 'phd' in title or 'ph.d' in title

def matches_location(locations):
    has_nyc = False
    has_remote_usa = False
    for loc in locations:
        l = loc.lower()
        if any(kw in l for kw in ('uk', 'united kingdom', 'london', 'england', 'scotland')):
            continue
        if any(kw in l for kw in ('new york', 'nyc', 'manhattan', 'brooklyn')):
            has_nyc = True
        if 'remote' in l:
            if any(kw in l for kw in ('uk', 'canada', 'united kingdom', 'london', 'india', 'europe')):
                continue
            has_remote_usa = True
    return has_nyc or has_remote_usa

with open('.github/scripts/listings.json') as f:
    listings = json.load(f)

filtered = [
    entry for entry in listings
    if entry.get('season') in ('Fall', 'Winter')
    and not is_phd(entry)
    and matches_location(entry.get('locations', []))
]

with open('.github/scripts/listings.json', 'w') as f:
    json.dump(filtered, f, indent=2)

print(f"Filtered: {len(listings)} -> {len(filtered)} listings")

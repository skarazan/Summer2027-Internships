import json
import os
import urllib.request

UPSTREAM_URL = "https://raw.githubusercontent.com/vanshb03/Summer2027-Internships/dev/.github/scripts/listings.json"
LISTINGS_PATH = ".github/scripts/listings.json"

def matches_location(locations):
    for loc in locations:
        l = loc.lower()
        if any(kw in l for kw in ('new york', 'nyc', 'manhattan', 'brooklyn')):
            return True
        if 'remote' in l:
            return True
    return False

def filter_listings(listings):
    return [
        e for e in listings
        if e.get('season') in ('Fall', 'Winter')
        and matches_location(e.get('locations', []))
    ]

with open(LISTINGS_PATH) as f:
    old_filtered = json.load(f)
old_ids = {e['id'] for e in old_filtered}

print("Fetching upstream listings...")
with urllib.request.urlopen(UPSTREAM_URL) as resp:
    upstream = json.loads(resp.read())

new_filtered = filter_listings(upstream)
new_ids = {e['id'] for e in new_filtered}

added_ids = new_ids - old_ids
added = [e for e in new_filtered if e['id'] in added_ids]

old_by_id = {e['id']: e for e in old_filtered}
updated = []
for e in new_filtered:
    if e['id'] in old_ids and e.get('date_updated') != old_by_id[e['id']].get('date_updated'):
        updated.append(e)

reactivated = []
for e in new_filtered:
    old = old_by_id.get(e['id'])
    if old and not old.get('active') and e.get('active'):
        reactivated.append(e)

with open(LISTINGS_PATH, 'w') as f:
    json.dump(new_filtered, f, indent=2)

print(f"Upstream: {len(upstream)} -> Filtered: {len(new_filtered)} (was {len(old_filtered)})")
print(f"New: {len(added)}, Updated: {len(updated)}, Reactivated: {len(reactivated)}")

changes = added + updated + reactivated
if changes:
    lines = []
    for e in added:
        locs = ", ".join(e.get("locations", []))
        url = e.get("url", "")
        lines.append(f"🆕 **{e['company_name']}** — {e['title']}\n📍 {locs}\n🔗 {url}")
    for e in updated:
        locs = ", ".join(e.get("locations", []))
        url = e.get("url", "")
        lines.append(f"✏️ **{e['company_name']}** — {e['title']}\n📍 {locs}\n🔗 {url}")
    for e in reactivated:
        locs = ", ".join(e.get("locations", []))
        url = e.get("url", "")
        lines.append(f"🔓 **{e['company_name']}** — {e['title']} (reopened)\n📍 {locs}\n🔗 {url}")
    message = "\n\n".join(lines)
    with open(os.environ.get("GITHUB_OUTPUT", "/dev/null"), "a") as f:
        f.write("has_changes=true\n")
    with open(".github/scripts/discord_message.txt", "w") as f:
        f.write(message)
else:
    with open(os.environ.get("GITHUB_OUTPUT", "/dev/null"), "a") as f:
        f.write("has_changes=false\n")
    print("No changes detected.")

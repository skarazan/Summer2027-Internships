import json
import os
import hashlib
import urllib.request

UPSTREAM_URL = "https://raw.githubusercontent.com/vanshb03/Summer2027-Internships/dev/.github/scripts/listings.json"
LISTINGS_PATH = ".github/scripts/listings.json"
NOTIFIED_PATH = ".github/scripts/notified_hashes.json"

SIBLING_HASH_URLS = [
    "https://raw.githubusercontent.com/skarazan/Summer2026-Internships-NYC/dev/.github/scripts/notified_hashes.json",
    "https://raw.githubusercontent.com/skarazan/Internships-2026/main/.github/data/notified_hashes.json",
    "https://raw.githubusercontent.com/skarazan/southeast-tech-internships-2026-2027/main/.github/data/notified_hashes.json",
    "https://raw.githubusercontent.com/skarazan/jsearch-internship-scanner/main/.github/data/notified_hashes.json",
]

def job_hash(entry):
    key = f"{entry.get('company_name','').lower().strip()}|{entry.get('title','').lower().strip()}"
    return hashlib.md5(key.encode()).hexdigest()[:12]

def fetch_sibling_hashes():
    hashes = set()
    for url in SIBLING_HASH_URLS:
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                hashes.update(json.loads(resp.read()))
        except Exception:
            pass
    return hashes

def is_phd(entry):
    title = (entry.get('title') or '').lower()
    return 'phd' in title or 'ph.d' in title

def matches_location(locations):
    has_nyc = False
    has_remote_usa = False
    for loc in locations:
        l = loc.lower()
        # Skip UK locations
        if any(kw in l for kw in ('uk', 'united kingdom', 'london', 'england', 'scotland')):
            continue
        # NYC in-person/hybrid
        if any(kw in l for kw in ('new york', 'nyc', 'brooklyn')):
            has_nyc = True
        if 'manhattan' in l and 'beach' not in l:
            has_nyc = True
        # Remote USA only (not "Remote in UK", "Remote, Canada", etc.)
        if 'remote' in l:
            # reject if location explicitly mentions non-US
            if any(kw in l for kw in ('uk', 'canada', 'united kingdom', 'london', 'india', 'europe')):
                continue
            # accept "Remote", "Remote US", "Remote USA", "Remote in USA", or bare remote
            has_remote_usa = True
    return has_nyc or has_remote_usa

def filter_listings(listings):
    return [
        e for e in listings
        if e.get('season') in ('Fall', 'Winter')
        and not is_phd(e)
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

notified = set()
if os.path.exists(NOTIFIED_PATH):
    with open(NOTIFIED_PATH) as f:
        notified = set(json.load(f))
sibling_hashes = fetch_sibling_hashes()
all_known = notified | sibling_hashes

added = [e for e in added if job_hash(e) not in all_known]
updated = [e for e in updated if job_hash(e) not in all_known]
reactivated = [e for e in reactivated if job_hash(e) not in all_known]

changes = added + updated + reactivated
if changes:
    for e in changes:
        notified.add(job_hash(e))
    with open(NOTIFIED_PATH, "w") as f:
        json.dump(sorted(notified), f)
    MAX_SHOW = 5
    lines = []
    all_changes = added[:MAX_SHOW]
    for e in all_changes:
        locs = ", ".join(e.get("locations", []))
        url = e.get("url", "")
        lines.append(f"🆕 **{e['company_name']}** — {e['title']}\n📍 {locs}\n🔗 <{url}>")
    for e in reactivated[:max(0, MAX_SHOW - len(all_changes))]:
        locs = ", ".join(e.get("locations", []))
        url = e.get("url", "")
        lines.append(f"🔓 **{e['company_name']}** — {e['title']} (reopened)\n📍 {locs}\n🔗 <{url}>")
    extra = len(added) + len(updated) + len(reactivated) - len(lines)
    if extra > 0:
        lines.append(f"...and **{extra} more** — check the README")
    message = "@everyone\n\n" + "\n\n".join(lines)
    with open(os.environ.get("GITHUB_OUTPUT", "/dev/null"), "a") as f:
        f.write("has_changes=true\n")
    with open(".github/scripts/discord_message.txt", "w") as f:
        f.write(message)
else:
    with open(os.environ.get("GITHUB_OUTPUT", "/dev/null"), "a") as f:
        f.write("has_changes=false\n")
    print("No changes detected.")

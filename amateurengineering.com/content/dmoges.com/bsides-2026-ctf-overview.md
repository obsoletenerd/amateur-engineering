---
Title: BSides Ballarat 2026 CTF: The Ballarat Bitcoin Mining Underground
Date: 2026-03-12T10:00:00+10:00
Tags: ctf, cybersecurity, bsides2026, bsides
Author: dmoges
AuthorURL: https://dmoges.com
Category: dmoges
Status: published
Cover: /images/placeholder.jpg
---

This year's BSides Ballarat CTF was my most ambitious yet - a five-challenge story that took teams from analysing smart meter traffic all the way to physically cutting wires under a countdown timer. The whole thing is built around an underground bitcoin mining operation leeching power from Ballarat's electricity grid, and teams had to track it down, find the insider, break into their communications, and ultimately stop a self-destruct mechanism before it destroyed all the evidence.

## The Story

Someone is stealing power from Ballarat's grid to run an illegal bitcoin mining operation. You start by analysing smart meter traffic to figure out which building is being used, then progressively break into the company website, the insider's webmail, and the mining group's IRC server. Each challenge reveals new pieces of the puzzle - including fragments of a self-destruct override code scattered across all four digital challenges. The finale brings everything together in a physical hardware challenge where you're racing a 10-minute countdown to disarm the system.

I wanted this year's CTF to feel like a real investigation, where each discovery naturally leads to the next. Intel you gather early on (credentials, server addresses, code fragments) is needed in later challenges.

**The individual writeups below contain full spoilers.** If you want to try the challenges yourself first, the challenge environments are available in the [BSides Ballarat CTF git repo](https://github.com/bsides-ballarat/CTF2026-overview).

## The Challenges

### Challenge 1: Find the Company (175 points, 3 flags)

**Category**: Forensics / Network Analysis

You get a PCAP file full of smart meter traffic and need to spot the suspicious power consumption. A constant 42+ kW draw is a dead giveaway for mining hardware. The target turns out to be Ballarat Engineering Supplies at 315 Sturt Street, and bonus flags reward digging into the meter ID and finding hidden metadata.

[Read the full Challenge 1 writeup](/posts/bsides-2026-ctf-01-find-the-company/)

### Challenge 2: Website Access (700 points, 8 flags)

**Category**: Web Application Security

With the company identified from Challenge 1, you're now attacking the Ballarat Engineering Supplies website. Vulnerabilities progress from easy information disclosure (exposed staff API, robots.txt, source maps) through CSRF and path traversal, up to SQL injection and chained CSRF attacks. The big discovery here is Trevor Blackwood - the warehouse coordinator who's been helping the mining operation from the inside.

[Read the full Challenge 2 writeup](/posts/bsides-2026-ctf-02-website-access/)

### Challenge 3: Webmail Access (650 points, 8 flags)

**Category**: Email Security / Cryptography

Trevor's corporate webmail is protected by 2FA, but the implementation has some serious flaws. You can download the SQLite database via path traversal, extract TOTP secrets, or just brute-force the predictable backup codes. Inside Trevor's inbox you'll find IRC server credentials and another piece of the self-destruct override code.

[Read the full Challenge 3 writeup](/posts/bsides-2026-ctf-03-webmail-access/)

### Challenge 4: IRC Access (700 points, 5 flags)

**Category**: AI Security / Prompt Injection

The mining group runs an IRC server with an AI helper bot called BitHelper. You need to use prompt injection to trick the bot into giving up operational secrets - the mining rig password (a nod to Ballarat's Eureka Stockade history) and the final piece of the self-destruct override code.

[Read the full Challenge 4 writeup](/posts/bsides-2026-ctf-04-irc-access/)

### Challenge 5: Stop the Self-Destruct (1000 points)

**Category**: Hardware / Physical

The grand finale. The mining facility is rigged with explosives, and you need to assemble the override code from fragments found across all previous challenges, then physically cut the right wires on a Raspberry Pi Pico 2 rig before a 10-minute countdown runs out. Cut the wrong wire and the timer speeds up.

[Read the full Challenge 5 writeup](/posts/bsides-2026-ctf-05-self-destruct/)

## The Meta-Puzzle

One of the design elements I'm most proud of is the self-destruct override code that threads through every challenge. The format (`SD_SEQUENCE_[COLOR]_[NUMBER]_[LETTER]`) is discovered in Challenge 2, the colour BLUE comes from Challenge 1's meter metadata, SEVEN from Challenge 3's webmail, and ALPHA from Challenge 4's IRC logs. The complete code `SD_SEQUENCE_BLUE_SEVEN_ALPHA` is actually hidden in Challenge 1's meter metadata from the very start - rewarding teams who are thorough in their initial analysis.

## Scoring and Hints

There were 29 flags across the first four challenges, worth a total of 3,225 points including the self-destruct finale. Each challenge had purchasable hints at varying point costs - gentle nudges for free or cheap, specific techniques for moderate cost, and near-complete bypasses if you were really stuck. No team ever hit a complete dead end, but teams who didn't need hints came out well ahead on points.

## My thoughts

Building a five-challenge narrative CTF was a massive undertaking compared to previous years. The hardest part was making sure the story held together and that each challenge flowed naturally into the next. I spent a lot of time on the physical self-destruct challenge - getting the Raspberry Pi Pico 2 to reliably detect wire cuts via GPIO while maintaining the countdown timer was trickier than I expected.

The prompt injection challenge was new territory for me, and I think AI security is going to become increasingly relevant in CTFs. Having teams try to social engineer an LLM felt very current.

For next year, I'm considering making the physical component even more involved. The wire-cutting finale got great reactions and I think there's room to expand on that idea.
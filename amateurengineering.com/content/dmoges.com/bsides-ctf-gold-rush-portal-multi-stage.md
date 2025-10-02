---
Title: BSides 2025 CTF: Gold Rush Portal - Multi-Stage Network Challenge
Date: 2025-07-24T12:30:00+10:00
Tags: ctf, cybersecurity, bsides2025
Author: dmoges
Author-URL: https://dmoges.com
Category: dmoges
Status: published
---

This was my most ambitious challenge for BSides CTF 2025 - a multi-stage network penetration scenario running on a Raspberry Pi. I wanted participants to experience a realistic attack chain, starting from WiFi access all the way to compromising internal services.

## Challenge Details

**Difficulty**: Progressive (Easy → Medium → Hard)

**Category**: Network Services & Web Exploitation  

## The Setup

I configured a Raspberry Pi 3B as a WiFi access point with three vulnerable services. When you connect to the "Gold Rush Mining Guest" network, you get redirected to a captive portal - just like at hotels or cafes. But this portal has a problem.

The flags tell the story:
- Stage 1: `FLAG{W1F1_CL13NT_S1D3_VULN_3XPL01T3D}`
- Stage 2: `FLAG{FTP_4N0NYM0US_4CC3SS_1S_UNSAF3}`
- Stage 3: `FLAG{3M41L_S3RV3R_C0MPR0M1S3D}`

## Stage 1: The Captive Portal

The portal asks for your personal information before granting access. Standard stuff. But if you open the browser's developer console (F12), you'll find something interesting in the JavaScript.

Stop reading here if you want to solve it yourself!

### The Vulnerability

The authentication is handled entirely client-side. There's a JavaScript object called `authState` with an `isAuthenticated` property. Just type `authState.isAuthenticated = true` in the console and boom - you're in.

I know, I know - who would actually do this in production?

## Stage 2: Anonymous FTP

Once you're past the portal, you can scan the network. Running `nmap 192.168.1.0/24` reveals an FTP server on port 21.

### Finding the Flag

Connect with:
```bash
ftp 192.168.1.X
Username: anonymous
Password: [just press Enter]
```

Most people forget to check for hidden files. Use `ls -la` and you'll spot `.hidden_flag.txt`. Inside, you'll find the second flag and some credentials:
- Username: `admin`
- Password: `password123`

Classic sysadmin move - leaving credentials in "hidden" files.

## Stage 3: Mail Server Compromise

The credentials from the FTP server work on the mail server (ports 110 and 143). This was intentional - password reuse is still incredibly common in corporate environments.

### Getting the Final Flag

You can use telnet for a quick and dirty connection:
```bash
telnet 192.168.1.X 110
USER admin
PASS password123
LIST
RETR 1
QUIT
```

The email contains the final flag. Mission complete.

## Real-World Relevance

Each vulnerability in this challenge represents something I've seen in actual penetration tests:

1. **Client-side authentication**: More common than you'd think, especially in IoT devices
2. **Anonymous FTP**: Still enabled by default on many devices
3. **Password reuse**: The number one way lateral movement happens in breaches

This entire attack chain requires zero exploits - just misconfigurations and bad practices.

## Technical Implementation

Running this on a Raspberry Pi presented some interesting challenges. Docker on ARM isn't as straightforward as x86, and getting the WiFi AP to play nicely with the captive portal redirect took some creative iptables rules.

The setup uses:
- hostapd for the WiFi access point
- dnsmasq for DHCP and DNS hijacking
- nginx for the captive portal
- vsftpd for the FTP server
- Custom Python script for the mail server (because why not?)

Also, the power of the wifi on the Pi 3B is pretty limited, so everyone had to be in one room to participate. 
This wasn't intended, and next year we'll ensure the infrastructure is more powerful.
---
Title: BSides 2025 CTF: Hidden Bio Picture - OSINT Challenge
Date: 2025-07-09T14:00:00+10:00
Tags: ctf, cybersecurity, bsides2025
Author: dmoges
Author-URL: https://dmoges.com
Category: dmoges
Status: published
Cover: https://dmoges.com/images/bsides-ctf-hidden-bio-osint/image.png
---

This was the most basic challenge for the BSides CTF 2025, designed to just get people started.
Anyone with some basic web experience or OSINT skills should be able to solve it quickly.

## Challenge Details

**Difficulty**: Beginner 

**Category**: OSINT / Web Reconnaissance  


## The Discovery

While exploring the [Gold Rush Security](https://goldrushsecurity.com/) website for general clues and exploits, observant participants might notice something interesting in the "About" page.
The website displays three employee profiles with their photos:
- `bio_1.png` - Chief Executive Officer
- `bio_2.png` - Chief Technology Officer
- `bio_3.png` - Chief Security Officer

But what about `bio_4.png`?

![A stressed CSO](https://dmoges.com/images/bsides-ctf-hidden-bio-osint/image-1.png)

## The Investigation Process

When you see a numbered sequence (bio1, bio2, bio3), always check if the pattern continues.
Web developers often prepare resources in advance or leave old files on the server.
In this case, if you try to access `/static/images/bio_4.png`, you'll see the following image:

![Party time, you found a flag](https://dmoges.com/images/bsides-ctf-hidden-bio-osint/image.png)


If you haven't done anything web-based before, you might not know that you can access files directly by their URL.
Most browsers allow you to right-click on an image and open the image in a new tab, which will show you the direct URL.
Inspect elements also works if you prefer that method.


## Real-World Relevance

This challenge simulates several common security issues:

1. **Improper Access Controls**: Files accessible via direct URL even when not linked
2. **Information Disclosure**: Sensitive information in seemingly innocuous files
3. **Poor Data Hygiene**: Old or unused files left on production servers
4. **Predictable Naming**: Sequential naming patterns enable enumeration

In short, trim unnecessary files and don't use sequential naming for sensitive resources. This is a common mistake in web development that can lead to information leaks.

## Conclusion

This was an easy challenge, but hidden enough that only a couple of people found it.
If you are reading this post for clues for 2026, there will be another challenge like this, so keep an eye out for it.
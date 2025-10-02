---
Title: BSides 2025 CTF: Barcode Basics - Code39 Challenge
Date: 2025-07-09T13:30:00+10:00
Tags: ctf, cybersecurity, bsides2025
Author: dmoges
Author-URL: https://dmoges.com
Category: dmoges
Status: published
---

The Barcode challen was one of the first challenges I thought of when I started planning the BSides CTF 2025. It is a simple challenge that introduces participants to barcode analysis and decoding, specifically focusing on Code39 barcodes.
However I threw some extra complexity in there to mess with people a bit.

## Challenge Details

**Difficulty**: Beginner/Intermediate, but with some gotchas

**Category**: Barcode Analysis / Encoding, a little OSINT  

## The Challenge

The barcode itself is right in the middle of the website, at https://goldrushsecurity.com/ and also even has the name of the user on the card, Marcus.
The image is below, don't scroll past it if you want to try and solve it yourself first!
Clues get progressively revealed as you scroll down the page, so stop at each section to avoid spoilers.

![BSides 2025 Barcode challenge original image](https://dmoges.com/images/bsides-ctf-barcode-basics/image.png)


## Background: Code39 Barcodes

Code39 (also known as Code 3 of 9) is one of the most widely used barcode symbologies. Key characteristics:

- **Alphanumeric**: Can encode uppercase letters (A-Z), numbers (0-9), and special characters (- . $ / + % SPACE)
- **Self-checking**: Each character has a specific pattern of bars and spaces
- **Variable length**: No fixed length requirement
- **Start/Stop characters**: Uses asterisk (*) as delimiter
- **Simple structure**: Easy to decode manually if needed

These are the reasons I chose this encoding, as there are other barcode encodings that are more complex, but Code39 is simple enough to decode by hand if you need to.

I won't explain further, as I'll just be rehashing the Wikipedia page, but if you want to read more about it, check out the [Wikipedia article on Code39](https://en.wikipedia.org/wiki/Code_39).

## Solution

Like I said, solutions below, so if you want to try and solve it yourself, stop reading now!

## A touch of OSINT

There is a bit of OSINT involved in this challenge. 
The barcode is on the Gold Rush Security website, which is a fictional company created for the CTF.

The barcode itself is a part of a user card for a fictional employee named Marcus.
It says so on the card.

If you poke around the site a little, you'll see his bio on the page, telling you he is the Chief Techncial Officer, and his full name is Dr Marcus Cipher.
The login to the Client Portal tells you that usernames are first initial and last name, so you can guess that his username is `mcipher`.
From here, we just need a password, which is what's encoded in the barcode.

## Barcode Analysis Approach

The image is rotated and partially obscured, but we can still decode what we can see.
If you rotate the image in an image editor, you can see the barcode more clearly.
From here, you can use an online barcode decoder or even manually decode it.

Using this method, you can read the start and end of the barcode.
We tested this (yes we tested some things) with a few barcode readers and they were able to read the partial barcode.

This should get you `S3CUR3D8YG` at the start, and `RU$HK` at the end.
The K is just to throw you.
The G in the start is too obscured to be read automatically, but nearly all bars are present, so it can be deduced.
In classic leetspeak, this reads as "Secured By G" and "Rush".
Based on the width of the obscured part, there 3 letters hidden.

To self-verify, the first few letters are under the barcode as well, so you can see the `S3CU` as means of self-checking your decoding.

## The last few letters

The last few letters are completely hidden (save for a few bars), so you have to guess them.
There are only 43 characters in Code39, so you can try a few combinations.
That gives $43^3 = 79,507$ combinations to try, which is a bit much.
If you've guessed the password, this drastically reduces the number of combinations you need to try.
You just try `O` vs `0`, `L` vs `1`, and `D` vs `8`, and you get `S3CUR3D8yG0LdRU$HK`.
That reduces down to just a handful of combinations, which you can try in the client portal.

The rules of the competition said brute-force was allowed within reason, and this is said application.
There is no DOS protection on the client portal, so you can try a few combinations without worrying about being blocked.

Here's the original barcode, before I printed it and set up the scene:

![Unobscured barcode](https://dmoges.com/images/bsides-ctf-barcode-basics/barcode.png)

## Security Implications

This challenge demonstrates important concepts:

### Information Leakage
- Barcodes are often overlooked as security risks
- May contain sensitive information (passwords, internal codes)
- Easily readable by anyone with a smartphone

Don't use passwords for anything that you wouldn't put in plain text.
In general, you don't "encode" secrets using any schema - you "encrypt" them.

## My final thoughts

This was a fun challenge to create, but I think it had too many moving parts for the goal of this challenge - as an introduction challenge.

The obscured barcode threw a few people off, and even the "k" on the end had people thinking they had it wrong!
I spent a lot of time moving the card on top of the barcode to obscure just enough of the barcode to make it a challenge, but not so much that it was impossible to decode.

Overall I was happy with the result, but I think a partial credit would have helped, to encourage people that have it partially right.

One of the challenges we scrapped as it was too difficult was a QR code that had a password encoded in it.
While QR codes have error-correction, I couldn't get the challenge enough - the best I had was a many-hour long brute-force error correction attempt!

I'll probably do something similar in next year's CTF, with the learnings applied from this challenge.
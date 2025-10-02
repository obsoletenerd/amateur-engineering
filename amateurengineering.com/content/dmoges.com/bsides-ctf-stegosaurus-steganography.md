---
Title: BSides 2025 CTF: Stegosaurus - LSB Steganography Challenge
Date: 2025-07-09T13:00:00+10:00
Tags: ctf, cybersecurity, bsides2025
Author: dmoges
AuthorURL: https://dmoges.com
Category: dmoges
Status: published
Cover: https://dmoges.com/images/bsides-ctf-stegosaurus-steganography/stegosaurus-challenge.png
---

This challenge was the most difficult I created for BSides CTF 2025.
I was worried about the difficulty, and it was multiple-intermediate steps in a row without a "checkpoint" to help participants.
However I did leave clues but I did not have anyone complete it, so I thought I would write this post to explain the challenge and how to solve it.

## Challenge Details

**Difficulty**: Difficult, with multiple intermediate steps in a row

**Category**: Steganography / Cryptography  

## Challenge Image

![Stegosaurus Challenge Image](https://dmoges.com/images/bsides-ctf-stegosaurus-steganography/stegosaurus-challenge.png)

It is important to note the filename of the image on the original server was `LSBSTEGO_CONFIG_LCG[1664525,1013904223,4294967296]_DEFAULT1111.png` which provides important clues about the challenge.

## Background: LSB Steganography

LSB steganography hides data in the least significant bits of pixel values. Since changing the LSB only alters a pixel's color value by 1 (out of 256), the modification is virtually imperceptible to the human eye.

### Linear Congruential Generator (LCG)

This challenge uses an LCG to determine which pixels contain hidden data. An LCG is a pseudo-random number generator defined by:

```
X(n+1) = (a * X(n) + c) mod m
```

Where:
- `a` = multiplier (1664525)
- `c` = increment (1013904223)
- `m` = modulus (4294967296)
- `X(0)` = seed value

The numbers above are from the filename, which I tried to make as obvious as possible, as they would not be guessable or otherwise identified.

## Challenge Analysis

### File Name Clues

The image filename provides crucial information:
```
LSBSTEGO_CONFIG_LCG[1664525,1013904223,4294967296]_DEFAULT1111.png
```

This reveals:
- LSB steganography is used
- LCG parameters: a=1664525, c=1013904223, m=4294967296
- Some default configuration (possibly seed or password related)

When I was writing this challenge, I was going to stop here.
However I thought it would be fun to have an extra step, and that helped the story element - these guys were writing their own algorithms which is never a good idea.

## Linear Congruential Generator (LCG) Implementation

You'll need a library for implementing the LCG.
It is not a difficult algorithm, but I recommend using a library to avoid mistakes.
I used a file called `lcg.py` which I got from [rossilor95's GitHub](https://github.com/rossilor95/lcg-python/blob/main/lcg.py)

I put a link to this repo in `/debug` on the server as a hint to participants.

The filename gives the parameters for the LCG including the seed.

```python
# Pseudo-code for extraction
seed = hash(password) % m
lcg = LCG(seed, a, c, m)
bits = []

for i in range(message_length * 8):
    pixel_index = lcg.next() % total_pixels
    pixel = image[pixel_index]
    # Extract LSB from R, G, B channels
    bits.extend([pixel.R & 1, pixel.G & 1, pixel.B & 1])

# Convert bits to ASCII
message = bits_to_ascii(bits)
```

In essence, LCG decides the next pixel to read based on the seed and parameters.
Then, if the LSB of the pixel is 1, it adds a 1 to the message, otherwise it adds a 0.
Repeat until the message is fully extracted.

## My thoughts

I really liked this challenge, but I think it was too difficult for the CTF.
The main issue was that it required multiple steps in a row without any "checkpoints" to help participants.

It is also quite fiddly, and a slightly incorrect implementation of the LCG would lead to a completely different result.
I chose LCG instead of other algorithms like Mersenne Twister or Xorshift because it is simple and easy to implement to minimise the chance of errors.

For next year's CTF, I might simplify this challenge by having a key file with pixel locations, or even a "LSB-Blue" to indicate a pixel is used for the message, and "LSB-Green" for the value.
Another option is to write the library itself and release it open-source, but that would move the challenge to "beginner" level.
---
Title: Binary Chords - The Binary-Chording 8% Mechanical Keyboard
Date: 2025-11-01 13:48
Modified: 2025-11-01 13:48
Summary: After having used a 60% mechanical keyboard for a fair while now, some joking-around at the local hackerspace made us think about ways to go even smaller. There's plenty of "chording" mechanical keyboards out there using their own combinations of chording and layers to shrink smaller, but most are still 10-12 keys or so... we thought we could go smaller by going closer to the bare metal, and going binary.
Category: ObsoleteNerd
Tags: Hardware, 3DPrinting, Software, Projects, Projects
Status: Published
Author: ObsoleteNerd
AuthorURL: https://obsoletenerd.com
Cover: https://obsoletenerd.com/images/2025-11-01-Binary-Chords-Final.jpg
---

I've used 60% wireless mechanical keyboards for a fair few years now, both as a portable keyboard when traveling, for PS5 games that support keyboards, and for Raspberry Pi projects... and I've also built various custom mechanical keyboards such as Dactyl Manuforms and a bunch of different macro pads. I like making keyboards and keyboard-related projects, but most of them are a huge investment in time (and sometimes money) just to try eek out minor improvements in typing speed or ergnonomics, and they rarely actually re-think how typing works.

Some joking around at my [local hackerspace](https://www.ballarathackerspace.org.au) had us coming up with new ideas for keyboards, a few of which were just outright silly (single-key morse-code keyboard anyone?) but one of which stuck in my head as actually having some fun potential... going closer to the bare metal. The ASCII table of characters recognised by all modern computers is mapped to a table of 8-bit binary values, and that's just 8 switches in on/off positions at the same time. That sounds a lot like a keyboard to me, but a keyboard where you play it like a piano (aka the other type of keyboard).

An 8% binary-chording mechanical keyboard.

I had just recently finished a 1-weekend project building a [little binary clock](https://github.com/obsoletenerd/esp32-binary-clock) for my desk (post coming soon), so binary is on the mind a lot at the moment... and I also had some leftover switches lying around from a project I did with the kids. A couple hours later, I had a prototype running using a Raspberry Pi Pico W and the packaging that keyboard switches get delivered in:

<img alt="Binary Chords Prototype" src="https://obsoletenerd.com/images/2025-11-01-Binary-Chords-Prototype.jpg" width="49%"><img alt="Binary Chords Prototype Wiring" src="https://obsoletenerd.com/images/2025-11-01-Binary-Chords-Prototype-Wiring.jpg" width="49%">

I took this into the hackerspace and it was actually more fun (and more usable) than expected, which prompted me to try turn it into more of a real thing.

I designed a new case in Fusion, then spent more time than I'd like to admit making pretty wiring that no one will ever see, and fixed up the code from the prototype with some feedback from people who used it. It's still very very basic code-wise, and only does the first 128 characters in the [ASCII table](https://www.ascii-code.com), a lot of which are control codes that aren't even recognised on modern systems. But it does work, and all the normal alphanumeric characters are there, plus basic punctuation, so you can actually type with it. The posts I put on [Bluesky](https://bsky.app/profile/obsolete.bsky.social/post/3m4mxhkuryk2j)/etc were typed using the keyboard itself.

<img alt="Binary Chords Case" src="https://obsoletenerd.com/images/2025-11-01-Binary-Chords-Case.jpg" width="49%"><img alt="Binary Chords Wiring" src="https://obsoletenerd.com/images/2025-11-01-Binary-Chords-Wiring.jpg" width="49%">

I may have also gone a bit overboard with the joke after someone mentioned needing a typing tutor to now learn how to type in binary, so had Claude Code whip up a PyGame Guitar-Hero clone that has random letters falling down for you to type at just the right time...

<img alt="Binary Chords The Game" src="https://github.com/obsoletenerd/binary-chords/raw/main/BinaryChordsTheGame.png" width="80%">

So yeah... that's 2 days of my life I'll never get back, but at least I kinda made something new in the keyboard scene that isn't just a fork-and-tweak of another project?

Code is available [on Github](https://github.com/obsoletenerd/binary-chords), but it's nothing special.

Maybe I'll do the morse-code one next.

<img alt="Binary Chords" src="https://obsoletenerd.com/images/2025-11-01-Binary-Chords-Final.jpg" width="80%">
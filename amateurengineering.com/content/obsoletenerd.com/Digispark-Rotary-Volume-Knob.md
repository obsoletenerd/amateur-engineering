---
Title: Digispark-based USB Volume Knob
Date: 2021-05-13 10:08
Modified: 2021-05-13 10:08
Summary: This is a very basic beginner-friendly project that gives a physical volume knob that works on most desktop/laptops. Using a rotary encoder, a Digispark microcontroller, a few soldered wires, some pre-existing firmware from Adafruit, and a 3D printed housing, we get a super tidy and tiny dial for controlling the system volume (or map it to whatever you want). It plugs directly into the side of my laptop into the USB port, or you can use it via a USB extension cable to place it on your desk.
Category: ObsoleteNerd
Tags: Projects, Hardware, Software, 3DPrinting, Projects
Status: Published
Author: ObsoleteNerd
Author-URL: https://obsoletenerd.com
Cover: https://raw.githubusercontent.com/obsoletenerd/digispark-volume-knob/main/Meta/DigisparkVolumeKnob-Desktop.jpg
---

My mechanical keyboard doesn't have media keys for volume/mute and while it's possible to map key combos to do the job, I've always preferred the tactile feedback of physical volume knobs. After making various other USB HID devices like a ["real" analog USB handbrake](https://github.com/obsoletenerd/analog-usb-handbrake) for my racing sim and my [arcade button macro board](http://obsoletenerd.com/arcade-macro-board-for-obs.html) for keyboard shortcuts, I figured making a volume knob should be easy enough. As is usual for me, I spent a solid evening looking up USB HID standards for media keys on standard desktop/laptop keyboards and got a prototype working using some very hacky code... then while doing some different searches on getting the Adafruit rotary encoder to work I came across [Adafruit's own tutorial](https://learn.adafruit.com/trinket-usb-volume-knob/) on making **exactly** this project, complete with fully working code for my exact encoder... typical. There has to be a name for that moment in projects where you've spent many hours trying to do something complicated, only to realise someone else has solved it and it's super easy.

It's a very basic project overall, suitable for beginners with only a few wires to solder and some copy/paste code with no modifications required (unless you change the pins used). The part that took the longest was designing the enclosure as I had a very specific goal in mind. I wanted it to be as small as possible, plug directly into my laptop and sit flush with the table, or plug into my PC via a USB extension cable to sit on my desk, and lastly I wanted it to show off the Digispark. I've also been playing with designing/printing enclosures that click together so that everything can come apart again later if a component needs replacing, rather than my old "just add more glue" approach.

*The below is a copy/paste from [the Github repo](https://github.com/obsoletenerd/digispark-volume-knob/):*

# Digispark Volume Knob

Physical rotary volume knob using a Digispark and rotary encoder, via USB HID standard media controls.

Plugs into any PC/laptop or any other USB device that accepts standard media controls (like the media keys on your generic keyboards), and translates the rotary knob into volume up/down, and clicking the knob as mute/unmute.

## Ingredients

- [Digispark](http://digistump.com/products/1) (or any similar Attiny85 board)
- [Rotary Encoder](https://core-electronics.com.au/rotary-encoder-extras.html)
- 3D printer, wire, soldering gear, a table, probably a few snacks, etc.

## Instructions

Print the 3 STLs in the repository: [Chassis v1.stl](https://github.com/obsoletenerd/digispark-volume-knob/blob/master/Chassis%20v1.stl), [Knob v1.stl](https://github.com/obsoletenerd/digispark-volume-knob/blob/main/Knob%20v1.stl) (unless you're using the knob that came with the encoder, but I preferred my minimal design) and [Lid v1.stl](https://github.com/obsoletenerd/digispark-volume-knob/blob/master/Lid%20v1.stl).

Mock the parts up inside the chassis to get an idea for wire lengths, then solder it all together outside of the chassis for better access. Check the encoder's [Data Sheet](https://cdn-shop.adafruit.com/datasheets/pec11.pdf) for pinouts if you're not sure, but the general idea is:

- Encoder channel A to Digispark pin 0
- Encoder channel B to Digispark pin 2
- Encoder common to Digispark pin GND
- Encoder switch pin 1 to Digispark pin 1
- Encoder switch pin 2 to Digispark 5V

<center>
<img alt="Digispark Volume Knob wiring" src="https://raw.githubusercontent.com/obsoletenerd/digispark-volume-knob/main/Meta/DigisparkVolumeKnob-Wiring.jpg" width="80%">
</center>

The code to load onto the Digispark is just the Adafruit ["Trinket USB Volume Knob" code](https://learn.adafruit.com/trinket-usb-volume-knob/add-a-mute-button), as their Trinket uses the same Attiny85 chip as the Digispark so they're 100% compatible. If you know what you're doing, you can copy/paste the code from my repository (don't forget to add the "TrinketHidCombo.h" library before compiling) or if you need more details, follow [their tutorial here](https://learn.adafruit.com/trinket-usb-volume-knob/code) and make sure you use the extra code from the "Add a Mute Button" page if you got an encoder with clicky switch.

I then used a bit of 3M double-sided tape to stick the encoder to the chassis piece and keep it stable (yet still be able to peel it off if it fails and needs to be replaced), or you could use hot glue, and then crammed all the wiring in:

<center>
<img alt="Digispark Volume Knob parts" src="https://raw.githubusercontent.com/obsoletenerd/digispark-volume-knob/main/Meta/DigisparkVolumeKnob-Parts.jpg" width="80%">

<img alt="Digispark Volume Knob assembly" src="https://raw.githubusercontent.com/obsoletenerd/digispark-volume-knob/main/Meta/DigisparkVolumeKnob-Assembly.jpg" width="80%">
</center>

The lid clicks onto the chassis (and is easily removable for repairs later), and then the knob clips onto the top of the encoder. NOTE: You might need to print the knob at 102% size if it's a bit too tight on your encoder, depends on your printers tolerances.

Depending on your laptop/device you can plug it directly into the USB port, or I use a small USB extension cable from my PC to have the knob sitting directly to the right of my mouse for easy volume adjustments.


<center>
<img alt="Digispark Volume Knob on a laptop" src="https://raw.githubusercontent.com/obsoletenerd/digispark-volume-knob/main/Meta/DigisparkVolumeKnob-Laptop.jpg" width="80%">

<img alt="Digispark Volume Knob on a PC" src="https://raw.githubusercontent.com/obsoletenerd/digispark-volume-knob/main/Meta/DigisparkVolumeKnob-Desktop.jpg" width="80%">
</center>
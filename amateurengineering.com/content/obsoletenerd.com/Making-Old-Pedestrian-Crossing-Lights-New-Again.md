---
Title: Making Old Pedestrian Crossing Lights New Again
Date: 2025-09-25 11:55
Modified: 2025-09-25 11:55
Summary: After impulsively buying a set of old pedestrian crossing lights at a local swap-meet (13 year old me forced me to), I wanted to get them going again both for the kids to use in the back yard and also for me to use to tell the kids when it is/isn't safe to come into the garage. I added 240V LED spotlights inside, controlled via relays with a Raspberry Pi Pico, and then a basic MicroPython state-machine that lets the crossing button or a timer control the different modes on the lights.
Category: ObsoleteNerd
Tags: Hardware, Software, Projects, Projects
Status: Published
Author: ObsoleteNerd
AuthorURL: https://obsoletenerd.com
Cover: https://obsoletenerd.com/images/2025-09-25-Pedestrian-Lights-Playground.jpg
---

Childhood-me always wanted a set of traffic lights in my room, but it wasn't until adult-me saw a stall selling them at a local swap-meet that I realised there's nothing actually stopping that from happening. They were selling some pedestrian crossing lights really cheaply that were in pretty rough condition, but that suited me perfectly as I planned on putting modern lights inside anyway.

I wanted to turn them into something that has both a useful-purpose, which is telling the kids when it's safe to come into the garage when I'm welding/grinding, but also have some more fun usecases like letting the kids use them as a timer for the trampoline or when playing around in the back yard.

## The Hardware

The entire thing was very rusty and corroded when I bought it, hence the cheap price, and getting the old brackets off used every ounce of strength and leverage I could muster. I soaked all the bolts for days, used breaker-bars on the end of my biggest wrenches, and even sheered one of the massive bolts in half trying to loosen the nuts. Ultimately I did get all the old hardware off and then gutted the internals of the light box which still had the original reflectors and bulbs, but the wiring was all so corroded it wasn't worth re-using. I gave it all a pretty solid clean but decided not to repaint it all yet, as I like how used/original it looks as-is. I might end up stripping and repainting it all one day, as childhood-me always wanted a set of traffic lights that have been entirely chrome plated.

<img alt="Pedestrian Lights as Purchased" src="https://obsoletenerd.com/images/2025-09-25-Pedestrian-Lights-Start.jpg" width="49%"><img alt="Inside the Pedestrian Lights" src="https://obsoletenerd.com/images/2025-09-25-Pedestrian-Lights-Opened.jpg" width="49%">
<img alt="Pedestrian Lights Standard Internals" src="https://obsoletenerd.com/images/2025-09-25-Pedestrian-Lights-Inside.jpg" width="49%"><img alt="Pedestrian Lights with Empty Internals" src="https://obsoletenerd.com/images/2025-09-25-Pedestrian-Lights-Gutted.jpg" width="49%">

For new lighting inside I played with a bunch of bright LED modules but none of them were bright enough to really work in daytime so I ended up going for 2 outdoor 240V spotlights designed to put on the side of your house or garage. Internally I just used the standard wall plugs and some extension cords so that it's changeable easily later if I need/want to. They're already designed for outside so are mostly water proof(/resistent) but the light box itself also closes with rubber gaskets and bolts so very little water should ever get in even if it was left in the rain.

<img alt="Putting LED Spotlights in the Pedestrian Lights" src="https://obsoletenerd.com/images/2025-09-25-Pedestrian-Lights-LEDs.jpg" width="49%"><img alt="Pedestrian Lights with New Internals" src="https://obsoletenerd.com/images/2025-09-25-Pedestrian-Lights-New-Internals.jpg" width="49%">

For the controller box and electronics I started with an off-the-shelf outdoor electronics box bought from an electrial supplier and then bought an industrial metal push-button from Aliexpress that looked the part. I mounted the button to the front panel of the electronics box and then shoved all the components inside in individual 3D printed holders. There's a Raspberry Pi Pico talking to 2 solid-state relays (which I later learned aren't ideal for this due to current leakage, but it "works" for now), and a 5V module to give the Pi Pico power off the 240V lines. I added proper outdoor wire grommets for everything to try keep it as weather-sealed as possible, but I don't ever expect to actually leave this out in the rain. It just felt like the right thing to do and added to the industrial look of it all.

<img alt="Pedestrian Lights Prototype" src="https://obsoletenerd.com/images/2025-09-25-Pedestrian-Lights-Prototype.jpg" width="49%"><img alt="Raspberry Pi Pico Powered Pedestrian Lights" src="https://obsoletenerd.com/images/2025-09-25-Pedestrian-Lights-Controller.jpg" width="49%">

I built the frame using various odds and ends from the local hardware store. The main post is a fence post from a swimming pool fence, as they're very cheap for the size/strength and come with a baseplate with bolt holes already welded on and the whole thing is powder coated. The "feet" I made from some scrap galvanised square-tube that I had lying around, so I cut and welded pieces into an X with a steep angle as the entire thing is shakier forward/back then left/right due to the front-heavy nature of the pedestrian lights. I then drilled holes for it to  bolt to the fence post and coated it in a few coats of enamel paint. To mount the actual pedestrian lights themselves I found some chunky galvanised steel L brackets and drilled holes to put stainless bolts through. The whole structure is massively overkill and could probably hold up a small car, but the light box is so massive and heavy-looking that anything less than this would've just looked weird.

<img alt="Pedestrian Light Brackets" src="https://obsoletenerd.com/images/2025-09-25-Pedestrian-Lights-Brackets.jpg" width="49%"><img alt="Making Steel Feet for the Pedestrian Lights" src="https://obsoletenerd.com/images/2025-09-25-Pedestrian-Lights-Feet.jpg" width="49%">


### The Software

The code is quite basic for now, and just has 2 modes, a timer mode where it acts like normal pedestrian lights and a toggle mode where the button just swaps the lights between red/green/off.

The timer mode is great for the kids to use as a trampoline timer, riding their bicycles/etc around the yard, or using for games like hide-and-seek. It stays red until the button is pressed, then goes green for a preprogrammed amount of seconds (3 minutes by default), then flashes red a few times before setting back to permanent red. The kids have found heaps of uses for it already and are coming up with new ideas all the time, to the point where I'm now working on an upgraded version of the firmware that has a web dashboard where you can control it remotely, adjust the timers, come up with new modes, and more.

Below is the standard firmware that is offline-only and you just set a variable to change it between timer mode or manual mode. Being MicroPython this can be changed easily just by plugging a laptop into the USB port of the Pi Pico, no recompilation or re-flashing anything. That's a huge reason I've been using MicroPython where possible now, it makes changes so easy in projects like this that are going to evolve over time.

```MicroPython
################################################################
# Pedestrian Lights Controller by ObsoleteNerd
# Offline Version (No Wifi) v0.4
# https://github.com/obsoletenerd/Pidestrian
################################################################

from machine import Pin
import time

# 1 = Timer on. Works like a Pedestrian Crossing, press button
# and it goes green for timer_period seconds, then flashes red,
# then goes solid red until button pressed again.
#
# 0 = Timer off. Button toggles red/green/off.
timer_mode = 0

# Timer Period - Edit this to change "Green" time when in timer mode.
timer_period = 180 # 3 minutes

# Set up the 2 relay pins
red_light = Pin(27, Pin.OUT)
green_light = Pin(28, Pin.OUT)

# Set up the physical button
pin = Pin(22, Pin.IN, Pin.PULL_UP)

# Button interrupt and debounce
interrupt_flag = 0
debounce_time = 0

# Ghetto State Machine
current_state = "Stop"
states = ["Off", "Go", "Flash", "Stop", "Timer", "Boot"]

# Helper functions to make the code more readable
# Relays are active-low, so swap them for simplicity
# There's probably a better way to do this but i'm le tired
def red_light_on():
    red_light.off()  # Active-low: off = relay on = light on

def red_light_off():
    red_light.on()   # Active-low: on = relay off = light off

def green_light_on():
    green_light.off()  # Active-low: off = relay on = light on

def green_light_off():
    green_light.on()   # Active-low: on = relay off = light off

def all_lights_off():
    red_light_off()
    green_light_off()

# State changer
def change_state(state):
    global current_state, red_light, green_light

    current_state = state
    print('Changed to %s State' % current_state)
    global red_light, green_light

    if state == "Off":
        all_lights_off()
    elif state == "Go":
        red_light_off()
        green_light_on()
    elif state == "Flash":
        all_lights_off()
        for i in range(16):
            red_light_on()
            time.sleep(0.2)
            red_light_off()
            time.sleep(0.2)
        change_state("Off")
    elif state == "Stop":
        red_light_on()
        green_light_off()
    elif state == "Timer":
        red_light_off()
        green_light_on()
        time.sleep(timer_period)
        change_state("Flash")
    elif state == "Boot":
        for i in range(8):
            red_light_on()
            green_light_on()
            time.sleep(0.2)
            all_lights_off()
            time.sleep(0.2)
        change_state("Off")

# Handle interrupts for button
def callback(pin):
    global interrupt_flag, debounce_time
    if (time.ticks_ms() - debounce_time) > 500:
        interrupt_flag = 1
        debounce_time = time.ticks_ms()

pin.irq(trigger=Pin.IRQ_FALLING, handler=callback)

# Time to put it all together...
change_state("Boot")

while True:
    if interrupt_flag == 1:
        interrupt_flag = 0
        print("Button Pressed!")

        if timer_mode == 1:
            print("Timer Mode")
            change_state("Timer")
        else:
            print("Manual Mode")
            if current_state == "Off":
                print("Off State, Change to Stop (Red)")
                change_state("Stop")
            elif current_state == "Stop":
                print("Stop State, Change to Go (Green)")
                change_state("Go")
            elif current_state == "Go":
                print("Go State, Change to Off")
                change_state("Off")
            else:
                print('State is %s' % current_state)

    time.sleep(0.1)  # Add a small delay to avoid high CPU usage

```

## The Results

Overall I'm very happy with how this turned out. It wasn't a "big" project by any means, but it did involve a lot of different parts that each needed a fair bit of figuring out. Getting the feet right so that the unit was stable when kids are messing with it, getting the right lights to work even on a bright sunny day, finding all the right components that will actually work for an outdoor project, etc etc.

I would definitely like to finish the v2 of the firmware that allows more control via your phone, eg being able to set different timer lengths or make up new modes entirely for other backyard games, or just being able to swap between modes without plugging in a laptop. I also do think I'd like to strip and repaint it all in some funky colours so it's more of a tech-art piece and less of a "traffic lights stuck on a fence post" vibe, though it all does work well right now so none of that is a high priority.

Next I would really like to get a set of proper traffic lights for the driveway and do something similar to this, but letting the kids know when a car is entering/leaving so they don't walk/ride onto the driveway when a car is there. It's a lot of fun taking this old commercial equipment and finding uses for it at home and it's all built so well that you'll never find/make something yourselve to this quality without putting in more hours than it's ever worth.

<img alt="Pedestrian Light as a Workshop Warning" src="https://obsoletenerd.com/images/2025-09-25-Pedestrian-Lights-Workshop.jpg" width="49%"><img alt="Pedestrian Lights as a Trampoline Timer" src="https://obsoletenerd.com/images/2025-09-25-Pedestrian-Lights-Playground.jpg" width="49%">
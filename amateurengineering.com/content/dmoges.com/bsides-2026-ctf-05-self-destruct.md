---
Title: BSides 2026 CTF: Challenge 5 - Stop the Self-Destruct
Date: 2026-03-12T15:00:00+10:00
Tags: ctf, cybersecurity, bsides2026, hardware, bsides
Author: dmoges
AuthorURL: https://dmoges.com
Category: dmoges
Status: published
Cover: https://dmoges.com/images/bsides-2026-ctf-05-self-destruct/image.jpg
---

This was the grand finale - a physical hardware challenge where teams had to cut real wires under time pressure. I wanted the CTF to end with something you can't do at home behind a keyboard, something that gets your heart rate up.

## Challenge Details

**Difficulty**: Hard

**Category**: Hardware / Physical

## The Setup

**This post contains full spoilers including the complete solution.** If you want to try the challenges yourself first, the challenge environments are available in the [BSides Ballarat CTF git repo](https://github.com/bsides-ballarat/CTF2026-overview).

The mining facility is rigged with explosives set to destroy all evidence if the operation is discovered. A 10-minute countdown has started, and your team needs to physically disarm the system before it hits zero.

## Step-by-Step Solution

### Step 1: Connect via Serial

The hardware rig has a USB-C port labelled "DEBUG". Connect to it at 115200 baud.

**Linux:**
```bash
screen /dev/ttyACM0 115200
# or
picocom /dev/ttyACM0 -b 115200
```

**macOS:**
```bash
screen /dev/tty.usbmodem* 115200
```

**Windows:** Use PuTTY or TeraTerm, select the COM port from Device Manager, set baud to 115200. I dunno - ask Copilot or something.

**How you'd know to do this**: The USB-C port is physically labelled "DEBUG" on the hardware. Serial debug ports are standard on embedded systems. The baud rate 115200 is the most common default - if you've ever worked with Arduino or Raspberry Pi, this is familiar. The device physically says the protocol on the debug port, I didn't want that to be much of a challenge to work out.

Once connected, type `HELP`:

```
Available commands:
  CONNECT <passcode>      - Authenticate to the system
  DIAGNOSTIC-FULL         - Show override circuit wiring (requires auth)
  STATUS                  - Get current state
  HELP                    - Show this help
  HISTORY                 - Show command history
```

### Step 2: Figure Out the Passcode

There is a CONNECT command, but it required a passcode. Luckily, history is saved on the device, so if you just hit the up arrow 15 times, it shows you the last time someone logged in with the code:

```
> CONNECT 1374
==================================================
[OK] PASSCODE ACCEPTED
Access granted to network diagnostics
==================================================
```

**How you'd know to do this**: It is common to check for previous commands when connecting to a server the first time. This wasn't a real prompt, so there is no `.bash_history` file, but you are told the up/down arrows work when you enter HELP. 

### Step 3: Spot the Anomaly

After authentication, the system shows network diagnostics for all 8 ports:

```
Network Activity Monitor:
--------------------------------------------------
  Port 1: 300 packets/sec [ACTIVE]
  Port 3: [DISCONNECTED]
  Port 7: 652 packets/sec [ACTIVE]
  Port 4: 478 packets/sec [ACTIVE]
  Port 0: 423 packets/sec [ACTIVE]
  Port 5: [DISCONNECTED]
  Port 6: 149 packets/sec [ACTIVE]
  Port 2: 326 packets/sec [ACTIVE]
--------------------------------------------------

WARNING: Do not disconnect brown and white-brown
signal wires. These carry essential monitoring data.
```

Two ports show as disconnected: Port 3 and Port 5. Now look at the physical hardware:

- **Port 5**: No cable plugged in. Legitimately empty.
- **Port 3**: Has a cable plugged in, but shows as disconnected in diagnostics. **That's the anomaly.**

Port 3 is the override circuit disguised as a regular network cable.

**How you'd know to do this**: Comparing what the software says to what you physically see is the key insight. If both disconnected ports had no cables, there'd be nothing unusual. But one has a cable that the system doesn't recognise - that's your target.

### Step 4: Find Out Which Wires to Cut

You need the `DIAGNOSTIC-FULL` command. There are two ways to discover it:

**Path A - From Challenge 3's emails**: Trevor's email about the override system explicitly mentions "manufacturing diagnostic mode" accessed via `DIAGNOSTIC-FULL`. If you noted this during Challenge 3, you're already set.

**Path B - Buffer overflow discovery**: Send a really long command (300+ characters):

```
> AAAAAAAAAA... (300+ A's)

FAULT: Command buffer overflow
Buffer size: 300 bytes (max: 256)
CRITICAL ERROR - Dumping command registry:
  Standard Commands: CONNECT, DIAGNOSTIC-FULL, STATUS, HISTORY, HELP
System stabilized. Resuming normal operation...
```

The overflow triggers an error dump that reveals the full command list including `DIAGNOSTIC-FULL`.

**How you'd know to try Path B**: If you missed the email hint, fuzzing the serial interface is a natural thing to try. Long inputs, special characters, unexpected commands - standard embedded systems testing. The command is also listed in the `HELP` output, so you may already know about it.

Now run the diagnostic:

```
> DIAGNOSTIC-FULL

==================================================
  OVERRIDE CIRCUIT -- MAINTENANCE LOG
  Port 3, last serviced 14/02/2026
==================================================

Cable wiring map (Cat5e, T-568B pinout):
--------------------------------------------------
  Pin 1  White-Orange    Disconnect detection
  Pin 2  Orange          Trigger signal (PRIMARY IGNITION PULSE) ← TARGET
  Pin 3  White-Green     Firing ground (detonator return path) ← TARGET
  Pin 6  Green           Firing supply (+9V detonator power) ← TARGET
  Pin 4  Blue            Data line
  Pin 5  White-Blue      Data line
  Pin 7  Brown           Disconnect detection
  Pin 8  White-Brown     Disconnect detection
--------------------------------------------------
```

The output tells you exactly which wires to cut. The targets are marked - in this example, Orange, White-Green, and Green. (The specific wires are randomised each game, so you can't memorise them from watching another team.)

### Step 5: Cut the Wires

Locate the Port 3 cable on the patch panel and strip the outer jacket to expose the coloured wires inside. Use the wire cutters we provided at the station.

The Raspberry Pi Pico 2 detects each cut automatically via GPIO - an intact wire pulls the pin LOW (connected to ground), and a cut wire floats HIGH (pull-up resistor, no ground path). No need to type anything; the system announces each cut:

```
[OK] Trigger wire cut: Orange
2 wires remaining.

[OK] Trigger wire cut: Green
1 wire remaining.

[OK] Trigger wire cut: White-Green

==================================================
[OK] OVERRIDE CIRCUIT DISABLED!
Detonator bypass successful
Self-destruct sequence ABORTED
Countdown STOPPED
==================================================

Time remaining: 07:30
MISSION SUCCESS!
```

Green LED turns on, red LED turns off, three victory beeps.

### What Happens If You Cut the Wrong Wire?

Cutting a wrong wire doesn't end the game, but it speeds up the countdown. The multiplier starts at 1x, and each mistake adds 1x:

- First wrong cut: timer runs at 2x speed
- Second wrong cut: 3x speed
- And so on...

There's also a safety mechanism: if both Brown and White-Brown wires are cut (the monitoring wires), the system detects "cable removed" and gives you 30 seconds to reconnect before an automatic failure. The diagnostic warning about not disconnecting these isn't just flavour text.

## The Physical Setup

I went all-in on atmosphere for this one. The challenge station was set up as a "briefcase" with:
- Red/Green emergency lighting
- Warning signs
- Wire strippers and cutters laid out on the table
- NeoPixel ring showing countdown (blue arc shrinking to red)
- NeoPixel strip with status animations and a subtle blue blink pattern: 1-3-7-4 (another passcode hint)

Participants were guided on setup and the expectation that they would actually need to cut wires.
We couldn't think of a way to make this obvious - people aren't naturally expecting to cut into props like this.

Here's the rig itself, set up during the event:

![The self-destruct challenge briefcase, with patch panel, warning labels, and countdown hardware visible](https://dmoges.com/images/bsides-2026-ctf-05-self-destruct/image.jpg)

## Real-World Relevance

OK, the "cutting wires to defuse a bomb" scenario is obviously dramatised, but the underlying skills are real:
- **Serial communication and hardware debugging**: Every embedded system has a debug port
- **Network diagnostics and anomaly detection**: Finding the one port that doesn't match the rest
- **Working under pressure**: Incident response is stressful, and the ability to stay methodical when things are going wrong is critical

The countdown mechanic with escalating penalties mirrors real incident response, where initial mistakes compound and reduce your remaining response time.

That said, this was more puzzle than cybersecurity. I expect very few participants to need these skills in the real world - but it was fun to build and for the teams to try out.

## My thoughts

This was by far the most work to build, and by far the most rewarding to watch teams play. The physical component completely changes the dynamic - you can't Google your way through cutting a wire with 4 minutes on the clock.

The escalating speed penalty was a late addition that I'm really glad I included. It creates genuine tension without being unfair - you can still succeed after a mistake, but the pressure ratchets up. Teams that stayed calm and methodical did much better than teams that panicked and started guessing.

I'll do a separate post a little later on the actual physical build.

For future CTFs, I want to expand the physical component even further. The reactions from teams when they successfully defused the system - the relief, the cheering - were the highlight of the whole event. That's something you just can't get from a terminal.
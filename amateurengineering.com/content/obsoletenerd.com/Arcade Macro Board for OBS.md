---
Title: Arcade Macro Board for OBS
Date: 2020-05-15 11:21
Modified: 2020-05-15 11:21
Summary: Since the coronapocalypse kicked in and we've all been isolated, I've been doing a lot of Jitsi meets with various groups of friends. Jitsi is basically Zoom but with less spyware and more "it crashes lots and has lots of bugs but it's Open Source so we convince ourselves it's worth it anyway". In this post we use some old arcade cabinet buttons and an Arduino to build an OBS scene-changing macro board. This lets you swap scenes in video chats and when streaming, or also just works as a generic macro-board for running key combinations, scripts, and macros on any USB-having device.
Category: ObsoleteNerd
Tags: Projects, Hardware, Software, 3DPrinting, Projects
Status: Published
Author: ObsoleteNerd
Author-URL: https://obsoletenerd.com
---

Since the coronapocalypse kicked in and we've all been isolated, I've been doing a lot of Jitsi meets with various groups of friends. Jitsi is basically Zoom but with less spyware and more "it crashes lots and has lots of bugs but it's Open Source so we convince ourselves it's worth it anyway". We'll get togther for a video chat, and thanks to [OBS (open source broadcasting software)](https://obsproject.com/) we can do things like sharing our screens to each other while video chatting, or play a board game and have one person contol and share the board view while everyone else chats and says their moves, and lots more.

In OBS you set up "Scenes", which are basically layouts of what you want to show each other. One might be your webcam view of yourself placed in the corner of a screen showing your coding IDE, so you can teach someone some code or share a non-live project you're working on. Another might be the screen showing a game you're playing. It's the software used by almost every single Twitch/YouTube streamer and live online show, and it's extremely powerful software considering it's completely free.

One thing that I've seen streamers do that I thought would also be useful for our private video chats is to buy a [Stream Deck](https://www.elgato.com/en/gaming/stream-deck), which is a physical panel of buttons that let you quickly change Scenes in OBS without having to change back to your OBS window or fiddle with your mouse. It's a very handy piece of equipment, but considering i'm not a streamer and have no real intent to ever be one (I don't even like mirrors), I can't really justify forking out the cash for a product like that. So... we make one.

<center><img src="https://obsoletenerd.com/images/2020-05-15-Arcade-Macro-Board-ArcadeMacroKeyboard2.jpg" width="80%" alt="Arcade Macro Board"></center>

<center><img src="https://obsoletenerd.com/images/2020-05-15-Arcade-Macro-Board-ArcadeMacroKeyboard3.jpg" width="80%" alt="Arcade Macro Board Interior"></center>

## Arcade Macro Keyboard

The below is pasted from this Github repository, so check there for code/etc: [https://github.com/obsoletenerd/arcade-macro-keyboard/](https://github.com/obsoletenerd/arcade-macro-keyboard/)

A macro keyboard made of arcade buttons. Acts like a normal USB keyboard, but each arcade button runs multi-key macros/shortcuts such as CTRL-ALT-SHIFT-1, which you can then map in OBS to any OBS function.

## Example Use

I use it as a Stream Deck using OBS for Twitch/YouTube streaming and Jitsi video calls. I set the "keyCodes" in the code to numbers 1-7 (ASCII 49-55), and the modifiers to CTRL, ALT, and SHIFT. Pressing arcade button 1 then sends the macro CTRL+ALT+SHIFT+1 to Windows, which I have mapped in OBS to switch to Scene 1. Etc etc.

It will also work everywhere in your OS not just OBS/Jitsi/etc as it just acts like a standard USB keyboard inserting the shortcuts as though you yourself pressed it on your primary keyboard. You could use it to run macros/combos for your games, or for running scripts/macros in productivity software and photo/video editing, or whatever you want.

Number of buttons doesn't matter, you can do more or less, as long as you have enough inputs and modify the code appropriately to add/remove them. Diagram below shows 8, but the code here is currently set up for 7 as that's all I ended up using.

## Wiring Diagram

<center><img src="https://obsoletenerd.com/images/2020-05-15-Arcade-Macro-Board-WiringDiagram.png" width="80%" alt="Arcade Macro Keyboard Diagram"></center>

## Installation

- Load the code onto your Arduino Nano
- Plug the USB cable into your PC
- Open up your OBS Settings and go to Hotkeys (this assumes you already have scenes set up)
- Click on each of your scene's "Switch to Scene" entry, and press one of the buttons on the macro board to insert that button's shortcut combo

<center><img src="https://obsoletenerd.com/images/2020-05-15-Arcade-Macro-Board-MappingButtonsInOBS.png" width="80%" alt="OBS Hotkeys"></center>

- Click OK

## Arduino

Want to use the Arduino IDE instead of VS Code? The .cpp file in /src should work fine as-is, or you can visit the [Arcade Macro Keyboard Sketchbook](https://create.arduino.cc/editor/obsoletenerd/15b42f98-5e19-4aff-b1d9-8078c02f6f8f/preview) on Arduino.cc to install the code directly from the browser to your Arduino Nano.

Early prototype with a 3D printed case:

<center><img src="https://obsoletenerd.com/images/2020-05-15-Arcade-Macro-Board-ArcadeMacroKeyboard1.jpg" width="80%" alt="Arcade Macro Board Prototype"></center>
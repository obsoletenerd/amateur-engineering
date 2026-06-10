---
Title: Adding Wi-Fi to an Ikea Vindriktning Sensor
Date: 2022-07-20 11:14
Modified: 2022-07-20 11:14
Summary: The Ikea Vindriktning air quality sensors are a very cheap and well built sensor for checking the air quality of your room at a glance, but they don't come with Wi-Fi. This is a quick and easy project to add a $5 Wi-Fi module (via an ESP8266) to the Vindriktning, letting it share the air quality readings with your home automation system or just to your phone/computer.
Category: ObsoleteNerd
Tags: Projects, Hardware, 3DPrinting, Projects
Status: Published
Author: ObsoleteNerd
AuthorURL: https://obsoletenerd.com
Cover: https://obsoletenerd.com/images/2022-07-20-Hacked-Ikea-Vindriktning-with-ESP8266.jpg
---

The Ikea Vindriktning air quality sensors are a very cheap and well built sensor for checking the air quality of your room at a glance, but they don't come with Wi-Fi or a way to remotely monitor data. 

This is a quick and easy project to add a $5 Wi-Fi module (via an ESP8266) to the Vindriktning PM2.5 sensor, letting it share the air quality readings with your home automation system or just to your phone/computer.

I have a few of these around the house feeding data regularly into a large database along with all my weather sensors, room thermometers, etc, as a way of tracking historical data in and around my house and do comparisons/graphing.

To convert a cheap non-smart Vindriktning sensor into a smart one, you only need a few things...

You'll need an [Ikea Vindriktning](https://www.ikea.com/au/en/p/vindriktning-air-quality-sensor-50498243/) air quality sensor, an ESP8266 dev module, a few bits of wire, and an optional 3D printed bracket that just makes it all look more professional.

<img alt="Ingredients for adding Wi-Fi to a Vindriktning sensor" src="https://obsoletenerd.com/images/2022-07-20-Hacking-Ikea-Vindriktning-Sensor.jpg" width="98%">

The PM2.5 Sensor talks to the Vindriktning controller via UART protocol, which we can tap into via the `REST` pin on the PCB, and conveniently also borrow 5V and GND to power our ESP8266.

First solder your 3 wires to the Vindriktning sensor's exposed pads, leaving enough wire to tuck around the ESP8266 as pictured further down below. 

I whipped up a little 3D printed bracket to hold my ESP8266 in a convenient location out of the air flow of the sensor, but you could also just hot glue it somewhere or use double sided tape. As long as it's not blocking the sensor or touch/shorting anything.

<img alt="Soldering wires to the Vindriktning sensor" src="https://obsoletenerd.com/images/2022-07-20-Adding-Wires-to-Vindriktning-Sensor.jpg" width="49%"><img alt="3D printed bracket for the ESP8266" src="https://obsoletenerd.com/images/2022-07-20-Bracket-for-Ikea-Vindriktning.jpg" width="49%">

Solder the other ends of the wires to the ESP8266. 5v to 5v, GND to GND, and REST to the GPIO pin labelled D4 on the ESP. I tucked my GND wire underneath to still fit the JST connector in and make it all a bit more compact, but you can route the wires however works in your situation.

Once the wires are soldered in, that's it... you reconnect and reassemble everything.

<img alt="Soldering wires to the ESP8266" src="https://obsoletenerd.com/images/2022-07-20-ESP8266-to-Ikea-Vindriktning.jpg" width="49%"><img alt="Re-assembling the completed sensor" src="https://obsoletenerd.com/images/content/images/2022-07-20-Reconnecting-Ikea-Vindriktning.jpg" width="49%">

You can then [flash ESPHome](https://esphome.io/guides/getting_started_hassio/#installing-esphome-dashboard) onto your ESP8266 if you have Home Assistant or other home automation, or to serve it up via API to your other devices. There's [lots of tutorials](https://esphome.io/components/sensor/pm1006/) for this part as it is now just a very basic wireless sensor. I'm not going to re-write what's been written a thousand times, I mostly just put this post up to tick another project post off my list.

<img alt="Ikea Vindriktning sensor with Wi-Fi" src="https://obsoletenerd.com/images/2022-07-20-Hacked-Ikea-Vindriktning-with-ESP8266.jpg" width="98%">
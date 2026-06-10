---
Title: BSides 2026 CTF: Challenge 1 - Find the Company
Date: 2026-03-12T11:00:00+10:00
Tags: ctf, cybersecurity, bsides2026, forensics, bsides
Author: dmoges
AuthorURL: https://dmoges.com
Category: dmoges
Status: published
Cover: /images/placeholder.jpg
---

I wanted Challenge 1 to kick things off with something that felt like real forensic work, not just another web challenge. Teams needed to dig through smart meter traffic to find an illegal bitcoin mining operation hiding in plain sight.

## Challenge Details

**Difficulty**: Easy

**Category**: Forensics / Network Analysis

## The Setup

You get a PCAP file containing captured smart meter traffic from Ballarat's electricity grid. Somewhere in the data is a building with suspiciously high power consumption - the kind you'd expect from a rack of mining hardware running 24/7.

The protocol is DLMS/COSEM, which is the actual standard used by Victorian smart meters. I wanted this to feel authentic, even if most people wouldn't have seen this protocol before.

**This post contains full spoilers including flags and solutions.** If you want to try the challenges yourself first, the challenge environments are available in the [BSides Ballarat CTF git repo](https://github.com/bsides-ballarat/CTF2026-overview).

## How to Approach This

The PCAP contains traffic from 15 different smart meters across Ballarat. The challenge introduction tells you DLMS uses TCP port 4059, and provides a table of OBIS codes - the addressing scheme that identifies what each data field means. The key one is `1.0.1.7.0.255` for instantaneous power (kW).

The core insight is that bitcoin mining has a very distinctive power signature: **high constant load with almost zero variance**. Normal buildings have day/night cycles, business hours patterns, weather-dependent HVAC. Mining rigs don't sleep.

There are several ways to solve this.

## Solution Path A: Python with Scapy

This is the most thorough approach. Load the PCAP, filter for DLMS traffic, parse the meter responses, and do the statistical analysis.

```python
from scapy.all import rdpcap, TCP, IP
from collections import defaultdict
import statistics, re

packets = rdpcap('ballarat_mdms_poll.pcap')

# Filter for DLMS responses (FROM port 4059)
meter_data = defaultdict(lambda: {
    'nmi': None, 'building': None, 'address': None,
    'power_readings': [], 'serial': None
})

for pkt in packets:
    if TCP in pkt and pkt[TCP].sport == 4059 and pkt.haslayer('Raw'):
        payload = bytes(pkt['Raw'].load).decode('utf-8', errors='ignore')
        src_ip = pkt[IP].src
        for line in payload.split('\n'):
            if '|' not in line:
                continue
            parts = line.strip().split('|')
            obis = parts[0]
            if obis == '1.0.1.7.0.255':  # Instantaneous power
                meter_data[src_ip]['power_readings'].append(float(parts[1]))
            elif obis == '0.0.42.0.0.255':  # Building info
                meter_data[src_ip]['nmi'] = re.search(r'NMI:(\d+)', line).group(1)
                meter_data[src_ip]['building'] = parts[2].strip()
                meter_data[src_ip]['address'] = parts[3].strip()
            elif obis == '0.0.96.1.0.255':  # Serial + hidden data
                meter_data[src_ip]['serial'] = '|'.join(parts[1:])
```

Then calculate statistics and look for the anomaly:

```python
for ip, data in meter_data.items():
    readings = data['power_readings']
    avg = statistics.mean(readings)
    variance_pct = (statistics.stdev(readings) / avg) * 100 if len(readings) > 1 else 0
    print(f"{data['building']:<40} | {avg:6.1f} kW | Variance: {variance_pct:5.1f}%")
```

The output makes the anomaly obvious:

```
Ballarat Engineering Supplies           |   42.0 kW | Variance:   0.1%
Cold Storage Warehouse                  |   29.1 kW | Variance:   0.7%
Craig's Royal Hotel                     |   19.3 kW | Variance:   6.4%
Ballarat Community Health               |   16.6 kW | Variance:   5.9%
...
```

Only one meter has both high power (42 kW) AND extremely low variance (0.1%). That's your target.

**How you'd know to do this**: The challenge introduction explicitly mentions "statistical anomalies" and contrasts normal buildings (5-30% variance) with mining operations (<3% variance). The OBIS code table tells you which fields contain power readings.

## Solution Path B: Wireshark (No Coding Required)

If you're not comfortable with Python, Wireshark works fine:

1. Open the PCAP, filter with `tcp.port == 4059`
2. For each source IP, right-click a packet → Follow → TCP Stream → set to ASCII
3. You'll see pipe-delimited data like:

```
1.0.1.7.0.255|42.036|kW
0.0.42.0.0.255|NMI:6102473951|Ballarat Engineering Supplies|315 Sturt Street|
0.0.96.1.0.255|AE0453928|FLAG:SD_SEQUENCE_BLUE_SEVEN_ALPHA|
```

4. Record the power readings and building names for each meter in a spreadsheet
5. Calculate average and variance - the outlier jumps out immediately


## Solution Path C: tshark + Command Line

Quick and dirty without a GUI:

```bash
# Extract all meter data as ASCII
tcpdump -r ballarat_mdms_poll.pcap -A tcp port 4059 > meter_data.txt

# Find the highest power consumers
grep "^1.0.1.7.0.255" meter_data.txt | awk -F'|' '{print $2}' | sort -n | tail -5

# Find who has >40 kW readings
grep -B5 "1.0.1.7.0.255|4[0-9]" meter_data.txt | grep "0.0.42.0.0.255"
```

## The Flags

### Flag 1: Identify the Building (100 points)

**Flag**: `BSides2026{ballarat_engineering_supplies_315_sturt_st}`

The building with 42 kW constant draw is Ballarat Engineering Supplies at 315 Sturt Street. Two readings of 42.036 kW and 41.995 kW - a variance of 0.07%. Compare that to Cold Storage Warehouse at 29 kW with 0.7% variance (compressor cycling), or Craig's Royal Hotel at 19 kW with 6.4% variance (normal hotel operations). The mining rig signature is unmistakable.

### Flag 2: Extract Meter Details (50 points)

**Flag**: `BSides2026{6102473951_AE0453928}`

Deeper in the DLMS data for the suspicious meter, the OBIS code `0.0.42.0.0.255` contains the NMI (National Metering Identifier) `6102473951` and code `0.0.96.1.0.255` has the serial number `AE0453928`. These are standard fields in NEM12 format that Australian energy companies use.

**How you'd know to look here**: The challenge hints mention "exact NMI and meter serial number" for the bonus flag. The OBIS code table in the introduction tells you which codes contain meter identification data.

### Flag 3: Hidden Metadata (25 points)

**Flag**: `SD_SEQUENCE_BLUE_SEVEN_ALPHA`

Buried in the serial number field (OBIS `0.0.96.1.0.255`) is extra data: `AE0453928|FLAG:SD_SEQUENCE_BLUE_SEVEN_ALPHA|`. At this point in the CTF you wouldn't know what this means - but if you noted it down, you'd have a huge advantage in Challenge 5. This was originally the complete self-destruct override code, and the BLUE component specifically comes from here as part of the meta-puzzle across Challenge 2, Challenge 3, and Challenge 4.
However, I had to scrap these "breadcrumb" clues in order to get challenge 5 ready in time for the event (it got close).

**How you'd know to look here**: The bonus flag hint says "One meter contains embedded message in device description" and points you at OBIS code `0.0.96.1.0.255`. In the Wireshark TCP stream view, the `FLAG:` prefix is visible in the ASCII data.

## Telling the Target Apart from Red Herrings

There are a couple of meters that might look suspicious at first glance:

- **Cold Storage Warehouse** (29.1 kW, 0.7% variance): Second highest power draw, but compressor cycling creates measurable variation. Legitimate industrial load.
- **Ballarat Library** (5.9 kW, 0.1% variance): Very low variance, but only 5.9 kW - not enough for a serious mining operation.

The key is looking at BOTH high power AND low variance together. Only Ballarat Engineering Supplies has >40 kW draw with <0.1% variation. Mining rigs produce a flat line - two readings of 42.036 and 41.995 kW, just 0.041 kW apart.

## Real-World Relevance

Illegal cryptocurrency mining operations have actually been detected through power consumption analysis. In 2021, UK police raided what they thought was a cannabis farm based on power usage patterns, only to find a bitcoin mining operation. Smart meter data analysis is a genuine forensic technique.

The constant high-draw pattern is a real indicator - mining rigs don't sleep, don't take weekends off, and don't vary with temperature. It's one of the most obvious signatures in power data.

## My thoughts

I spent a lot of time generating realistic DLMS/COSEM traffic for the PCAP. The challenge was making it authentic enough that teams could learn something real, while keeping it accessible for people who'd never seen smart meter protocols before. The 42 kW figure is realistic for a small mining operation - about 10-15 high-end ASIC miners.
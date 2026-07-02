# Overall architecture

### Background
The digital gong system was originally designed for Dhamma Pajjota. As there was no pre-existing audio system for an electronic gong, the choice was made to use network cables and small computers (Raspberry Pi) to create a distributed system.
This was followed by an implementation at Dhamma Mahi, which already had an audio system for an electronic gong. What was missing was the automation of the gongs played.

### Hardware
Each installation uses Raspberry Pi devices as the core computing units. The Raspberry Pis communicate with each other via standard network cables (Ethernet).
The master Rasperry Pi has a touchscreen interface allowing servants to:  
- see the coming gong schedules  
- go into manual mode to ring gongs with a screen button (or a real physical button connected to the Raspberry Pi)  
- check that the Internet connection is working  
- see the date of the last schedules received from the web application  

### Software
Version 2.0 of the software, is currently in development and will be available in Q3 2026.
It consists of two components:

- Software running on the Raspberry Pi(s) — written in Python and Python/Qt (graphical interface for the control centre touchscreen).

- Web application for remote database management — written in Python and HTMX, allowing schedules and configurations to be updated from any browser.

### 4. System Architectures
As of version 2.2, all changes are made in the web application and, once checked as valid gong schedules, are sent at 1am (center time) to the center Rasperry Pi(s) for the next day. The web application is hosted on a cloud server, which can be accessed from any browser. 

The system offers two approaches for the architecture on the center. They can be combined depending on the centre's existing infrastructure.

#### 4.1 Centralised approach (Dhamma Mahi)
One central Raspberry Pi connected to a single powerful amplifier. Long audio cables run from the amplifier to speakers installed in the relevant buildings.

Note from experience at Dhamma Mahi: the centralised system is slightly more complex to set up from an audio perspective, as it requires an intermediate sound card between the Raspberry Pi and the amplifier. As the audio signal will get degradation in long audio cables, the audio sent to the amplifier must be of the highest possible quality.

#### 4.2 Distributed approach (Dhamma Pajjota)
One central Raspberry Pi and a series of satellite Raspberry Pis installed in each building. Each satellite Raspberry Pi is connected to a smaller, less powerful local amplifier.

Advantages of the distributed approach:
Easier to expand — no need to reassess amplifier power when adding new buildings or speakers.
Ability to ring specific gongs individually in specific locations, enabling differentiated schedules per building.

Note on hardware constraint: a standard network cable can span a maximum distance of 100 metres (328 feet).
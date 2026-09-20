# Hardware notes

## Laptop prototype

The first milestone intentionally uses equipment already available:

- laptop running Python 3.11 or newer;
- built-in or USB microphone;
- built-in speaker or headphones;
- keyboard key as the temporary push-to-talk control;
- Wi-Fi connection for Telegram polling.

This validates the interaction before committing to electronics or enclosure dimensions.

## Raspberry Pi target

The specific bill of materials remains open until the laptop interaction is tested. A likely prototype includes:

- Raspberry Pi Zero 2 W or another supported Wi-Fi board;
- momentary push button sized for easy operation;
- one multicolor LED or a small set of status LEDs;
- USB or I2S microphone;
- compact speaker and amplifier;
- regulated wall power for early prototypes;
- optional battery only after charging, protection, and thermal risks are reviewed.

## Adapter mapping

| Capability | Laptop MVP | Raspberry Pi target |
|---|---|---|
| Input | Keyboard | GPIO button |
| Status | Console logs | LED and audio cues |
| Recording | Laptop microphone | USB/I2S microphone |
| Playback | OS audio command | ALSA-compatible output |
| Messaging | Telegram polling | Same adapter initially |

## Status vocabulary

| State | Laptop cue | Raspberry Pi target |
|---|---|---|
| Idle | Short ready tone | Soft ready LED |
| Recording | High start tone | Red recording LED |
| Sending | Mid tone | Pulsing status LED |
| Sent | Two ascending tones | Brief green confirmation |
| Cancelled | Two descending tones | Return to ready LED |
| Offline | Repeated low tone | Distinct connectivity pattern |
| Error | Long low tone | Distinct error pattern |

## Physical design constraints

- No exposed conductors, sharp edges, or accessible small fasteners.
- Strain relief on every external cable.
- Speaker volume limited to a child-appropriate level.
- Ventilation and temperature tested under sustained load.
- Controls should communicate state without requiring reading.
- An adult-accessible power/reset action should be difficult to trigger accidentally.

This is a prototype design document, not a product safety certification. An adult should supervise all early testing.

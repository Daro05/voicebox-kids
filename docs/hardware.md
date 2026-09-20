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

The selected first breadboard platform is Raspberry Pi Zero 2 WH with Raspberry Pi
Codec Zero. The Codec Zero provides the microphone, mono speaker driver, two status
LEDs, and a tactile button in the same footprint.

- Raspberry Pi Zero 2 WH;
- Raspberry Pi Codec Zero;
- compact 8 Ω mono speaker;
- regulated wall power for early prototypes;
- optional battery only after charging, protection, and thermal risks are reviewed.

See [BOM.md](BOM.md) for the exact prototype list and official references.

## Adapter mapping

| Capability | Laptop MVP | Raspberry Pi target |
|---|---|---|
| Input | Keyboard | Codec Zero button on GPIO27 |
| Status | Console logs | Codec Zero LEDs on GPIO23/24 plus audio cues |
| Recording | Laptop microphone | Codec Zero MEMS microphone through ALSA |
| Playback | OS audio command | Codec Zero mono speaker output |
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

# Prototype bill of materials

## Selected platform

The first physical prototype targets **Raspberry Pi Zero 2 WH + Raspberry Pi Codec
Zero**. The `WH` variant is preferred because its 40-pin header is already fitted.

This pairing keeps the prototype compact while providing Wi-Fi, a microphone, a mono
speaker driver, two programmable LEDs, and a tactile button through supported Raspberry
Pi hardware.

## Core components

| Component | Prototype choice | Reason |
|---|---|---|
| Computer | Raspberry Pi Zero 2 WH | Compact 65 × 30 mm board, Wi-Fi, 64-bit quad-core CPU, fitted GPIO header |
| Audio/control HAT | Raspberry Pi Codec Zero | Built-in MEMS microphone, 1.2 W mono speaker driver, GPIO27 button, GPIO23/24 LEDs |
| Speaker | 8 Ω mono speaker, rated at least 1.2 W | Matches the Codec Zero speaker output |
| Storage | High-quality 16 GB or larger microSD | Raspberry Pi OS and VoiceBox runtime |
| Power | Official-compatible regulated 5 V micro-USB supply | Stable wall-powered development without battery risk |
| Assembly | Correct standoffs and protected speaker wiring | Prevents board contact and cable strain |

Do not add a battery during the breadboard phase. Charging, protection, heat, enclosure,
and child-access risks need a separate review.

## GPIO and audio mapping

| Function | Codec Zero resource |
|---|---|
| Push-to-talk button | GPIO27 |
| Green status LED | GPIO23 |
| Red status LED | GPIO24 |
| Digital audio | I2S on GPIO18/19/20/21 |
| Audio input | Built-in MEMS microphone through ALSA |
| Audio output | 1.2 W mono speaker terminal |

The built-in tactile button is suitable for software validation, not the final child
interface. A larger protected momentary button should be designed after the breadboard
test.

## Primary references

- [Raspberry Pi Zero 2 W product page](https://www.raspberrypi.com/products/raspberry-pi-zero-2-w/)
- [Raspberry Pi Codec Zero product page](https://www.raspberrypi.com/products/codec-zero/)
- [Official Raspberry Pi audio-board documentation](https://www.raspberrypi.com/documentation/accessories/audio.html)
- [Official Raspberry Pi GPIO documentation](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#gpio-and-the-40-pin-header)

Confirm regional availability before purchasing. Product prices and reseller inventory
are intentionally not hard-coded in this document.

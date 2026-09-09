# Architecture

## Goals

VoiceBox separates the child's interaction model from transport and hardware details. The same core workflow should run first on a laptop and later on a Raspberry Pi, while Telegram can be replaced by another approved provider without rewriting the device behavior.

```mermaid
flowchart TB
    subgraph Providers[Messaging providers]
        TG[Telegram adapter]
        WA[WhatsApp adapter — future]
    end

    subgraph Core[Provider- and hardware-neutral core]
        Contract[MessagingAdapter protocol]
        Controller[Voice-note controller]
        State[State machine]
        AudioContract[Player / recorder protocols]
        ControlContract[Controls protocol]
    end

    subgraph Adapters[Environment adapters]
        LaptopAudio[Laptop audio]
        Keyboard[Keyboard controls]
        PiAudio[Raspberry Pi audio — future]
        GPIO[Button + LED GPIO — future]
    end

    TG --> Contract
    WA -.-> Contract
    Contract --> Controller
    Controller <--> State
    Controller --> AudioContract
    Controller --> ControlContract
    AudioContract --> LaptopAudio
    AudioContract -.-> PiAudio
    ControlContract --> Keyboard
    ControlContract -.-> GPIO
```

## Receive flow

```mermaid
sequenceDiagram
    participant F as Trusted family member
    participant T as Telegram adapter
    participant C as VoiceBox core
    participant P as Local audio player

    F->>T: Send voice note
    T->>T: Verify chat allowlist
    T->>T: Download to local inbox
    T->>C: VoiceNote metadata + path
    C->>C: idle → receiving → playing
    C->>P: Play local file
    P-->>C: Playback complete
    C->>C: playing → idle
```

## Design decisions

- **Ports and adapters:** protocols define messaging, audio, and controls; provider SDKs remain at the edges.
- **Deny by default:** Telegram chat IDs must be explicitly configured before the service starts.
- **Local-first media:** the core receives a local path, so playback does not depend on provider objects.
- **One interaction at a time:** the state machine makes device behavior observable and prevents ambiguous transitions.
- **Secrets outside source:** bot credentials are loaded from an ignored `.env` file or the runtime environment.

## Next implementation slice

Add a queue between receipt and playback so multiple notes are serialized, acknowledge successful playback through the messaging boundary, and enforce a configurable retention policy for downloaded media.

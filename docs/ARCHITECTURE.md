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
    participant Q as Playback queue
    participant P as Local audio player

    F->>T: Send voice note
    T->>T: Verify chat allowlist
    T->>T: Download to local inbox
    T->>C: VoiceNote metadata + path
    C->>Q: Enqueue note
    Q->>C: Next note in arrival order
    C->>C: idle → receiving → playing
    C->>P: Play local file
    P-->>C: Playback complete
    C->>C: playing → idle
    C->>T: Send playback acknowledgement
    T-->>F: Delivery status
```

## Send flow

```mermaid
sequenceDiagram
    participant C as Child interaction
    participant V as VoiceBox core
    participant R as FFmpeg recorder
    participant T as Telegram adapter
    participant F as Trusted family member

    C->>V: Press Enter
    V->>V: idle → recording
    V->>R: Start microphone capture
    C->>V: Press Enter again
    R-->>V: Local Ogg/Opus recording
    V->>V: recording → sending
    V->>T: Send voice note to approved destination
    T-->>F: Deliver voice note
    V->>V: Delete delivered local copy
    V->>V: sending → idle
```

## Design decisions

- **Ports and adapters:** protocols define messaging, audio, and controls; provider SDKs remain at the edges.
- **Deny by default:** Telegram chat IDs must be explicitly configured before the service starts.
- **Local-first media:** the core receives a local path, so playback does not depend on provider objects.
- **One interaction at a time:** the state machine makes device behavior observable and prevents ambiguous transitions.
- **Serialized playback:** a queue prevents overlapping notes and preserves arrival order.
- **Serialized interaction:** a shared lock prevents playback and microphone capture from overlapping.
- **Deterministic routing:** outbound notes go only to an explicitly approved chat.
- **Bounded recovery:** local playback is retried once before the family receives a failure status.
- **Private outbound media:** recordings use Ogg/Opus and are deleted after confirmed delivery.
- **Data minimization:** expired voice-note files are deleted on startup using a configurable policy.
- **Secrets outside source:** bot credentials are loaded from an ignored `.env` file or the runtime environment.

## Next implementation slice

Validate microphone permissions and the two-way interaction with adults, then add short
audio cues and a maximum recording duration before moving controls to Raspberry Pi.

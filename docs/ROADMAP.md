# Roadmap

## Phase 1 — Laptop MVP

- [x] Create a typed Python package and local CLI.
- [x] Define messaging, audio, recording, and control boundaries.
- [x] Receive allowlisted Telegram voice notes and download them locally.
- [x] Play downloaded notes through a detected local audio command.
- [x] Add guided bot verification, chat discovery, and environment diagnostics.
- [ ] Add queued playback, acknowledgements, and media retention.
- [ ] Add a laptop microphone recorder and send path.

## Phase 2 — Interaction model

- [ ] Prototype press/hold/release behavior with keyboard input.
- [ ] Define LED and audio cues for idle, recording, sending, unread, and error states.
- [ ] Test the flow with adults acting as both child and family member.
- [ ] Add timeouts, cancellation, retry, and offline behavior.
- [ ] Document child-safety, privacy, consent, and data-deletion decisions.

## Phase 3 — Raspberry Pi

- [ ] Select a Raspberry Pi board and supported OS image.
- [ ] Implement GPIO button and LED adapters.
- [ ] Validate microphone, amplifier, speaker, and power components.
- [ ] Package the service for automatic startup and safe shutdown.
- [ ] Add connectivity and health diagnostics without adding a screen.

## Phase 4 — Physical enclosure

- [ ] Build a breadboard prototype and record wiring revisions.
- [ ] Design a durable, child-appropriate enclosure with protected fasteners.
- [ ] Plan speaker grille, microphone port, button travel, ventilation, and charging access.
- [ ] Produce and test a 3D-printed enclosure.
- [ ] Review thermal, electrical, battery, and small-parts safety.

## Phase 5 — Portfolio release

- [ ] Record a concise product demo and architecture walkthrough.
- [ ] Publish build photos, bill of materials, diagrams, and engineering tradeoffs.
- [ ] Add automated checks, release notes, and a reproducible setup guide.
- [ ] Document evaluation results and known limitations.
- [ ] Tag a stable `v1.0.0` portfolio release.

## Phase 6 — Optional AI enhancements

- [ ] On-device or privacy-aware transcription for adult-accessible history.
- [ ] Family-name intent routing with an explicit confirmation cue.
- [ ] Noise suppression and voice-activity detection.
- [ ] Safety moderation designed around transparent, adult-controlled policies.
- [ ] Multilingual prompts without storing a child's voice for model training.

AI features are optional and follow a reliable, understandable messaging experience; none should make the device an emergency service or autonomous caregiver.

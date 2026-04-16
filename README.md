# Interpolbility
### AI Scope-Aware Write Protection with Adaptive User Education

---

AI is adaptive. In the wrong hands it becomes a threat moving faster than any human can react to. The same capability that makes it powerful enough to teach and protect is powerful enough to destroy — if nobody is watching the door.

Experience level does not determine risk. A CEO and a curious teenager face the same exposure if neither understands what their AI agent is doing or where it's writing. The only way to close that gap is to build protection that educates while it guards — creating a security culture from the ground up, one user at a time. That is the trust Anthropic is building toward. Interpolbility is one door in that house.

---

## What It Does

Interpolbility is a scope-aware write protection layer for AI agent deployments. It intercepts every write attempt an agent makes, checks it against defined boundaries, scans content for credential exposure, and presents the user with a clear, plain-English response menu before anything reaches the filesystem.

It does not just block. It explains. Every action comes with a WHAT, WHERE, and WHY so the user understands what happened and why it matters — building security awareness through interaction rather than documentation nobody reads.

---

## The Problem It Solves

AI agents are being given filesystem access, network access, and credential stores as part of normal workflows. The frameworks building these systems have no native write protection. The attack chain is specific:

1. Malicious code enters through a VSCode extension, compromised GitHub repo, or tampered agent instruction
2. The agent processes it as legitimate context and propagates it downstream
3. Without a protection layer, it reaches SSH configs, credential stores, private keys, and system directories
4. The attacker has remote access, file transfer capability, and persistence

Nobody is watching that door. Interpolbility watches it.

---

## How It Works

### Layer 1 — Startup and Baseline
- Onboards the user with a single experience level question
- Anchors the agent to a defined safe home directory every session
- Builds a SHA-256 hash baseline of all files in allowed directories
- Creates a persistent activity log
- Explains every action using WHAT / WHERE / WHY

### Layer 2 — Write Intercept
Two-stage filter on every write attempt:

**Stage 1 — Destination check**
Verifies the write destination against config-defined allowed and protected directories. Absolute path resolution prevents directory traversal bypass. Protected paths are blocked immediately.

**Stage 2 — Content check**
Scans file content for credential patterns — API keys, tokens, private key headers, hardcoded passwords, bearer tokens, AWS credentials. Suspicious content triggers an alert and holds the operation.

**YOLO Mode**
For advanced users and automated pipelines. Operations proceed without user input but nothing is silent — every action is logged and queued. On next startup the user receives a full summary and chooses whether to save it as a named alerts file.

### Layer 3 — Response Tools
When an alert fires, the user gets three investigation tools:

- **Diff** — color-coded side-by-side comparison of current file vs what the agent was trying to write. Green for additions, red for removals.
- **Hash Check** — SHA-256 integrity verification against the startup baseline. Mismatch triggers an exploration flow showing both hashes, both timestamps, and recommended actions.
- **Log Review** — filtered session activity for the specific file that triggered the alert. Option to export the full session log.

### Layer 4 — Adaptive User Profiling
Interpolbility builds a behavioral profile over time:

- **Explanation engagement** — tracks full, partial, and skipped explanation requests
- **Response time** — how long between alert and decision
- **Investigation rate** — how often the user uses Diff, Hash, or Log before deciding
- **Fix-it pattern detection** — identifies when a user is resolving alerts without engaging, and nudges toward understanding without withholding help
- **Progression detection** — when behavioral metrics suggest the user has grown, Interpolbility tells them what it observed and asks if they agree before updating their profile
- **Growth moments** — logged history of every profile progression, confirmed or declined

AI should never dumb users down. It should build them up at a rate no book or video can match — through interaction, through doing, through understanding earned rather than delivered.

---

## Multi-User Support

Interpolbility supports multiple named profiles on a single installation. Different users get different experience levels, different explanation settings, and different alert histories. The protection layer is identical for everyone. The communication layer adapts to each person.

---

## Configuration

All behavior is driven by `config.json`:

```json
{
  "allowed_directories": ["D:/Interpolbility"],
  "protected_directories": ["C:/Users", "C:/Windows", "C:/Program Files"],
  "protected_files": [".ssh/known_hosts", ".ssh/authorized_keys", ".env"],
  "protected_extensions": [".pem", ".key", ".ppk", ".pfx"],
  "yolo_mode": false
}
```

Set `yolo_mode` to `true` to enable BYPASS mode. Everything else is configurable without touching code.

---

## Project Structure

```
D:/Interpolbility/
├── config.json              # Rules, allowed dirs, user profile settings
├── startup.py               # Layer 1 — onboarding, baseline, home directory
├── write_protect.py         # Layer 2 — write intercept, destination and content checks
├── layer3.py                # Layer 3 — diff, hash check, log review
├── layer4.py                # Layer 4 — adaptive profiling, progression, fix-it detection
├── baseline_hashes.json     # SHA-256 fingerprints of allowed files at startup
├── user_profile.json        # Behavioral metrics and progression history
└── logs/
    ├── interpolbility.log   # Full session activity log
    ├── alerts.json          # Permanent alert history
    └── pending_holds.json   # YOLO mode queue — cleared after user review
```

---

## Research Extensions

Interpolbility is a starting point. The open questions it raises:

- How should allowed scope be defined dynamically as agent tasks evolve across a session?
- Can behavioral analysis detect anomalous write patterns before destination or content checks trigger?
- What does inter-agent integrity verification look like when Interpolbility itself is one node in a larger multi-agent chain?
- How does the education layer scale for enterprise deployments with hundreds of users at different technical levels?
- Can the adaptive profiling system detect not just experience level but specific knowledge gaps — flagging areas where a user consistently disengages?

---

## Why This Was Built

I built a 47-agent orchestration system in a classified environment and watched the trust boundary problem emerge in real time. I found a PKI authentication gap because something broke while I was deploying it. I identified credential exposure in AI memory files because I was thinking like an attacker while building like a developer.

Interpolbility exists because AI security is too important to leave only to people who came up through academia. The people who break systems and the people who build them need to be in the same room. This project is my attempt to put them there.

---

## Enterprise Path

The current implementation is a local research prototype. Multi-user support uses local profile selection - fast, simple, no dependencies. For enterprise deployment the architecture would expand to:

- **Authenticated accounts** - 2FA verified identity per user replacing local profile selection
- **Role-based directory scope** - each user's allowed and protected directories tied to their verified role, not a shared config
- **Central policy management** - one admin controls scope rules across all users and machines from a single location
- **Audit logs tied to verified identity** - every write attempt, block, and user decision attributed to a confirmed identity, not a self-declared name
- **Remote policy enforcement** - scope rules pushed from a central server, not editable locally by the user

The local version demonstrates the concept. The enterprise version is where this protects organizations at scale.

---

## Status

Active development. Layers 1 through 4 complete. Multi-user support complete.

**Language:** Python 3.10+
**Dependencies:** None beyond Python standard library
**Platform:** Windows / Linux / macOS

---

*Built by Rich*


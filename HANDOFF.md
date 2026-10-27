# Start here

This folder is the starting point for the astrology app. Nothing is built yet.
It holds the project rules (CLAUDE.md), the full plan, the phase prompts and a
starter rule file for the Discepolo finder.

## Moving to the other account

1. Unzip this folder somewhere permanent, for example `~/Projects/astrology-app`.
2. Create a new private GitHub repo under your own GitHub account
   (for example `astrology-app`). Keep it private: it will hold your rules.
3. Open the Claude desktop app signed into the Max account. Start a Claude Code
   session on this folder.
4. First message to Claude:

   > Read HANDOFF.md, CLAUDE.md and everything in docs/. Initialize git,
   > connect it to my private GitHub repo <paste repo URL>, and make the first
   > commit. Then tell me in a few lines what you understand the project to be
   > and list any questions you have before Phase 1. Do not write app code yet.

5. Switch the model to Fable 5.1, turn on plan mode, and paste the Phase 1
   prompt from docs/phase-prompts.md.

## Before Phase 1, gather

- [ ] 5 golden charts from astro.com (see golden/README.md for which ones)
- [ ] Your answers to the open questions in docs/reference.md
- [ ] Your Discepolo books, to check the "confirm" rows in rules/rules.yaml

## Coming back to the original account later

Clone the GitHub repo (or open the same folder) in Claude Code signed into the
other account. CLAUDE.md carries the project rules, so nothing else needs to move.

## Folder map

- CLAUDE.md: project rules Claude rereads every session
- docs/phase-prompts.md: one prompt per build phase, in order
- docs/reference.md: setup, data sources, licensing, finder method, traps,
  verification checklist, open questions, sources
- rules/rules.yaml: starter Discepolo scoring rules (edit freely)
- golden/: where your astro.com test charts go

# Next-session handoff

This page is a quick entry point for a new Codex session. The authoritative live
tracker is [`TASKS.md`](TASKS.md); read it before changing the project.

Repository: `F:\Coding Projects\Spider-Man-Web-of-Shadows-DS-Modding`  
Branch: `main`  
Published release: `ea16747` — combat feedback, Rebound juggle tuning and the
expanded combined TASM roadmap  
Stable ROM: `build/Spider-Man-WoS-modded.nds`  
Default recipe: `reference/gameplay_profile.json`

The user has confirmed Web Vault in normal play. The current build also contains
the closer, higher Rebound launch, actual DEALT/TAKEN loss readouts and a numeric
native combo-meter value. The remaining player checks are readability in busy
fights, ordinary incoming hits, Rebound pursuit near walls/ceilings and unusual
enemies or bosses. The next approved development move is Sling Strike, replacing
Mid-Air Snare at 600 XP / event 324 / bit 15.

Begin by reading `AGENTS.md`, `TASKS.md` and `COMBAT_FEEDBACK.md`, then verify the
working tree and recent commit. Ask what the player observed since the last release
before treating any pending check as complete. Use a fresh save copy for isolated
Sling Strike research, preserve the free Snap Sweep and shared traversal, and keep
the stable ROM filename. Existing seven-slot implementation is the safe starting
path; the combined TASM 1/2 kit and ten-plus skill ideas in
`TASM_EXPANDED_ROADMAP.md` are design work until menu, ownership and save support
are proven.

The ROM, extracted assets, active overlays, builds and saves are private and
ignored by Git. GitHub carries source, tools, tests and documentation only. The
player workflow remains `Play Spider-Man.cmd` -> Continue -> play -> save in-game
-> close DeSmuME.

Suggested opening prompt:

> Continue the Spider-Man Web of Shadows DS mod from `F:\Coding Projects\Spider-Man-Web-of-Shadows-DS-Modding`. Read `AGENTS.md`, `docs/TASKS.md` and `docs/COMBAT_FEEDBACK.md`. Confirm the current release and open player checks, then continue with Sling Strike only after accounting for any new player feedback.

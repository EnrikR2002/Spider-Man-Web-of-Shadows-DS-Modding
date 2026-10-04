# Codex project instructions

We are reverse-engineering the Nintendo DS version of Spider-Man: Web of Shadows (USA, game code CS5E) for private modding/research.

Priorities:
1. Never overwrite the original ROM. Read it from `original/`; write builds to `build/`.
2. Keep all tools deterministic and scriptable from Windows PowerShell.
3. Prefer Python standard library for archive/ROM tooling unless a dependency clearly saves substantial work.
4. Every parser/repacker needs round-trip tests before it is trusted.
5. Unknown binary fields must be documented as unknown rather than guessed.
6. Preserve unknown bytes wherever possible.
7. Keep `docs/FORMAT_NOTES.md` updated with every confirmed structure, hypothesis, and test result.
8. Keep a `docs/MODDABILITY_MATRIX.md` with each format, what it likely controls, parsing status, editing status, and confidence.
9. Do not distribute the ROM or extracted copyrighted assets. If public patching is added later, produce patches/tools only.
10. Favor minimal empirical experiments: change one field/asset, rebuild, boot, observe, revert/iterate.

Confirmed facts are in `docs/ANALYSIS.md` and `reference/glob_manifest.csv`.

## Session continuity and tasks

- Read `docs/TASKS.md` at the start of each session before choosing work.
- Keep it as the project task/handoff source of truth: current work, last completed
  release, ordered next steps, unresolved checks and links to detailed evidence.
- Update it after a milestone and before ending a session. Distinguish implemented,
  agent-tested and player-confirmed behavior; never mark an untested move complete.
- Preserve queued work across sessions. Record a concrete next action when stopping
  during research, along with candidate/evidence paths needed to resume.

## Accepted user workflow (2026-10-04)

- Develop one suit at a time. TASM 1 is active; retain the selected backlog in
  `docs/SUIT_ROADMAP.json`. Prototype through the red form while investigating
  a separate third slot. Describe proposals separately from implemented behavior.
- The agent handles save management for every feature release. Use the actual
  configured Battery directory in ignored `work/playtest.json`. Preserve progress,
  verify the DSV wrapper and snapshot bytes, and keep DeSmuME closed during mutation.
- Test isolated candidates, merge all accepted overlays, then publish with
  `python tools/playtest.py build`. Keep `build/Spider-Man-WoS-modded.nds` stable;
  retain prior ROM/checkpoints. Do not give the player renamed everyday builds.
- Player flow: `Play Spider-Man.cmd` -> Continue -> play -> save in-game -> close.
  The agent creates/restores named battery checkpoints when useful or requested.
  Do not ask the player to manage filenames or run backup/build commands.
- Use battery copies for isolated emulator tests; never write research results
  into the real save or replay an old save state over a changed ROM.

## Upgrade progression constraint (2026-10-04)

Latest user steering supersedes the one-for-one limits below: combine the TASM 1
and TASM 2 combat identity into one TASM kit; ideate 10+ skills and flexible
prices/power tiers. The original seven slots are a starting implementation path,
not a design ceiling. Expanded progression/menu/save support remains research;
do not silently grant abilities or remove shared traversal requirements.
Web Vault is player-confirmed. Its brief air window should gain deliberate paid
pursuit/control extensions later. Rebound now needs lower horizontal and higher
vertical enemy knockback with unchanged damage. Add real dealt/taken damage
feedback with per-hit and running totals, plus a simple numeric combo HUD that
shows gains below 30. Never display inferred attack strength as actual HP damage.

- User confirmed Snap Sweep works and may remain the free base opener.
- Future TASM moves must replace existing purchased Red-tab skills, with new
  names, comparable power/role and purchase gating. Do not grant them at game start.
- Preserve each replaced slot's native cost, progression gates and purchase flag;
  an existing purchase carries over as ownership of its replacement. Keep shared
  Both Suits upgrades and traversal/progression functions intact.
- The user approved the full replacement plan. `docs/TASM1_UPGRADE_PLAN.md` /
  `.json` describe approved targets, not already implemented gameplay. Implement
  incrementally, retaining purchase gates and measuring balance against originals.
- Snap Sweep's base binding borrows GroundAttack15 assets. Editing those assets
  globally can leak paid behavior into the opener. Preserve the base action and
  modify purchased action routes separately, checking locked and purchased cases.
- Before expanding the kit, document original red/black combat identity and
  investigate the lower-right combo meter, including Snap Sweep's contribution.
  The user authorizes ambitious mechanics and custom animations where feasible.

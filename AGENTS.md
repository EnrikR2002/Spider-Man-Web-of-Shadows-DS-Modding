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

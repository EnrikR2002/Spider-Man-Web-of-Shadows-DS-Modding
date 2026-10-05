# Small instruction clarity pass

2026-10-04. Published to the stable launcher after isolated candidate checks.
This adds sixteen bounded English/American text edits to `tasm-combat-flow`.
The same ARM9, purchase records, accepted cosmetics, red marker and combat HUD
remain in use. No ability, price, damage or save field is changed.

- Shared moves put the input first and the role on a separate line: uppercut,
  rolling kick, aerial stomp, sustained dodge, recovery and enemy kick-off.
- Spider Dance now says to wait between attacks, clarifying the native combo's
  pause input. The native timing window remains unmapped; no buffering is added.
- Web Swing, Web Hang, Wall Run and throwing instructions use shorter lines
  with the original button glyphs and surface/context requirements.
- Map/SELECT/zoom, saving and practice tips are shorter. The training hint
  explains the already implemented target refill and names the pause-menu exit.

Text slots: 164,167,170,173,179,182,194,230,233,239,242,403,404,407,417,421.
Only `English.strings` and `American.strings` change. The generator starts from
the verified current overlays, validates their recipe, preserves the Huffman tree,
offset table, allocation, unedited slots and each edited slot's remaining bytes,
then decodes all 1,049 slots in each language. Edits reject unsupported glyphs and
overflow instead of expanding the archive. Reapplying the pass is byte-identical.

Private captures at `build/boot-tests/Clarity-67472ad1/` show Core traversal/throw
instructions, Spider Dance, Quick Recovery and the training hint. Initial
`Clarity-002a1447/shared-menu` captures verify the other shared descriptions;
only Quick Recovery wording subsequently changed to avoid an isolated button
glyph wrapping onto its own line. Tutorial tips are codec/bounds verified;
their individual story-triggered popups were not all visited.

The existing four text/palette tests and the complete 96-test suite pass; the
full run is recorded in ignored `work/qol-clarity/tests.log`.
The rebuilt ROM verifies all 3,733 resources and matches the tested candidate.
ARM9 is byte-identical to the combat-flow release:
`b43630d4f0bf0ea3530a6330f7c80482d6ba1f70ba194a447eb93e8a738d77ea`.
ROM SHA256:
`67472ad12cc6be60134588a992945eaba505eacc85a741f48684ce3a5f737520`.

DeSmuME was closed during publication. Checkpoint `before-clarity` and the
before-build snapshot retain the exact latest 634-byte DSV, v0/512 payload:
`a22cdc22490db27af413520d4a7aa09e7decdec3ab5d41636c575bc6bd19ce46`.
Prior combat-flow ROM `c700f3b5` is retained in `build/releases/`.

Generate another isolated candidate with `python tools/qol_clarity.py`.
The guarded current overlays must already be available privately. For layout
replays, pass the appropriate `reference/combat-inputs/clarity-*.json` script
and a read-only battery copy to `tools/emulator_smoke.py`. Publish accepted
overlays through `python tools/playtest.py build`; keep the everyday filename.

Larger retry-menu routing, HUD settings, camera changes and expanded purchases
remain queued research. This pass does not implement the next paid move.

# Compact combat HUD and readability release

Historical initial release. Current player-feedback fixes and limits: `COMBAT_FLOW.md`.

2026-10-04. Replaces the large panels described in `COMBAT_FEEDBACK.md`.
Current composed recipe: `tasm-sling-strike`; stable filename remains
`build/Spider-Man-WoS-modded.nds`. No damage values are rendered.

## Player-facing behavior

- The native lower-right meter is preserved. An 8-pixel stock-font number is
  centered at X239/Y160 above it, without a COMBO label or idle zero.
- It shows the existing composite meter value (75 Ã— tier + integer gauge),
  including Snap's 12 below the native bar threshold. It is not a hit count.
  Positive common enemy HP loss enables it for 30 active HUD updates, roughly
  one second at the observed update rate; misses and idle decay do not keep it up.
- Wounded living common enemies get a 24Ã—4-pixel bar above their bounds: black
  border, red remaining health and gray empty space. Full/dead/offscreen enemies
  are hidden. Up to eight fresh updating enemies can be represented.
- Stock font0, FontPaletteSprite colors and the BG2 bitmap canvas are reused.
  No extra extracted artwork is needed. Native menus/messages remain readable.
- MissionMiniMapIcon.pal is exactly the original red palette again. Unknown
  palette entries, compressed pixels and DAT bytes are unchanged.
- Rebound/Vault inputs and four native prerequisite descriptions are clearer in
  English/American. Other upgrades retain their native names, prices and gates.
- Test Upgrades restores the dummy to its native maximum HP after each defeat,
  replacing its previous 40-Q12 refill. Regular enemies retain their health rules.

## Engine implementation and bounds

`tools/combat_hud.s/.hex/.py` reuse the guarded SDK extension from the previous
feedback release: destination 0214F420, 16 KiB heap reservation, own code/source
size 3600 hexadecimal. Native font lifecycle cleanup remains paired to HUDText
construction/destruction. The renderer removes only its BG2 canvas tile IDs
200..2FF hexadecimal, retaining other tilemap entries.

The new actor observer at 02073A68 snapshots the known common enemy HP setter
ABI (vtable+150 = 02049304), positive HP below maximum, native position and
half-height. Its eight 32-byte records at own state+400 contain actor identity,
HUD tick, HP/max, XYZ and half-height. Rendering never dereferences a retained
actor pointer. Records older than two HUD updates expire; room entry clears them.
Death/healing can leave at most this short snapshot delay before disappearance.

Perspective projection uses the native SideScrollCamera/PerspectiveView,
rotation matrix, eye, FOV and aspect. Camera type mismatches skip bars. Native
fixed-point transform/divide helpers remain in use. See FORMAT_NOTES for offsets.
Bar fill is floor(22Ã—HP/max), bounded by valid HP and at most 22 iterations.

Both original common health hooks still retain capped *private telemetry* for
balance tests. No strength is presented as actual damage. This is not an
attacker-credit system: common enemy/environmental HP loss can enable the combo
number. Specialized boss/immune health paths are not comprehensively audited.
Paused gameplay freezes the native HUD and its current snapshot normally.

HUD-only ARM9 SHA256:
`4061f7cbcce487b72dc3f06d2f079f2060759eb3147448743e3de5fd3eeed62d`.
Own HUD code SHA256:
`40cd7401bb0a89c947084a60b7c1f0077839f6ca9ab9721797785d3700d366ac`.
Final Sling composition hashes and evidence are in `TASM1_SLING_STRIKE.md`.

## Verification

92 tests pass, including executable edit/revert, SDK relocation, all-file byte
preservation, every native purchase record, exact own-code hashes and text slot
preservation. All 3,733 Glob resources are verified during rebuild.

Private replay evidence: `CompactHud-5fc6bfd3/compact-snap` first establishes
tiny number 12, bar alignment and no overlap. `SlingStrike-0d7a12d2/final-hud-snap`
checks repeated full dummy refills, idle number clearing and native pause text.
`sling-purchase-save` under `SlingStrike-8897a7aa` shows Save Complete and the red
mission marker. Final-ROM `SlingStrike-92f4aa29/balanced-hud-snap` confirms the
tiny12/bar at frame3110, repeated full refills, hidden numeral while idle at3510,
and native pause text at3670. Save reload and paired damage-budget replays use
the same final composition; observations are in `work/hud-sling/final-evidence.json`.

Player checks remain open for real encounter density, bars on unusual enemies,
camera edges, ceilings, bosses and long play. A normal-room traversal replay
resumed the real-save copy and crossed rooms without stale HUD entries, but did
not land an ordinary AI-enemy hit; do not call that a normal-fight coverage test.

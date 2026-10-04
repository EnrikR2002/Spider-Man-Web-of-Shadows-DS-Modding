# Web Vault — purchased Red-suit release

2026-10-04. Web Vault replaces **Web Launch at 200 XP**, native event 323 / bit 14.
Use **A to grapple, then Up** (configured keyboard: **W, then Up**). Existing
Web Launch ownership carries over. Rebound, Snap Sweep, cosmetics and QoL remain.
Sling Strike is next; player acceptance for these two paid replacements is pending.

## Implemented behavior

The native grapple launch receives a ten-unit forward player approach and a short
physical hop when its launch event runs. Spider-Man becomes vulnerable in the
ordinary airborne state, can use normal aerial attacks, and lands normally.
The measured idle-input hop rises 11.632 game units above the arena floor.
The enemy's original launch response, damage route and resistance data are retained.
No extra hit is authored. Shared purchases, other Red purchases and traversal
requirements retain their native tables and input gates.

## Bounded implementation

- Native action **51**, controller state **40**, resource
  `spd_GrapplePullBack` (GMB 3359). Its nine-sample GMB channel-zero horizontal
  words become `(0,0,0,8192,24576,40960,40960,40960,40960)` Q12. Vertical root,
  duration, non-root channels and the native GAB event-8 marker at time 5 stay exact.
- The 37-joint SCA retains its 612-byte frame stride and every unknown byte.
  Only independent Chest rotations at frames 3/4/5 change by 4/9/14 degrees.
- ARM9 **0x020C9268..0x020C927B**, five instructions in the state-40 launch
  event case, call native physical hop helper **0x020BF164** with the controller
  pointer. Then native reaction **37** and strength **0xC00** are stored through
  the unchanged common stores at **0x020C925C**, before the original target dispatch.
  No callback table, input selector, purchase query, collision helper, target
  response table, native jump command or common damage/credit handler is changed.
- Rebound's two accepted kind-32 horizontal impulse edits remain. Text slots
  186/187/188 change together and retain the original D-pad glyph. Both English
  and American overlays compose with Rebound and all earlier text/QoL edits.

Earlier root-only vertical experiments did not lift Spider-Man. Entry/callback
hop experiments interrupted the launch and were rejected. The accepted hook runs
only inside the native launch event's paid case after a grapple has a target.
This release includes executable edits; earlier Rebound-only statements about
changing data alone describe that historical release.

## Verification and private replay evidence

Test seed: read-only copy of the current 634-byte DSV, SHA256
`985c616b69a1ad03de6aeb26d0715f6d199894938eaa9ba80a455b04703a2622`.
It already owns Web Kick and Web Launch, has 109 XP and resumes in the early
Residential save room. The real save is unchanged before and after publication.
Inputs are checked in under `reference/combat-inputs/web-vault-*.json`; RAM,
screenshots, isolated native saves and ROMs remain private under `build/boot-tests/`.

Accepted candidate evidence: `WebVault-bd94b6f9/`:

| Replay | Observed result |
|---|---|
| `vault-owned` | Original ownership preserved; action 51/state 40 enters, X120 ->130; short hop, landing and idle return |
| `vault-refund` | Native refund 109 ->309 XP clears bit 14; same input produces no action 51, no approach and no hop; Rebound remains owned |
| `vault-repurchase-save` | Native purchase 309 ->109 XP restores only bit 14; game displays Save Complete; isolated 512-byte native payload captured |
| `vault-save-reload` | Fresh boot of captured native save retains purchase and XP; entire player trace matches `vault-owned` |
| `vault-left-facing` | X162.901 ->152.901, same short hop, normal landing; movement faces the target |
| `vault-miss` | Wrong-facing missed grapple earns no credit and creates no vault |
| `vault-air-follow` | Separate Y input enters native aerial actions 1/2/3, then ordinary fall/landing; extra credit comes from these explicit attacks |
| `rebound-regression` | Rebound still follows native actions 49/50, retreats X120 ->115, stays grounded and retains native credit |
| `vault-alternate-form` | Compared with `vault-alternate-native`: action/resource, facing and X/Y traces match across 189 frames; no Red Web Vault is granted to the alternate form |

Paired unchanged-Web-Launch control:
`Spider-Man-WoS-modded-be5fedb6/vault-native-paired`, same seed/input.
Across all **289 traced frames**, gauge, grace, decay, tier and active fields match
exactly. The transient credit-marker byte clears earlier when Web Vault transitions
to falling; it is not claimed identical. Enemy animation and X/Y positions match
exactly at frames 3202, 3206, 3220 and 3250, including launch, ascent and descent.
For example frame 3220 is Q12 `(565820,102139)` in both runs. Native response
stores/dispatch and all 21 purchase rows are byte-identical. Raw enemy HP loss
is not independently decoded; no invented numeric damage claim is made.

Full suite: **81 tests pass** (77.897 seconds). New checks bound root changes,
independent pose edits, merged text slots, exact ARM9 differences/branch targets,
all purchase tables and unchanged shared/input routes. Stable verification rereads
all **3,733** resources and exactly matches the tested candidate.

## Publication and remaining checks

Stable ROM: `build/Spider-Man-WoS-modded.nds` (11 changed Glob assets), SHA256
`bd94b6f9f8a8a1d8566aca4da284ba4c150ac675cd62ce6afb405a6e9be8c092`.
Known accepted ARM9 SHA256:
`6e563225538658c6c8437ede1886037132adc5ed865693727ef60457072529bf`.
`tools/tasm_web_vault.py` creates the deterministic composed candidate;
`reference/gameplay_profile.json` pins its seven required overlay hashes.
`mod.py build/verify` and the read-only probes recognize this exact profile.

Published with `tools/playtest.py build`. Named save checkpoint `before-web-vault`
and the previous Rebound ROM in `build/releases/be5fedb6.../` are retained. The
unchanged real DSV remains associated with the same everyday ROM filename.
Player flow: **Play Spider-Man.cmd -> Continue -> play -> save in-game -> close**.

Native DeSmuME play, low ceilings, walls, bosses, interruptions and long sessions
remain broader acceptance checks in TASKS.md. Native collision/gravity and resistance
are preserved, but these edge cases have not all been replayed. No independent
third suit slot or later paid replacement is included in this release.

# Current work, backend queue and handoff

Updated 2026-10-05 (America/Edmonton). Read this and AGENTS at startup; then only
the section relevant to the task. Shipped history: [CHANGES](CHANGES.md); ROM
knowledge: [TECHNICAL](TECHNICAL.md); combat design: [TASM_ROADMAP](TASM_ROADMAP.md).

## Current work

**v0.1.1 published:** seven Both Suits prices total 725 XP (was 3,050), retaining
discounted Red rows. Stable `bcc6974a`, profile tasm-v0.1.1; 17 overlays/3,736
resources. Each shared buy/refund plus native save/reload passes, with v0.1.0
price control and visible boot/pause/Options number. Real 634-byte DSV preserved
exactly; old/new ROM/compositions retained. All 141 source tests pass.
Latest steering: FUN COMES FIRST; the 26-skill catalog was rejected as overwhelming.
New design: one complete bounce/zip/sling/web-burst kit, responsive attacks/escapes,
generous isolated prototype, progression and balancing later. This is a design
reset; no new combat prototype has shipped. Snap Sweep and
original Vault are player-confirmed. User reports decent duel tools but severe
crowd hitstun/insufficient mobility. Earlier scene/motion acceptance checks remain
open; no redesigned mechanic has shipped.

## Ordered next development

1. **Fun prototype in one crowd room:** copy a reproducible three-enemy encounter;
   trace where native attacks/hitstun trap input. Start with current Sling approach,
   native kick-off/vault, grapple/pull and dodge/recovery research. Keep the full
   proposed kit enabled only in disposable research saves/RAM.
2. Connect **bounce + zip + immediate escape**, with generous targeting, air
   steering and input buffers. Cross the group, choose a different enemy and leave
   after one contact. Add web burst and directional enemy sling/collisions to that
   same loop. Test target loss, both facing directions and blocked landings.
3. Player playtest with a tiny control card/quick restart; iterate until movement
   and crowd improvisation are fun. Then select a few worthwhile upgrades and
   investigate only the shop/ownership migration they require. The 26-item catalog
   and additional-shop-row-first ordering are superseded; balance can wait.
4. Gather player feedback on current motion and normal/dense encounters, incoming
   hits, walls/ceilings, specialized enemies/bosses, HUD crowding and long play.
5. Isolate actual DeSmuME JIT/preload/renderer settings for reported hitches, then
  optional 2x visual acceptance. Idle benchmarks are not proof of a hitch fix.

## Backend ideas retained

Independent shop rows/ownership/refund/save migration; third suit selector;
native HUD/accessibility settings; training timing/reset/quick retry; camera
tracking; enemy windups/fair anti-loop AI; room/encounter/BSP/OBJ editing; same-size
texture work, models/rigs and SDAT sound tools. Selected Ben Reilly/2099/Kaine/
Raimi/symbiote backlog is in reference/suit_roadmap.json, after the combined TASM
kit. Shared progression/traversal remain intact. Research/ideas are not releases.

## Evidence and safe resumption

- Current price qualification build/version-0.1.1 and work/shared-economy;
  replay prefix build/boot-tests/Versioned-bcc6974a. Source saves are private copies.
- Prior version qualification `build/version-0.1.0/`; boot/options/purchase replays under
  `build/boot-tests/Versioned-e1b66ebd/`; copied-save/source/evidence/logs under
  `work/version-research/`; publication.json pins ROM/save/checkpoint/compositions.
  Release registry reference/releases.json. Never restore fixtures over real progress.
- Prior animation proof `work/animation-research/anime-evidence.json`,
  candidate `build/oscorp-anime/`, regeneration `build/oscorp-anime-regenerated/`,
  replays `build/boot-tests/OscorpAuthored-4d36970e/`.
- Native research starting points `work/rush/{research.py,tables.txt,probe.py}`;
  combat inputs `reference/combat-inputs/`; grapple/control mapping in TECHNICAL.
  Bit17 repeat fixture `work/animation-research/scissor-input.json`; four repeats
  were one observation, not a universal cap. m6 uses G11/16/17; they are not spares.
- Real Battery path: work/playtest.json. Re-read latest save while DeSmuME is
  closed before publication/checkpoints; verify wrapper/snapshot bytes. Preserve
  prior ROM/active recipe/overlays, stable filename and user's current progress.
  Player only launches/Continues/plays/saves/closes. Agent owns other operations.

No new Markdown files. Use the six fixed roles; append technical evidence/change
entries in their owner and keep this handoff under 900 words. Archives are read
through tools/doc_archive.py in bounded sections. Cache files remain ignored;
prior deletion was rejected by automatic approval review.

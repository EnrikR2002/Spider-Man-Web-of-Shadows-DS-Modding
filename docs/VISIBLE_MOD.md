# One reversible visible mod: green Spider-Man

Verified in gameplay on 2026-10-02. Only `spd.nsbtx` is replaced. The active overlay
is `mods/spd.nsbtx`, and the ready ROM is `build/Spider-Man-WoS-modded.nds`.

## Exact modification

The original 4,772-byte NSBTX contains one 64x64 I8 texture, `Cartoon64`, with a
256-color BGR555 palette `Cartoon64_pl` at file offset 0x10A4. The experiment swaps
R/G channels for each color satisfying R>=8, R>G+4, R>B+4; it preserves B and bit 15.
156 colors are modified. The pixel indices, headers, dictionaries, dimensions,
asset size, FAT, header and every other asset remain byte-identical.

Original asset SHA256:
`461b2a00b617a4987e84338a63d7242ce54052c9537d85b8308719aa980c5206`

Modified asset SHA256:
`afc01a3744a1723d98fb74de310193dda14ae2dfd840a428655a07bcf0c0b8ef`

Modified ROM SHA256:
`9fca9e27bed2c220e44f6449d0261f061fea0ddc2e1df62db3d6563d6752eed8`

Exactly 311 bytes differ from the clean ROM, all in this asset's palette. The
recipe is implemented in `tools/nitro_texture.py`; generating it does not require
an external graphics editor. Recipe/old-new color metadata and texture previews
are emitted under `build/`. The full ROM differing ranges are in
`reference/visible_mod_report.json`.

## Build and confirm in a desktop emulator

```powershell
python mod.py experiment green-suit
python mod.py build
python mod.py verify
```

Use a recent [official melonDS desktop release](https://github.com/melonDS-emu/melonDS/releases)
or your existing DeSmuME setup. The automated proof below used the separate
[melonDS DS libretro core](https://github.com/JesseTG/melonds-ds/releases/tag/v1.1.5).

1. Open `build/roundtrip/Spider-Man-WoS-unmodified.nds` first to establish the baseline.
   If it is missing, run `python mod.py verify --round-trip` after extraction.
2. Use DS mode/direct boot and start a new game. Confirm that the playable red-suit
   Spider-Man has red body sections. Follow the title/menu prompts with Start/A;
   skip the introduction if desired and reach the first Residential gameplay area.
3. Close the baseline game and open `build/Spider-Man-WoS-modded.nds` from a fresh
   boot. Start a new game with the same choices; use the same emulator settings.
4. The same red-suit player now has bright green body sections. Blue areas, white
   eyes, background and UI retain their colors. Check movement/gameplay as desired.
   Use a fresh boot rather than an old save state that may contain cached assets.

### DeSmuME 0.9.11 on the other computer

The clone contains the texture-edit recipe, so you do not need to transfer the
generated `mods/spd.nsbtx` or an existing build. Copy the clean ROM into `original/`
and run the setup commands in [README.md](../README.md#set-up-on-another-computer).
Those commands create both the byte-identical baseline and the green-suit build.

1. Start your existing DeSmuME 0.9.11. Choose **File > Open ROM** and select
   `build/roundtrip/Spider-Man-WoS-unmodified.nds` inside the new clone.
2. Start a new game and reach the first Residential gameplay area. Use the keys
   assigned to DS Start/A in **Config > Control Config** for menus. Observe the
   playable Spider-Man's red body sections.
3. Choose **File > Close ROM**, then **File > Open ROM** and select
   `build/Spider-Man-WoS-modded.nds`. Start a new game and reach the same area.
   The previously red sections should be bright green.
4. After future builds, close and reopen the ROM. Avoid loading an old emulator
   save state for this comparison, because it can restore previously loaded assets.

These menu names follow the [official DeSmuME Windows manual](https://wiki.desmume.org/index.php?title=DeSmuME_Manual_for_the_Windows_port).
The manual describes an older version; gameplay evidence in this project uses
melonDS DS 1.1.5. DeSmuME 0.9.11 gameplay has not been tested here, so this is the
manual confirmation procedure for your installation. No emulator is required
for extraction, tests, or ROM builds.

### Optional automated captures

The optional harness supplies the exact sequence used here without requiring your
BIOS files or a GUI. It never loads/persists your game saves:

```powershell
python tools/emulator_smoke.py --fetch-core > build/emulator-modded.log 2>&1
python tools/emulator_smoke.py build/roundtrip/Spider-Man-WoS-unmodified.nds > build/emulator-unmodified.log 2>&1
```

It runs 1,800 frames, pressing Start+A for 8 frames at the start of every 120-frame
period after frame 600, with all other inputs released. The RTC is fixed to 2004-01-01
00:00. It records its full options in each capture directory's `boot.json`.
`--fetch-core` downloads the official v1.1.5 release once; both archive and DLL hashes
are checked before loading it. Its license/provenance are kept in `work/emulator/`.

Core DLL SHA256:
`534e0a4f489107dd35491bc9a628e8a32d7a9c58460a4951851dac570403312b`

Frame 1799 captures are available locally:

- Baseline: `build/boot-tests/Spider-Man-WoS-unmodified-61a6ed6e/frame-01799.png`.
- Modified: `build/boot-tests/Spider-Man-WoS-modded-9fca9e27/frame-01799.png`.

They show the player hanging from the ceiling in the same Residential scene/pose.
Exactly 452 RGB pixels differ, all inside [114,66,141,99), in the player sprite area;
all other pixels are identical. Earlier logo/title captures are available too.
These captures demonstrate the mod in the engine, beyond a standalone texture preview.

## Revert and rebuild

```powershell
python mod.py experiment revert
python mod.py build
python mod.py verify
```

With no other overlays, the ROM hash returns to
`61a6ed6e67fcce5cc63843fafeb0c0e6072bb750f552d5ff5d690cda02ea9203`.
This was tested. Revert removes only the generated texture overlay and refuses to
delete it if you have subsequently made another edit. Your clean source is unchanged.
To repeat the experiment, run the three green-suit commands again.

The tested behavior covers boot and the opening gameplay scene. Black-suit behavior,
a full playthrough and actual DS hardware remain untested. No model, actor binding,
combat field, room file, text or custom UI data was edited for this experiment.

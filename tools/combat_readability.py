"""Compose bounded upgrade text and the original red mission marker."""
from tools.qol_suits_menu import BASE, StringSlots, decode_grown
from tools import wos_tool as w
from tools import qol_minimap as qm

TEXT_EDITS = {
    185: 'Grapple with \ue602, then press \ue601.\nKick back and pop the enemy up.',
    188: 'Grapple with \ue602, then Up.\nLaunch and vault after the enemy.',
    197: 'Requires Spider Dance.\n\ue601, pause, \ue601, then rapid \ue601.',
    203: 'Needs Amazing Speed Boost.\nMax attack speed.',
    218: 'Requires Black Widowmaker.\nExtend its combo with more hits.',
    224: 'Requires Super Charge.\nHalves the required charge time.',
}


def text_overlay(clean, current, extra=None):
    slots = StringSlots(clean)
    texts = [decode_grown(current, i) for i in range(len(slots.texts))]    # any (grown) tree
    edits = {i: text for i, text in enumerate(texts) if text != slots.texts[i]}
    edits.update(TEXT_EDITS)
    if extra: edits.update(extra)
    table = BASE + w.u32(clean, BASE)
    if len(current) != len(clean) or current[:table] != clean[:table] or slots.variant_offsets(current) != slots.offsets:
        return slots.repack(current, edits)
    return slots.replace(edits)


def compose(glob, manifest, overlays, extra=None):
    entries = {e['name']: e for e in manifest['entries']}
    def clean(name):
        e = entries[name]
        return glob[e['offset']:e['offset'] + e['size']]
    icon = qm.load_icons(glob, manifest)['MissionMiniMapIcon']
    current = overlays.get(qm.ASSET, icon.palette)
    if current not in (icon.palette, qm.yellow_mission(icon)):
        raise ValueError('Mission marker requires an explicit palette merge')
    overlays[qm.ASSET] = icon.palette
    for name in ('American.strings', 'English.strings'):
        overlays[name] = text_overlay(clean(name), overlays.get(name, clean(name)), extra)
    return overlays

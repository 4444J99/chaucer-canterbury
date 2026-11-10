"""Stage 5 Scribal Witness Transducer (Hengwrt Hg vs Ellesmere El) and TEI-XML Emitter."""

from __future__ import annotations

import re
from xml.sax.saxutils import escape

from chaucer_canterbury.models import GeneratedVerseLine

THORN_WORDS = {
    "the": "þe", "that": "þat", "this": "þis", "thise": "þise", "thow": "þow",
    "thou": "þou", "ther": "þer", "ther-fore": "þer-fore", "thanne": "þanne",
    "than": "þan", "they": "þei", "with": "wiþ", "thurgh": "þurȝ", "thy": "þi",
    "thyn": "þin",
}


def to_hengwrt_orthography(line: str, line_index: int = 1) -> str:
    """Apply conservative c. 1400 Hengwrt (MS Peniarth 392D) scribal spelling habits."""
    tokens = line.split(" ")
    out: list[str] = []
    for idx, tok in enumerate(tokens):
        m = re.match(r"^([^A-Za-z]*)([A-Za-z'-]+)([^A-Za-z]*)$", tok)
        if not m:
            out.append(tok)
            continue
        lead, core, trail = m.groups()
        low = core.lower()
        was_cap = core[0].isupper()

        if low in THORN_WORDS:
            w = THORN_WORDS[low]
        else:
            w = low
            # Yogh 'ȝ' for palatal/velar 'gh'
            w = w.replace("ght", "ȝt").replace("gh", "ȝ")
            # Vocalic/intervocalic 'v' -> 'u' (e.g., 'love' -> 'loue', 'have' -> 'haue', 'servise' -> 'seruise')
            w = re.sub(r"([aeiouyrl])v([aeiouy])", r"\1u\2", w)

        if idx == 0 and was_cap:
            if w.startswith("f") and not w.startswith("ff") and line_index % 4 == 1:
                w = "ff" + w[1:]
            else:
                w = w[0].upper() + w[1:]
        elif was_cap:
            w = w[0].upper() + w[1:]
        out.append(f"{lead}{w}{trail}")
    return " ".join(out)


def to_ellesmere_orthography(line: str) -> str:
    """Apply regularized c. 1405 Ellesmere (Huntington EL 26 C 9) prestige orthography."""
    tokens = line.split(" ")
    out: list[str] = []
    for tok in tokens:
        m = re.match(r"^([^A-Za-z]*)([A-Za-z'-]+)([^A-Za-z]*)$", tok)
        if not m:
            out.append(tok)
            continue
        lead, core, trail = m.groups()
        was_cap = core[0].isupper()
        w = core
        # Ellesmere prefers 'v' intervocalically and explicit double long 'oo'/'ee' in closed syllables
        w_low = w.lower()
        w_low = w_low.replace("loue", "love").replace("haue", "have").replace("ioie", "joye")
        if was_cap:
            w_low = w_low[0].upper() + w_low[1:]
        out.append(f"{lead}{w_low}{trail}")
    return " ".join(out)


def generate_ellesmere_marginalia(source_auctor: str, source_title: str, genre: str) -> list[str]:
    """Generate authentic Latin rubricated marginalia in the Ellesmere apparatus manner."""
    return [
        f" Incipit narracio secundum materiam {source_auctor} ({source_title.split('(')[0].strip()}).",
        f" Nota de {genre.replace('_', ' ')}: Auctoritas allegata ante annum MCCCC.",
        " Vide quomodo fortuna et prudencia inter peregrinos contendunt.",
    ]


def emit_tei_xml_apparatus(
    turn_index: int,
    speaker_name: str,
    source_title: str,
    lines: list[GeneratedVerseLine],
) -> str:
    """Emit valid parallel TEI-XML critical apparatus encoding #Hg and #El witnesses."""
    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<TEI xmlns="http://www.tei-c.org/ns/1.0">',
        "  <teiHeader>",
        "    <fileDesc>",
        "      <titleStmt>",
        f"        <title>Emergent Pilgrimage Turn {turn_index}: {escape(speaker_name)}</title>",
        "      </titleStmt>",
        "      <sourceDesc>",
        "        <listWit>",
        '          <witness xml:id="Hg">Hengwrt Orthographic Profile (NLW Peniarth 392D model)</witness>',
        '          <witness xml:id="El">Ellesmere Orthographic Profile (Huntington EL 26 C 9 model)</witness>',
        "        </listWit>",
        f"        <bibl>Compilatio substrate: {escape(source_title)}</bibl>",
        "      </sourceDesc>",
        "    </fileDesc>",
        "  </teiHeader>",
        "  <text>",
        "    <body>",
        f'      <div type="pilgrimage_turn" n="{turn_index}">',
    ]
    for ln in lines[:12]:
        hg = escape(ln.hengwrt_orthography)
        el = escape(ln.ellesmere_orthography)
        ipa = escape(ln.ipa_transcription)
        pat = escape(ln.metrical_pattern)
        if hg != el:
            xml_lines.append(
                f'        <l n="{ln.line_number}" met="{pat}" ana="ipa:{ipa}">'
                f'<app><rdg wit="#Hg">{hg}</rdg><rdg wit="#El">{el}</rdg></app></l>'
            )
        else:
            xml_lines.append(
                f'        <l n="{ln.line_number}" met="{pat}" ana="ipa:{ipa}">{el}</l>'
            )
    xml_lines.extend(
        [
            "      </div>",
            "    </body>",
            "  </text>",
            "</TEI>",
        ]
    )
    return "\n".join(xml_lines)

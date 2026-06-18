"""
field_merge.py — ComicInfo.xml field merge logic for the editor core.

Ported from CAPT's widgets/xml_editor.py (build_xml_from_fields). Only tags
present in the submitted field set are touched; every other existing tag in
the original XML is preserved verbatim — this is how Volume, Month, Inker,
Colorist, Letterer, CoverArtist, Characters, Teams, Locations, Manga, and
StoryArcNumber survive edits made via either editor view even though neither
UI exposes them (EDITOR_SPEC.md Section 3.3).
"""

import logging
import xml.etree.ElementTree as ET
from typing import Optional

logger = logging.getLogger(__name__)


def build_xml_from_fields(
    field_values: dict, original_xml_content: Optional[str] = None
) -> str:
    """
    Build a ComicInfo.xml string from field values, preserving any existing
    tags not present in field_values.

    Per-field semantics:
    - value is None: leave the existing tag untouched (no-op)
    - value is empty/whitespace-only string: remove the tag if present
    - value is a non-empty string: create or update the tag

    :param field_values: dict of ComicInfo fields to apply
    :param original_xml_content: existing ComicInfo.xml content, if any
    :return: well-formed ComicInfo.xml string (UTF-8, with XML declaration)
    """
    if original_xml_content:
        try:
            root = ET.fromstring(original_xml_content)
        except ET.ParseError:
            root = ET.Element("ComicInfo")
    else:
        root = ET.Element("ComicInfo")

    for tag, value in field_values.items():
        if value is None:
            continue

        if isinstance(value, str) and value.strip() == "":
            elem = root.find(tag)
            if elem is not None:
                root.remove(elem)
            continue

        elem = root.find(tag)
        if elem is None:
            elem = ET.SubElement(root, tag)
        elem.text = str(value)

    xml_bytes = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    return xml_bytes.decode("utf-8")

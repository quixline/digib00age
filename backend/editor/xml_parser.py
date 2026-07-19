"""
xml_parser.py — ComicInfo.xml field extraction for the editor core.

Ported from CAPT's utils/xml_parser.py (see v2_investigation_report.md), with
ScanInformation dropped per EDITOR_SPEC.md Section 4 (no longer editable in
either editor view).
"""

import logging

from lxml import etree

from backend.rename_tool import parse_comic_filename

logger = logging.getLogger(__name__)

COMICINFO_TAGS = [
    "Series",
    "Number",
    "Title",
    "Year",
    "Genre",
    "AgeRating",
    "Format",
    "Notes",
    "Publisher",
    "Summary",
    "BlackAndWhite",
    "Count",
    "Writer",
    "Penciller",
    "PageCount",
    "StoryArc",
    "Language",
    "NeedsReview",
]


def parse_comicinfo_xml(xml_content: str) -> dict:
    """
    Parse ComicInfo.xml content and extract the editor's field set.

    Tolerant of malformed XML via lxml recovery mode. Missing tags resolve to
    an empty string. Tag matching is case-insensitive.

    :param xml_content: raw XML string
    :return: dict of field values keyed by tag name (see COMICINFO_TAGS)
    """
    field_values = {tag: "" for tag in COMICINFO_TAGS}

    try:
        parser = etree.XMLParser(recover=True, encoding="utf-8")
        root = etree.fromstring(xml_content.encode("utf-8"), parser=parser)
        tag_map = {}

        for elem in root.iter():
            tag_name = elem.tag.lower()
            tag_map[tag_name] = elem.text if elem.text is not None else ""

        for tag in COMICINFO_TAGS:
            for key, text in tag_map.items():
                if key == tag.lower():
                    field_values[tag] = text.strip()
                    break

    except Exception as exc:
        logger.error("Error parsing ComicInfo XML: %s", exc, exc_info=True)
        # Fall through and return the blank-field default

    return field_values


def parse_filename_for_comicinfo(filename: str) -> dict:
    """
    Fall back to filename-pattern parsing when ComicInfo.xml is missing or
    unparseable. Reuses the Filename Editor's parser (backend/rename_tool.py's
    parse_comic_filename -- the tested, scene-release-tolerant one, not the
    minimal scanner.py fallback) rather than reimplementing it, remapped from
    its lowercase keys to the editor's tag-cased field names.

    :param filename: archive filename, without path
    :return: dict with Series/Number/Year/Title keys (Title always blank --
        the filename pattern has no title component, matching CAPT's
        original behaviour)
    """
    parsed = parse_comic_filename(filename)
    return {
        "Series": parsed.get("series") or "",
        "Number": parsed.get("issue_num") or "",
        "Year": parsed.get("year") or "",
        "Title": "",
    }

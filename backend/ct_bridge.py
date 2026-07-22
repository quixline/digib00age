"""
ct_bridge.py — ComicVault's bridge into ComicTagger's comicapi/comictalker/
comictaggerlib.issueidentifier libraries (EDITOR_SPEC.md 9.1, ADMIN_SPEC.md
11.4.3). Imported directly, no CLI wrapper. Never calls ComicArchive.write_tags()
— ComicVault owns ComicInfo.xml read/write via backend/editor/. This module
only maps GenericMetadata -> ComicVault's flat field-dict and drives
search/identify against ComicVine.

Requires the comictagger dependency pinned in requirements.txt to a specific
develop-branch commit — PyPI's published release (1.5.5) predates the
comictalker plugin split this module depends on (confirmed 2026-07-03).
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from comicapi.comicarchive import ComicArchive
from comicapi.genericmetadata import ComicSeries, GenericMetadata
from comictaggerlib.issueidentifier import IssueIdentifier, IssueIdentifierOptions
from comictaggerlib.issueidentifier import Result as IIResult
from comictaggerlib.resulttypes import IssueResult
from comictalker.talker_utils import cleanup_html
from comictalker.talkers.comicvine import ComicVineTalker

from backend.config import PROJECT_ROOT, get_config
from backend.rename_tool import parse_comic_filename

CT_VERSION = "1.0.0"  # ComicVault's own version string, passed to CT's talker/cache
CT_CACHE_DIR = PROJECT_ROOT / "ct_cache"  # ComicVineTalker's sqlite search-result cache


def get_talker() -> ComicVineTalker:
    """One shared talker instance per call (cheap to construct); auto-selects
    the rate limiter (default vs personal-key) based on the configured
    comicvine_api_key. parse_settings() requires all four keys below — a
    partial dict raises KeyError (confirmed against the real installed
    package, not just its type hints)."""
    CT_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    talker = ComicVineTalker(version=CT_VERSION, cache_folder=CT_CACHE_DIR)
    api_key = get_config().get("comicvine_api_key", "")
    talker.parse_settings(
        {
            "comicvine_key": api_key or None,
            "comicvine_url": None,
            "comicvine_custom_parameters": "",
            "cv_use_series_start_as_volume": False,
        }
    )
    return talker


def check_api_key(api_key: str) -> tuple[str, bool]:
    """Save & Test button's backend call — hits ComicVine's team/1/ endpoint
    with whatever key was just typed (not necessarily the saved one).
    check_status() only reads comicvine_key/comicvine_url, confirmed against
    source — no need for the other two parse_settings() keys here."""
    talker = get_talker()
    return talker.check_status({"comicvine_key": api_key or None, "comicvine_url": None})


@dataclass
class SeriesResult:
    id: str
    name: str
    start_year: Optional[int]
    publisher: str
    count_of_issues: Optional[int]
    description: str
    image_url: str


def search_series(series_name: str) -> list[SeriesResult]:
    """Shared backend function (EDITOR_SPEC.md 9.1) — called by the Full
    Editor's Search Online modal. The CT Auto-Tag automation stage shares
    this module's talker/rate-limiter setup via identify_file() below rather
    than calling this function directly (automated identify vs. manual
    search are different CT entry points, per DECISIONS.md 2026-07-03)."""
    talker = get_talker()
    results: list[ComicSeries] = talker.search_for_series(series_name, on_rate_limit=None)
    return [
        SeriesResult(
            id=r.id,
            name=r.name,
            start_year=r.start_year,
            publisher=r.publisher or "",
            count_of_issues=r.count_of_issues,
            description=r.description or "",
            image_url=r.image_url or "",
        )
        for r in results
    ]


@dataclass
class IssueResultDTO:
    issue_id: str
    number: str
    date: str  # "YYYY" or "YYYY-MM" or "" — derived from year/month
    title: str
    description: str
    cover_url: str


def _issue_number_sort_key(number: str) -> tuple:
    """Natural sort key for issue numbers ("2" < "11" < "11A" < "Annual 1").
    ComicVine returns issues in whatever order its own API paginates them,
    not numeric issue order (Select Issue modal, EDITOR_SPEC.md 9.6) -- and
    the Select Series modal's Ok fast-path (9.6/9.7) assumes the first
    result in this list is issue #1, so both display order and that
    fast-path depend on sorting here rather than trusting API order."""
    m = re.match(r"^(\d+(?:\.\d+)?)", (number or "").strip())
    if m:
        return (0, float(m.group(1)), number[m.end():].strip().lower())
    return (1, 0.0, (number or "").strip().lower())


def list_issues_for_series(series_id: str) -> list[IssueResultDTO]:
    talker = get_talker()
    issues: list[GenericMetadata] = talker.fetch_issues_in_series(series_id, on_rate_limit=None)
    out = []
    for md in issues:
        date = "-".join(str(x) for x in (md.year, md.month) if x) if (md.year or md.month) else ""
        out.append(
            IssueResultDTO(
                issue_id=md.issue_id or "",
                number=md.issue or "",
                date=date,
                title=md.title or "",
                description=md.description or "",
                cover_url=(md._cover_image.URL if md._cover_image else ""),
            )
        )
    out.sort(key=lambda r: _issue_number_sort_key(r.number))
    return out


def fetch_issue_metadata(issue_id: str) -> GenericMetadata:
    """Full GenericMetadata for a specific issue — used by both the Search
    Online modal's Confirm step and the CT Auto-Tag stage's write path."""
    return get_talker().fetch_comic_data(issue_id=issue_id, on_rate_limit=None)


# -- GenericMetadata -> ComicVault field-dict mapping --
# Captures everything CT/ComicVine supplies into ComicInfo.xml, mirroring
# comicapi/tags/comicrack.py's own write mapping field-for-field (confirmed
# 2026-07-04 after live testing showed data loss against a real file) -- not
# just the subset ComicVault's own editor UI exposes. build_xml_from_fields()
# writes any dict key as a literal XML tag with no COMICINFO_TAGS filtering
# in this callpath, so tags the editor never displays (Inker/Colorist/
# Letterer/CoverArtist/Editor/Volume/Web/etc.) still land in the file and
# survive future editor saves via field_merge.py's normal preservation rule.
#
# Deliberately still excludes Genre/Format/AgeRating/BlackAndWhite -- not
# an "editor doesn't show it" exclusion like the above, but a correctness
# one: Genre/Format/AgeRating are ComicVault-enforced dropdowns (DECISIONS.md
# 2026-07-03 session 3; ComicVine's issue mapper doesn't even set md.genres)
# and BlackAndWhite has a real semantic mismatch -- ComicVault's own
# convention is the literal text "on" for checked (EDITOR_SPEC.md 3.3),
# while CT's own writer uses "Yes", which the Editor's populateForm() would
# not recognise as checked. PageCount is excluded too -- always
# auto-computed from the archive elsewhere in ComicVault, never from CT.
def metadata_to_field_dict(md: GenericMetadata) -> dict:
    """Maps onto ComicInfo.xml tag names so the result can be handed
    straight to build_xml_from_fields(). Only non-empty/known fields are
    included -- the caller decides None-vs-value semantics per
    field_merge.py's rules (absent key = no-op, preserving whatever's
    already there). Caller is responsible for ensuring md came from a full
    single-issue fetch (ct_bridge.fetch_issue_metadata) rather than the
    lighter bulk-search results IssueIdentifier.identify() returns, which
    do not carry credits -- confirmed 2026-07-04, see ct_autotag.py."""
    fields: dict = {}
    if md.series:
        fields["Series"] = md.series
    if md.issue:
        fields["Number"] = md.issue
    if md.issue_count:
        fields["Count"] = str(md.issue_count)
    if md.title:
        fields["Title"] = md.title
    if md.volume:
        fields["Volume"] = str(md.volume)
    if md.description:
        # ComicVine's description comes back as raw HTML (<p><em>...</em></p>,
        # occasional <table> credit lists) -- CT's own pipeline runs this
        # through cleanup_html() before writing tags (comictaggerlib/md.py),
        # converting it to plain text (and tables to a readable text-table
        # form) rather than leaving markup in the field. Found missing
        # 2026-07-04 -- without this, the raw tags were XML-escaping into
        # literal "&lt;p&gt;&lt;em&gt;" text in Summary.
        fields["Summary"] = cleanup_html(md.description)
    if md.alternate_series:
        fields["AlternateSeries"] = md.alternate_series
    if md.alternate_number:
        fields["AlternateNumber"] = md.alternate_number
    if md.alternate_count:
        fields["AlternateCount"] = str(md.alternate_count)
    if md.story_arcs:
        fields["StoryArc"] = ", ".join(md.story_arcs)
    if md.series_groups:
        fields["SeriesGroup"] = ", ".join(md.series_groups)
    if md.publisher:
        fields["Publisher"] = md.publisher
    if md.imprint:
        fields["Imprint"] = md.imprint
    if md.day:
        fields["Day"] = str(md.day)
    if md.month:
        fields["Month"] = str(md.month)
    if md.year:
        fields["Year"] = str(md.year)
    if md.language:
        fields["Language"] = md.language
    if md.web_links:
        fields["Web"] = " ".join(u.url for u in md.web_links)
    if md.manga:
        fields["Manga"] = md.manga
    if md.characters:
        fields["Characters"] = ", ".join(sorted(md.characters))
    if md.teams:
        fields["Teams"] = ", ".join(sorted(md.teams))
    if md.locations:
        fields["Locations"] = ", ".join(sorted(md.locations))

    if md.issue_id:
        fields["Notes"] = (
            "Tagged with ComicVault (ComicTagger backend) using info from Comic Vine "
            f"on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. [Issue ID {md.issue_id}]"
        )

    _ROLE_FIELDS = (
        ("Writer", GenericMetadata.writer_synonyms),
        ("Penciller", GenericMetadata.penciller_synonyms),
        ("Inker", GenericMetadata.inker_synonyms),
        ("Colorist", GenericMetadata.colorist_synonyms),
        ("Letterer", GenericMetadata.letterer_synonyms),
        ("CoverArtist", GenericMetadata.cover_synonyms),
        ("Editor", GenericMetadata.editor_synonyms),
    )
    for tag, synonyms in _ROLE_FIELDS:
        people = [c.person for c in md.credits if c.role.casefold() in synonyms]
        if people:
            fields[tag] = ", ".join(people)

    return fields


# -- Auto-Tag identify pipeline (CT Auto-Tag automation stage only; the Full
#    Editor's manual Search Online does NOT use this -- it goes through
#    search_series()/list_issues_for_series() above directly, per
#    EDITOR_SPEC.md 9.5's manual-path field-source rule) --


class ConfidenceLevel:
    CONFIDENT = "confident"
    LOW_CONFIDENCE = "low_confidence"
    NO_MATCH = "no_match"


@dataclass
class AutoTagIdentifyResult:
    confidence: str  # ConfidenceLevel.*
    best_match: Optional[IssueResult] = None
    error: Optional[str] = None


# IssueIdentifierOptions has no defaults of its own (all 9 fields required,
# confirmed against the real installed class). series_match_search_thresh/
# series_match_identify_thresh are overridden at call-time in identify_file()
# from the Admin page's Match Ratio Threshold slider (processing_folder_
# ct_match_threshold, default 80 -- added 2026-07-04, no UI to tune at first,
# added once Tez had more real-world experience with match quality). Both
# stay tied to one value, matching CT's own single "match ratio" concept.
_DEFAULT_IIO_KWARGS = dict(
    use_publisher_filter=False,
    publisher_filter=[],
    quiet=True,
    border_crop_percent=10,
    tpb_detection=False,
)


def identify_file(archive_path: str) -> AutoTagIdentifyResult:
    """Runs IssueIdentifier against a file already on disk, seeded from its
    existing ComicInfo.xml (if any) via CT's own read_tags. If the archive
    has no Series/Issue# embedded, falls back to ComicVault's filename
    parser (backend/rename_tool.py's parse_comic_filename -- the tested,
    scene-release-tolerant one, not the minimal scanner.py fallback).

    A one-shot/OGN filename with no issue number defaults to "1" (matches
    ComicTagger's own default-on "If no issue number, assume 1" Auto-Tag
    option, confirmed with Tez 2026-07-04 after live testing surfaced a
    real file this fixes). Only genuinely produces no_match now if even the
    filename can't supply a series name at all."""
    talker = get_talker()
    ca = ComicArchive(archive_path)
    md = ca.read_tags("cr")

    if not md.series or not md.issue:
        parsed = parse_comic_filename(os.path.basename(archive_path))
        if not md.series:
            md.series = parsed["series"]
        if not md.issue:
            md.issue = parsed["issue_num"] or "1"
        if not md.year and parsed["year"]:
            md.year = int(parsed["year"])

    if not md.series or not md.issue:
        return AutoTagIdentifyResult(
            confidence=ConfidenceLevel.NO_MATCH,
            error="Not enough info for a search (Series/Issue # required)",
        )

    match_threshold = get_config().get("processing_folder_ct_match_threshold", 80)
    iio = IssueIdentifierOptions(
        cache_dir=CT_CACHE_DIR,
        talker=talker,
        series_match_search_thresh=match_threshold,
        series_match_identify_thresh=match_threshold,
        **_DEFAULT_IIO_KWARGS,
    )
    ii = IssueIdentifier(iio, on_rate_limit=None, output=lambda *a, **k: None)

    result, matches = ii.identify(ca, md)

    if result == IIResult.single_good_match:
        return AutoTagIdentifyResult(confidence=ConfidenceLevel.CONFIDENT, best_match=matches[0])
    if result == IIResult.no_matches:
        return AutoTagIdentifyResult(confidence=ConfidenceLevel.NO_MATCH)
    # single_bad_cover_score / multiple_bad_cover_scores / multiple_good_matches
    # -- all "low confidence", governed by the Save on Low Confidence toggle.
    best = matches[0] if matches else None
    return AutoTagIdentifyResult(confidence=ConfidenceLevel.LOW_CONFIDENCE, best_match=best)

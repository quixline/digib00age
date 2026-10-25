"""
ct_bridge.py — digib00age's bridge into ComicTagger's comicapi/comictalker/
comictaggerlib.issueidentifier libraries (EDITOR_SPEC.md 9.1, ADMIN_SPEC.md
11.4.3). Imported directly, no CLI wrapper. Never calls ComicArchive.write_tags()
— digib00age owns ComicInfo.xml read/write via backend/editor/. This module
only maps GenericMetadata -> digib00age's flat field-dict and drives
search/identify against ComicVine.

Requires the comictagger dependency pinned in requirements.txt to a specific
develop-branch commit — PyPI's published release (1.5.5) predates the
comictalker plugin split this module depends on (confirmed 2026-07-03).
"""

from __future__ import annotations

import contextlib
import difflib
import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from backend import ct_vendor_bootstrap  # noqa: F401 — seeds comicapi archiver/tag plugins before any ComicArchive() call below

from comicapi.comicarchive import ComicArchive
from comicapi.genericmetadata import ComicSeries, GenericMetadata
from comicapi.utils import sanitize_title
from comictaggerlib.issueidentifier import IssueIdentifier, IssueIdentifierOptions
from comictaggerlib.issueidentifier import Result as IIResult
from comictaggerlib.resulttypes import IssueResult
from comictalker.comictalker import TalkerError
from comictalker.talker_utils import cleanup_html
from comictalker.talkers.comicvine import ComicVineTalker

from backend.config import _ct_cache_dir, get_config
from backend.rename_tool import parse_comic_filename

CT_VERSION = "1.0.0"  # digib00age's own version string, passed to CT's talker/cache
CT_CACHE_DIR = _ct_cache_dir()  # ComicVineTalker's sqlite search-result cache


class _TalkerErrorCapture(logging.Handler):
    """IssueIdentifier._search_for_issues() catches TalkerError internally
    (network failures, ComicVine rate limits, timeouts) and returns an empty
    result rather than raising -- identify() then reports IIResult.no_matches,
    indistinguishable from a genuine "ComicVine has nothing" result (found
    2026-10-25: a brief ComicVine hiccup made every single Auto-Tag file in
    that run log as a normal [skipped: no match], with no trace of the real
    cause). It does still call self.log_msg(f"Error searching for series...")
    before swallowing, which reaches the stdlib `logging` module -- this
    handler captures just that message so identify_file() can tell the two
    cases apart."""

    def __init__(self) -> None:
        super().__init__(level=logging.INFO)
        self.messages: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.messages.append(record.getMessage())


@contextlib.contextmanager
def _capture_issue_identifier_errors():
    """Temporarily force comictaggerlib.issueidentifier's logger to emit (it
    has no handler/level configured by the app otherwise, so these messages
    normally go nowhere -- confirmed 2026-10-25, nothing app-wide calls
    logging.basicConfig()) and collect anything it logs during the call."""
    target_logger = logging.getLogger("comictaggerlib.issueidentifier")
    handler = _TalkerErrorCapture()
    prev_level = target_logger.level
    target_logger.addHandler(handler)
    target_logger.setLevel(logging.INFO)
    try:
        yield handler.messages
    finally:
        target_logger.removeHandler(handler)
        target_logger.setLevel(prev_level)


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


def _series_match_score(series_name: str, result: ComicSeries) -> tuple[float, int]:
    """Best-match ranking key: title-similarity ratio first (same technique
    CT's own comicapi.utils.titles_match uses internally for accept/reject
    filtering, applied here as a score instead of a threshold cutoff), then
    issue count as a flagship-vs-spinoff tiebreak. Needed because CT's own
    ComicVineTalker.search_for_series() can serve results from its sqlite
    cache (comictalker/comiccacher.py's get_search_results(), no ORDER BY),
    which does not preserve ComicVine's live relevance order -- confirmed
    2026-07-23 by reproducing the exact cache-read query against a real
    cache hit that put a spinoff series ahead of the actual "2000 AD" series."""
    ratio = difflib.SequenceMatcher(
        None, sanitize_title(series_name), sanitize_title(result.name)
    ).ratio()
    return (ratio, result.count_of_issues or 0)


class ComicVineLookupError(RuntimeError):
    """Raised by the manual Search Online path (search_series/
    list_issues_for_series/fetch_issue_metadata) when the underlying
    ComicVineTalker call fails (network error, rate limit, timeout). Without
    this, a TalkerError bubbled up as a bare unhandled 500 with no message
    reaching the Full Editor UI -- indistinguishable from the modal simply
    coming back empty (found 2026-10-25 diagnosing a ComicVine hiccup)."""


def search_series(series_name: str) -> list[SeriesResult]:
    """Shared backend function (EDITOR_SPEC.md 9.1) — called by the Full
    Editor's Search Online modal. The CT Auto-Tag automation stage shares
    this module's talker/rate-limiter setup via identify_file() below rather
    than calling this function directly (automated identify vs. manual
    search are different CT entry points, per DECISIONS.md 2026-07-03)."""
    talker = get_talker()
    try:
        results: list[ComicSeries] = talker.search_for_series(series_name, on_rate_limit=None)
    except TalkerError as e:
        raise ComicVineLookupError(str(e)) from e

    # ComicVine's /search endpoint (above) is thin -- count_of_issues and the
    # cover image are frequently 0/blank for many volumes even when real data
    # exists, because /search returns less than the full per-volume resource
    # (confirmed 2026-10-25: a long-since-tagged series showed 0 issues/blank
    # cover here, but full data once Select Issue's separate full-volume fetch
    # ran). Batch-enrich every result from the richer /volumes/ endpoint in
    # ONE extra call -- it filters by up to 100 ids per request (_get_id_list)
    # -- rather than one fetch per row, which would multiply this search's API
    # cost by its result count and risk the same rate-limit failure mode as
    # today's Auto-Tag incident. Falls back to the thin data on failure rather
    # than failing the whole search over an enrichment-only call.
    if results:
        try:
            enriched = talker._fetch_series([int(r.id) for r in results], on_rate_limit=None)
            enriched_by_id = {series.id: series for series, _complete in enriched}
            results = [enriched_by_id.get(r.id, r) for r in results]
        except TalkerError:
            pass

    results.sort(key=lambda r: _series_match_score(series_name, r), reverse=True)
    return [
        SeriesResult(
            id=r.id,
            name=r.name,
            start_year=r.start_year,
            publisher=r.publisher or "",
            count_of_issues=r.count_of_issues,
            # ComicVine's series description is raw HTML and sometimes embeds
            # a small <img> (e.g. a "first issue" cover thumbnail) alongside
            # the text -- run it through the same cleanup_html() used for the
            # Summary field mapping below so the Select Series preview shows
            # plain text only, never an inline image.
            description=cleanup_html(r.description) if r.description else "",
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
    try:
        issues: list[GenericMetadata] = talker.fetch_issues_in_series(series_id, on_rate_limit=None)
    except TalkerError as e:
        raise ComicVineLookupError(str(e)) from e
    out = []
    for md in issues:
        date = "-".join(str(x) for x in (md.year, md.month) if x) if (md.year or md.month) else ""
        out.append(
            IssueResultDTO(
                issue_id=md.issue_id or "",
                number=md.issue or "",
                date=date,
                title=md.title or "",
                description=cleanup_html(md.description) if md.description else "",
                cover_url=(md._cover_image.URL if md._cover_image else ""),
            )
        )
    out.sort(key=lambda r: _issue_number_sort_key(r.number))
    return out


def fetch_issue_metadata(issue_id: str) -> GenericMetadata:
    """Full GenericMetadata for a specific issue — used by both the Search
    Online modal's Confirm step and the CT Auto-Tag stage's write path."""
    try:
        return get_talker().fetch_comic_data(issue_id=issue_id, on_rate_limit=None)
    except TalkerError as e:
        raise ComicVineLookupError(str(e)) from e


# -- GenericMetadata -> digib00age field-dict mapping --
# Captures everything CT/ComicVine supplies into ComicInfo.xml, mirroring
# comicapi/tags/comicrack.py's own write mapping field-for-field (confirmed
# 2026-07-04 after live testing showed data loss against a real file) -- not
# just the subset digib00age's own editor UI exposes. build_xml_from_fields()
# writes any dict key as a literal XML tag with no COMICINFO_TAGS filtering
# in this callpath, so tags the editor never displays (Inker/Colorist/
# Letterer/CoverArtist/Editor/Volume/Web/etc.) still land in the file and
# survive future editor saves via field_merge.py's normal preservation rule.
#
# Deliberately still excludes Genre/Format/AgeRating/BlackAndWhite -- not
# an "editor doesn't show it" exclusion like the above, but a correctness
# one: Genre/Format/AgeRating are digib00age-enforced dropdowns (DECISIONS.md
# 2026-07-03 session 3; ComicVine's issue mapper doesn't even set md.genres)
# and BlackAndWhite has a real semantic mismatch -- digib00age's own
# convention is the literal text "on" for checked (EDITOR_SPEC.md 3.3),
# while CT's own writer uses "Yes", which the Editor's populateForm() would
# not recognise as checked. PageCount is excluded too -- always
# auto-computed from the archive elsewhere in digib00age, never from CT.
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
            "digib00age thanks ComicTagger, Comic Vine and all the contributors for their work. "
            f"[Issue ID {md.issue_id}]"
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
# added once digib00age had more real-world experience with match quality). Both
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
    has no Series/Issue# embedded, falls back to digib00age's filename
    parser (backend/rename_tool.py's parse_comic_filename -- the tested,
    scene-release-tolerant one, not the minimal scanner.py fallback).

    A one-shot/OGN filename with no issue number defaults to "1" (matches
    ComicTagger's own default-on "If no issue number, assume 1" Auto-Tag
    option, confirmed with digib00age 2026-07-04 after live testing surfaced a
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

    with _capture_issue_identifier_errors() as log_messages:
        result, matches = ii.identify(ca, md)

    if result == IIResult.single_good_match:
        return AutoTagIdentifyResult(confidence=ConfidenceLevel.CONFIDENT, best_match=matches[0])
    if result == IIResult.no_matches:
        # A genuine "ComicVine has nothing" and a swallowed TalkerError both
        # land here (see _TalkerErrorCapture docstring) -- surface the
        # captured message when there is one so this doesn't silently look
        # identical to a real no-match in the Auto-Tag log/admin UI.
        talker_errors = [m for m in log_messages if "error" in m.lower() or "aborting" in m.lower()]
        return AutoTagIdentifyResult(
            confidence=ConfidenceLevel.NO_MATCH,
            error=" / ".join(talker_errors) if talker_errors else None,
        )
    # single_bad_cover_score / multiple_bad_cover_scores / multiple_good_matches
    # -- all "low confidence", governed by the Save on Low Confidence toggle.
    best = matches[0] if matches else None
    return AutoTagIdentifyResult(confidence=ConfidenceLevel.LOW_CONFIDENCE, best_match=best)

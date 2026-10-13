// digib00age — api.js
// Shared fetch wrapper for all /api/... calls. Plain global script (no ES
// modules anywhere in this codebase) — must be loaded before any script
// that calls apiFetch(). Auth: session is a cookie (cv_session, see
// backend/auth.py) sent automatically by the browser — no header injection
// needed here.
//
// reader.js and sw.js are deliberately excluded (see docs/DECISIONS.md /
// docs/api-consolidation-scope.md) — not migrated, not loaded here.

const API_BASE = '/api';

// ---------------------------------------------------------------------------
// JSDoc type hints for the backend/schemas.py response shapes covered by
// Session 2 Phase 1 (library.py) — hand-maintained against schemas.py, NOT
// generated. No build step reads these; they're VS Code/editor-only type
// hints via `@type`/`@returns` casts at call sites. Only endpoints with a
// Pydantic response_model are typed here — don't backfill one for an
// endpoint schemas.py doesn't cover yet, that just invites drift between
// the annotation and what the backend actually returns. See
// DECISIONS.md "Lightweight typed API contracts: response_model + JSDoc,
// not codegen".
// ---------------------------------------------------------------------------

/**
 * @typedef {Object} PersonCredit
 * @property {number} person_id
 * @property {string} name
 */

/**
 * @typedef {Object} IssueOut
 * @property {number} id
 * @property {string} series
 * @property {number|null} volume
 * @property {string|null} number
 * @property {string|null} title
 * @property {number|null} year
 * @property {number|null} month
 * @property {string|null} publisher
 * @property {string|null} format
 * @property {string|null} format_group
 * @property {string|null} summary
 * @property {string|null} story_arc
 * @property {number|null} story_arc_number
 * @property {string|null} writer
 * @property {string|null} penciller
 * @property {PersonCredit[]} writers
 * @property {PersonCredit[]} pencillers
 * @property {string|null} characters
 * @property {string|null} teams
 * @property {string|null} locations
 * @property {string|null} age_rating
 * @property {string|null} language
 * @property {boolean} black_and_white
 * @property {string} manga
 * @property {boolean} favorites
 * @property {boolean} flagged_for_review
 * @property {boolean} queued_for_reading
 * @property {number|null} personal_rating
 * @property {number|null} page_count
 * @property {number|null} count
 * @property {string[]} genres
 * @property {string} cover_path
 * @property {string|null} metadata_source
 * @property {boolean} missing
 * @property {string|null} date_added
 * @property {string} read_status
 * @property {number} current_page
 * @property {string|null} last_read_at
 */

/**
 * @typedef {IssueOut & {next_issue_id: number|null, prev_issue_id: number|null}} IssueDetailOut
 */

/**
 * @typedef {IssueOut & {relative_folder: string}} IssueWithFolderOut
 */

/**
 * @typedef {Object} FolderEntryOut
 * @property {string} name
 * @property {number} issue_count
 * @property {string|null} cover_path
 * @property {boolean} has_favorite
 * @property {boolean} has_flagged_review
 * @property {number|null} year_min
 * @property {number|null} year_max
 */

/**
 * @typedef {Object} TabFolderOut
 * @property {number} tab_id
 * @property {string} path
 * @property {FolderEntryOut[]} folders
 * @property {IssueOut[]} files
 */

/**
 * @typedef {Object} TabSearchOut
 * @property {number} tab_id
 * @property {string} query
 * @property {number} count
 * @property {IssueWithFolderOut[]} results
 */

/**
 * @typedef {Object} GenreCount
 * @property {string} genre
 * @property {number} issue_count
 */

/**
 * @typedef {Object} PublisherCount
 * @property {string} publisher
 * @property {number} series_count
 */

/**
 * @typedef {Object} PersonCount
 * @property {number} person_id
 * @property {string} name
 * @property {number} series_count
 */

async function apiFetch(path, options = {}) {
  const { method, headers, body, onLoading, onError, retry = true, signal } = options;
  const fetchOpts = (method || headers || body || signal)
    ? { method, headers, body, signal }
    : undefined;

  onLoading?.(true);
  try {
    let res;
    const attempts = retry ? 2 : 1;
    for (let attempt = 1; attempt <= attempts; attempt++) {
      try {
        res = await fetch(API_BASE + path, fetchOpts);
        break;
      } catch (networkErr) {
        if (networkErr.name === 'AbortError') throw networkErr;
        if (attempt === attempts) throw new Error(`Network error (server unreachable): ${path}`);
      }
    }
    if (!res.ok) {
      const httpErr = new Error(`HTTP ${res.status} from ${path}`);
      httpErr.status = res.status;
      httpErr.body = await res.json().catch(() => null);
      throw httpErr;
    }
    return res.json();
  } catch (err) {
    onError?.(err);
    throw err;
  } finally {
    onLoading?.(false);
  }
}

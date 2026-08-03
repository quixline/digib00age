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

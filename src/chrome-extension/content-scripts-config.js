// Shared by background.js (via importScripts) and options.js (via <script>) so
// the dynamically-registered content scripts for a user-added origin are defined
// in exactly one place, identical in shape to manifest.json's static localhost
// entries. Registration ids are derived from the origin so re-adding the same
// origin cleanly replaces its previous registration instead of duplicating it.

function contentScriptIdsFor(origin) {
  return [`editor-fill-${origin}`, `genre-bridge-${origin}`];
}

function contentScriptDefsFor(origin) {
  const [editorFillId, genreBridgeId] = contentScriptIdsFor(origin);
  return [
    {
      id: editorFillId,
      matches: [`${origin}/editor*`],
      js: ['content/editor-fill.js'],
      runAt: 'document_idle',
    },
    {
      id: genreBridgeId,
      matches: [`${origin}/editor*`],
      js: ['content/genre-bridge-main.js'],
      world: 'MAIN',
      runAt: 'document_idle',
    },
  ];
}

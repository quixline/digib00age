// Runs the scrape on demand only — no persistent content script on
// goodreads.com, no goodreads.com host_permissions entry. activeTab grants
// momentary access to whichever tab the toolbar icon was clicked on.
chrome.action.onClicked.addListener(async (tab) => {
  if (!tab.id || !tab.url || !tab.url.includes('goodreads.com/book/show')) {
    console.warn('[GR-bridge] icon clicked on a non-book page, ignoring:', tab.url);
    return;
  }

  const [{ result }] = await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: scrapeGoodreadsPage,
  });

  if (!result) {
    console.warn('[GR-bridge] scrape returned nothing');
    return;
  }

  await chrome.storage.local.set({ grScrape: result, grScrapeAt: Date.now() });
});

// Injected into the GoodReads tab via chrome.scripting.executeScript — must be
// fully self-contained (no references to anything outside this function body).
function scrapeGoodreadsPage() {
  const fromNextData = () => {
    const el = document.getElementById('__NEXT_DATA__');
    if (!el) throw new Error('no __NEXT_DATA__ element');

    const data = JSON.parse(el.textContent);
    const apollo = data.props?.pageProps?.apolloState;
    if (!apollo) throw new Error('no apolloState in __NEXT_DATA__');

    const rootKeys = Object.keys(apollo.ROOT_QUERY || {});
    const bookQueryKey = rootKeys.find((k) => k.startsWith('getBookByLegacyId'));
    const bookRef = bookQueryKey && apollo.ROOT_QUERY[bookQueryKey]?.__ref;
    const book = bookRef && apollo[bookRef];
    if (!book) throw new Error('no Book entity in apolloState');

    const contributorName = (edge) => edge && apollo[edge.node?.__ref]?.name;

    const writer = contributorName(book.primaryContributorEdge) || '';

    const illustratorEdge = (book.secondaryContributorEdges || []).find((e) =>
      /illustrator|artist|penciller/i.test(e.role || '')
    );
    const penciller = contributorName(illustratorEdge) || '';

    const publisher = book.details?.publisher || '';

    const pubTime = book.details?.publicationTime;
    const year = pubTime ? String(new Date(pubTime).getUTCFullYear()) : '';

    const language = book.details?.language?.name || '';

    const genresRaw = (book.bookGenres || [])
      .map((bg) => bg.genre?.name)
      .filter(Boolean);

    const strippedKey = Object.keys(book).find(
      (k) => k.startsWith('description(') && k.includes('stripped')
    );
    const summary = (strippedKey ? book[strippedKey] : book.description) || '';

    const title = book.title || '';

    if (!writer && !publisher && !year && !summary) {
      throw new Error('all fields empty — __NEXT_DATA__ shape likely changed');
    }

    return { title, writer, penciller, publisher, year, language, genresRaw, summary };
  };

  const fromDom = () => {
    console.warn('[GR-bridge] falling back to DOM scraping — publisher will likely be blank');

    const contributorNodes = Array.from(document.querySelectorAll('.ContributorLink'));
    let writer = '';
    let penciller = '';
    for (const node of contributorNodes) {
      const name = node.querySelector('.ContributorLink__name')?.textContent?.trim() || '';
      const role = node.querySelector('.ContributorLink__role')?.textContent || '';
      if (!name) continue;
      if (/writer|author/i.test(role) && !writer) writer = name;
      else if (/illustrator|artist|penciller/i.test(role) && !penciller) penciller = name;
    }
    if (!writer && contributorNodes.length) {
      writer = contributorNodes[0].querySelector('.ContributorLink__name')?.textContent?.trim() || '';
    }

    const featuredText = document.querySelector('.FeaturedDetails')?.textContent || '';
    const yearMatch = featuredText.match(/(19|20)\d{2}/);
    const year = yearMatch ? yearMatch[0] : '';

    const summary =
      document.querySelector('[data-testid="description"]')?.textContent?.trim() ||
      document.querySelector('.BookPageMetadataSection__description')?.textContent?.trim() ||
      '';

    const title = document.querySelector('h1')?.textContent?.trim() || '';

    // Best-effort only — Language typically lives in a collapsed "Book details &
    // editions" panel not present in the initial DOM, so this will often come up
    // empty even when the __NEXT_DATA__ path would have found it.
    let language = '';
    for (const el of document.querySelectorAll('dt, span, div')) {
      if (el.textContent?.trim() === 'Language' && el.nextElementSibling) {
        language = el.nextElementSibling.textContent?.trim() || '';
        if (language) break;
      }
    }

    // Genre pills link to /genres/<slug> — a more durable selector than any
    // specific CSS class, since it's tied to the link's actual destination.
    const genresRaw = Array.from(new Set(
      Array.from(document.querySelectorAll('a[href*="/genres/"]'))
        .map((a) => a.textContent?.trim())
        .filter(Boolean)
    ));

    return { title, writer, penciller, publisher: '', year, language, genresRaw, summary };
  };

  try {
    return fromNextData();
  } catch (e) {
    console.warn('[GR-bridge] __NEXT_DATA__ scrape failed, using DOM fallback:', e.message);
    try {
      return fromDom();
    } catch (e2) {
      console.warn('[GR-bridge] DOM fallback also failed:', e2.message);
      return null;
    }
  }
}

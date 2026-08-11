// digib00age — pwa.js
// Service worker registration + install-prompt capture.
// Included in all full HTML pages. No automatic prompts — install is
// triggered only by the explicit "Install App" button on the Admin page.

// The service worker is deliberately not used on loopback origins — the ones
// the tray app launches its --app= windows at. There it's pure downside: the
// server is on this same machine, so offline caching buys nothing, while a
// cold SW startup can park the navigation before it ever reaches the network.
// Confirmed 2026-08-09 on a permanently-blank --app= window: the backend's
// access log for the entire boot contained exactly one browser request,
// GET /sw.js — never GET / — while DevTools showed an empty Elements tree and
// an empty Network tab, i.e. the navigation was queued waiting on a service
// worker that never became ready. LAN clients (the mobile reader, other people
// browsing the library over the network) hit a real host/IP origin and keep
// the full PWA, which is where offline support actually matters.
const IS_LOOPBACK_ORIGIN = ['localhost', '127.0.0.1', '::1', '[::1]'].includes(location.hostname);

if ('serviceWorker' in navigator) {
  if (IS_LOOPBACK_ORIGIN) {
    // Tear down anything a previous version of this file installed here, so
    // existing browsers stop hanging without the user clearing site data by
    // hand. Note this can only run on a page that actually loaded — a client already
    // hung by the old SW never gets this far, which is why the /sw.js route in
    // backend/main.py serves loopback a self-unregistering worker as well.
    navigator.serviceWorker.getRegistrations()
      .then((regs) => Promise.all(regs.map((reg) => reg.unregister())))
      .then(() => caches.keys())
      .then((keys) => Promise.all(
        keys.filter((k) => k.startsWith('digib00age-shell-')).map((k) => caches.delete(k))
      ))
      .catch(() => {});
  } else {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/sw.js');
    });
  }
}

let deferredInstallPrompt = null;

window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredInstallPrompt = e;
  document.dispatchEvent(new CustomEvent('pwa-installable'));
});

window.addEventListener('appinstalled', () => {
  deferredInstallPrompt = null;
  document.dispatchEvent(new CustomEvent('pwa-installed'));
});

window.triggerPWAInstall = function () {
  if (deferredInstallPrompt) {
    deferredInstallPrompt.prompt();
    deferredInstallPrompt.userChoice.then(() => {
      deferredInstallPrompt = null;
    });
  }
};

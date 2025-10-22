/* MkDocs Material instant-nav helpers + cache-busting for /assets and /publish */
(function () {
  // cache-bust helper aware of GitHub Pages subpath
  function bust(url) {
    try {
      // Use href (includes subpath), not only origin
      var u = new URL(url, window.location.href);
      var stamp = (window.__AP_BUST__ = window.__AP_BUST__ || Date.now());
      if (u.pathname.indexOf("/assets/") !== -1 || u.pathname.indexOf("/publish/") !== -1) {
        u.searchParams.set("v", String(stamp));
      }
      return u.toString();
    } catch (e) { return url; }
  }
  window.bust = bust;

  // Monkey-patch fetch: auto-bust assets/publish
  var _fetch = window.fetch.bind(window);
  window.fetch = function(resource, init) {
    try {
      var url = (typeof resource === "string") ? resource : resource.url;
      if (url && (url.indexOf("/assets/") !== -1 || url.indexOf("/publish/") !== -1)) {
        var b = bust(url);
        if (typeof resource === "string") resource = b;
        else resource = new Request(b, resource);
      }
    } catch (e) {}
    return _fetch(resource, init);
  };

  function onPageReady() {
    // Notify modules to re-init on instant navigation
    window.dispatchEvent(new CustomEvent("ap:page:ready", { detail: { path: location.pathname }}));

    // Re-init if modules exist
    if (typeof window.initSqlLab === "function") window.initSqlLab();
    if (typeof window.initNetworkMap === "function") window.initNetworkMap();
    if (typeof window.initExplorer === "function") window.initExplorer();
    if (typeof window.initDataTables === "function") window.initDataTables();
  }

  // Hook into MkDocs Material's instant navigation
  if (window.document$ && typeof window.document$.subscribe === "function") {
    window.document$.subscribe(onPageReady);
  } else {
    document.addEventListener("DOMContentLoaded", onPageReady);
  }
})();

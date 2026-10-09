/* theme.js — dark mode toggle for the RCK feed dashboard.
   Load in <head> (no defer) so the theme is applied before first paint. */
(function () {
  var KEY = 'rck_theme';
  var root = document.documentElement;

  function saved() {
    try {
      var s = localStorage.getItem(KEY);
      if (s === 'dark' || s === 'light') return s;
    } catch (e) {}
    return null;
  }

  function systemPref() {
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
      ? 'dark' : 'light';
  }

  function apply(theme) {
    root.setAttribute('data-theme', theme);
  }

  // Apply immediately (prevents a white flash on dark-mode reloads)
  apply(saved() || systemPref());

  document.addEventListener('DOMContentLoaded', function () {
    var right = document.querySelector('.header-right');
    if (!right) return;

    // Wrap the existing header-right so the button sits beside it
    var wrap = document.createElement('div');
    wrap.className = 'header-actions';
    right.parentNode.insertBefore(wrap, right);
    wrap.appendChild(right);

    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'theme-toggle';
    wrap.appendChild(btn);

    function refresh() {
      var dark = root.getAttribute('data-theme') === 'dark';
      btn.textContent = dark ? '\u2600\uFE0F' : '\uD83C\uDF19';
      btn.title = dark ? 'Switch to light mode' : 'Switch to dark mode';
      btn.setAttribute('aria-label', btn.title);
    }

    btn.addEventListener('click', function () {
      var next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      apply(next);
      try { localStorage.setItem(KEY, next); } catch (e) {}
      refresh();
    });

    refresh();
  });
})();

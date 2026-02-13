# ~/~ begin <<docs/gong-web-app/utils-javascript.md#libs/utilsJS.py>>[init]

# ~/~ begin <<docs/gong-web-app/utils-javascript.md#block-navigation>>[init]
JS_BLOCK_NAV = """
document.querySelectorAll('a').forEach(link => {
    // Click handler - only disable for same-tab navigation
    link.addEventListener('click', function(event) {
        const willOpenNewTab =
            event.ctrlKey || event.metaKey || event.shiftKey || event.altKey
            || event.button === 1
            || this.getAttribute('target') === '_blank'
            || (event.ctrlKey && event.shiftKey)  // Ctrl+Shift
            || (event.ctrlKey && event.altKey)    // Ctrl+Alt
        ;
        // ONLY disable onbeforeunload for same-tab navigation
        if (willOpenNewTab) {
            console.log('Click intercepted:', this.href, { willOpenNewTab });
            window.onbeforeunload = function() { return "Unsaved changes!";};
            event.preventDefault();  // Prevent default navigation
        } else {
            console.log('Click NOT intercepted:', this.href, { willOpenNewTab });
            window.onbeforeunload = null;  // Disable for this navigation
        }
    });
    // Context menu handler for right-click
    link.addEventListener('contextmenu', function(event) {
            console.log('context menu intercepted:', this.href);
            window.onbeforeunload = function() { return "Unsaved changes!";};
            event.preventDefault();  // Prevent default navigation
    });
});

// disable bfcache: see https://web.dev/articles/bfcache
document.addEventListener('DOMContentLoaded', function() {
  // Disable bfcache immediately
  window.addEventListener('unload', () => {});
  window.addEventListener('beforeunload', () => {});
  window.addEventListener('pageshow', (e) => {
    if (e.persisted) location.reload();
  });
});

console.log("Planning page timer script loaded, onbeforeunload set to warn about unsaved changes.");
window.onbeforeunload = function() { return "Unsaved changes!";};
"""

# ~/~ end
# ~/~ end

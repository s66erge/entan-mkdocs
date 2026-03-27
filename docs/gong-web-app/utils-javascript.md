# JS utilities

```python
#| file: libs/utilsJS.py 
<<block-navigation>>
<<client-timer>>
```

### Block navigation

Except for links/buttons with class='allownavigation'

```python
#| id: block-navigation
JS_BLOCK_NAV = """
document.querySelectorAll('a').forEach(link => {
    // Click handler - only disable for same-tab navigation
    link.addEventListener('click', function(event) {
        if this.classList.contains('allownavigation') {
            window.onbeforeunload = null;
        }
        const willOpenNewTab =
            event.ctrlKey || event.metaKey || event.shiftKey || event.altKey
            || event.button === 1
            || this.getAttribute('target') === '_blank'
            || (event.ctrlKey && event.shiftKey)  // Ctrl+Shift
            || (event.ctrlKey && event.altKey)    // Ctrl+Alt
        ;
        // ONLY disable onbeforeunload for same-tab navigation
        if (willOpenNewTab) {
            //console.log('Click intercepted:', this.href, { willOpenNewTab });
            window.onbeforeunload = function() { return "Unsaved changes!";};
            event.preventDefault();  // Prevent default navigation
        } else {
            //console.log('Click NOT intercepted:', this.href, { willOpenNewTab });
            window.onbeforeunload = null;  // Disable for this navigation
        }
    });
    // Context menu handler for right-click
    link.addEventListener('contextmenu', function(event) {
        //console.log('context menu intercepted:', this.href);
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
```


```python
#| id: client-timer
JS_CLIENT_TIMER = """
function startCountdown(seconds, elementId) {
    const element = document.getElementById(elementId);
    let timeLeft = seconds;

    function updateDisplay() {
        if (timeLeft > 60) {
            const minutes = Math.floor(timeLeft / 60);
            element.textContent = `${minutes} min`;
        } else {
            element.textContent = `${timeLeft} sec`;
        }
    }
    updateDisplay();

    const interval = setInterval(() => {
        timeLeft--;
        updateDisplay();    
        if (timeLeft <= 0) {
            clearInterval(interval);
            window.onbeforeunload = null;
            window.location.href = `${timerRedirect}`;
        }
    }, 1000);
}
// Get starting time from #start-time element and START AUTOMATICALLY
const startSeconds = parseInt(document.getElementById('start-time').textContent);
const timerRedirect = document.getElementById('timer-redirect').textContent;
startCountdown(startSeconds, 'timer');
"""
```

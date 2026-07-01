# UI architecture

The UI architecture is based on **htmx** (https://htmx.org/), a JavaScript library that extends HTML with custom attributes to add dynamic web features directly in HTML without needing large JavaScript frameworks.

### Key Features of htmx:
- Adds attributes like hx-get, hx-post, hx-put, hx-delete, and hx-patch to HTML elements that trigger AJAX requests on certain user actions (click, submit, change).
- Enables partial HTML updates by swapping server responses into parts of the current page DOM, avoiding full page reloads.
- Supports event modifiers, CSS transitions, WebSockets, and Server-Sent Events through HTML attributes.
- Promotes a server-driven application model: the server returns HTML fragments rather than JSON, making UI updates simpler with less client-side JavaScript.

from fasthtml.common import *
from asyncio import sleep
from time import time
import threading

hdrs=(Script(src="https://unpkg.com/htmx-ext-sse@2.2.1/sse.js"),)
app,rt = fast_app(hdrs=hdrs)

TOTAL_SECONDS = 60 * 60  # 60 minutes
timer_start: float | None = None
timer_lock = threading.Lock()

def get_remaining() -> int:
    with timer_lock:
        if timer_start is None:
            return TOTAL_SECONDS
        elapsed = time() - timer_start
        remaining = max(0, TOTAL_SECONDS - int(elapsed))
        return remaining

@rt("/")
def get():
    return Titled(
        "A Countdown Timer",
        Div(
            "Remaining time: ",
            Strong("60:00", id="timer-display"),  # Initial display[file:2]
            hx_ext="sse",  # Enable SSE extension[file:2]
            sse_connect="timer-stream",  # Connect to SSE endpoint[file:2]
            hx_swap="outerHTML",  # Replace the strong tag[file:2]
            sse_swap="timeupdate"  # Listen for 'timeupdate' event[file:2]
        )
    )

async def timer_generator(shutdown_event):
    """Server-side countdown: send every 20 sec, format MM:SS[file:2]"""
    global timer_start
    with timer_lock:
        timer_start = time()
    
    while not shutdown_event.is_set():
        remaining = get_remaining()
        mins, secs = divmod(remaining, 60)
        display = Strong(f"{mins:02d}:{secs:02d}", id="timer-display")
        data = P(display)  # FT component for HTMX swap[file:2]
        yield Strong(f"{mins:02d}:{secs:02d}", id="timer-display"), {"event": "timeupdate"}
        
        # Wait until next 20-min mark or end
        next_update = TOTAL_SECONDS - ((TOTAL_SECONDS - remaining) // 10)
        await sleep(max(1, next_update))  # Avoid busy loop if <1s

@rt("/timer-stream")
async def get():
    return EventStream(timer_generator)  # Async SSE stream[file:2]

serve()
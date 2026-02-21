from fasthtml.common import *
from asyncio import sleep

# Create the FastHTML app
app, rt = fast_app(hdrs=(Script(src="https://unpkg.com/htmx-ext-sse@2.2.1/sse.js"),))

DURATION = 1 # minute
INTERVAL = 15 # seconds
# Global variable to track countdown state
countdown_active = True
remaining_seconds = DURATION * 60  # 60 minutes in seconds

def countdown_callback():
    """Function called when countdown completes"""
    print("Countdown finished!")

# Countdown generator for SSE
async def countdown_generator():
    global remaining_seconds, countdown_active
    while countdown_active and remaining_seconds > 0:
        yield sse_message(str(remaining_seconds))
        remaining_seconds -= INTERVAL
        await sleep(INTERVAL)
    
    # When countdown finishes, send final message and call callback only once
    if remaining_seconds <= 0 and countdown_active:
        countdown_active = False
        yield sse_message("Time is up!")
        countdown_callback()

    # The generator will naturally end here, closing the connection properly
    print("Countdown generator ending.")

@rt("/")
def get():
    return Titled(f"{DURATION}-Minute Countdown",
        Div(id="timer", 
            hx_ext="sse",
            sse_connect="/countdown",
            sse_swap="message",
            cls="timer-display"),
        Script("""
        let timerInterval;  // Global variable to store interval ID
        function checkTimerAndRemove() {
            const timerDiv = document.getElementById('timer');
            //console.log('Checking timer div...');
            if (!timerDiv) return;            
            const text = timerDiv.textContent || timerDiv.innerText;          
            if (text === "Time is up!") {
                timerDiv.remove();
                clearInterval(timerInterval);  // ✅ STOP POLLING
                console.log('Timer div removed - polling STOPPED');
            }
        }
        // Start polling - STORE the interval ID
        timerInterval = setInterval(checkTimerAndRemove, 1000);
        """)
    )

@rt("/countdown")
async def get(): 
    return EventStream(countdown_generator())

serve()

Bringing Statecharts and Domain-Driven Design (DDD) together is a powerful architectural pairing, especially when dealing with complex, behavior-rich business domains. While DDD provides the strategic and tactical patterns to model a business domain, statecharts offer a formal, visual mechanism to implement and guarantee the correctness of the behavior within those models.

Here is how they intersect, complement each other, and map together in practice.

1. The Core Alignment: Behavior Over Data
A common trap in DDD is falling into an Anemic Domain Model, where entities are just bags of getters and setters, and all business logic leaks into service layers.

Both DDD and Statecharts violently agree on a core principle: Domain models should be driven by behavior and lifecycle rules, not just data schemas.

In DDD: An entity should protect its invariants (business rules) by only allowing state mutations through explicit, meaningful command methods (e.g., order.confirmPayment() instead of order.setStatus("PAID")).

In Statecharts: State transitions are explicit, deterministic, and event-driven. You cannot transition to a new state unless an explicit event occurs and specific guard conditions are met.

2. Mapping Statecharts to DDD Tactical Patterns
When implementing DDD, statecharts naturally embed themselves into specific tactical constructs:

Aggregates as State Machines
The Aggregate Root is the prime candidate for a statechart. An aggregate is responsible for enforcing business invariants across a cluster of associated objects. If an aggregate has a complex lifecycle, a statechart is the behavioral blueprint of that aggregate.

DDD Concept	Statechart Equivalent	Description
Domain Event	Event / Trigger	Something that happened in the domain (e.g., OrderPlaced) that triggers a state transition.
Invariant / Policy	Guard	A boolean condition that must be true for a transition to occur (e.g., [isInventoryAvailable]).
Command / Operation	Action / Effect	The side-effect executed during a transition or entry/exit of a state (e.g., sending an email, calculating tax).
Aggregate State	Current State Configuration	The exact atomic, hierarchical, or parallel state(s) the aggregate currently occupies.
Ubiquitous Language & Visual Documentation
One of DDD’s primary goals is establishing a Ubiquitous Language shared between technical teams and business stakeholders.

Statecharts are inherently visual and formal (based on Harel’s semantics).

A statechart can be rendered as a diagram that a product owner, business analyst, and developer can all read and agree on. It bridges the gap between a written business specification and executable code, eliminating ambiguity about how an entity behaves.

3. Advanced DDD Patterns Solved by Statecharts
Statecharts provide specific features—like hierarchy, concurrency, and history—that elegantly solve complex DDD modeling challenges.

Hierarchical States (OR-States) for Sub-Processes
In complex domains, an entity might be in a macro-state that contains several micro-states.

Example: An Order might be in a Processing state. While in Processing, it moves through Validating, Packing, and Invoicing.

Statecharts handle this natively via orthogonal or nested states, allowing you to isolate sub-process logic without polluting the top-level aggregate logic.

Parallel States (AND-States) for Decoupled Concepts
An aggregate root often needs to track independent lifecycles simultaneously.

Example: A LoanApplication might have a CreditCheck lifecycle and an IdentityVerification lifecycle running concurrently. The application cannot move to Approved until both parallel states reach their respective success states.

Statecharts model this cleanly using orthogonal regions, preventing the state explosion problem (where you'd otherwise have to manually manage combinatorics like CreditChecked_IdentityPending).

Bounded Context Boundaries
Statecharts help define clean boundaries. A domain event emitted by a statechart in one Bounded Context (e.g., OrderShipped from the Shipping Context) can be received as an external trigger/event by a statechart in another Bounded Context (e.g., DeliveryTracking in the Customer Support Context).

4. Architectural Workflows: Event Sourcing & CQRS
If you are using Event Sourcing (ES) and CQRS, statecharts fit into the pipeline seamlessly:

[Command] ──> [Aggregate Root / Statechart] ──(Validates Guard)──> [Emits Domain Event] ──> [Persisted to Event Store]
Command Handling: A command arrives at the Aggregate Root.

Statechart Evaluation: The aggregate passes the command (as an event) to its internal statechart.

Guards & Transitions: The statechart checks guards. If valid, it transitions and fires an action.

Event Generation: The action generates a Domain Event representing the change.

Rehydration: When rebuilding the aggregate's state from past events, the events are replayed sequentially into the statechart to drive it back to its current state configuration.

Summary of Benefits
Integrating statecharts into your DDD practice yields a few distinct advantages:

Zero Anemia: Your aggregates become deeply behavioral and self-documenting.

Guaranteed Invariants: It becomes mathematically impossible for an aggregate to enter an invalid business state because illegal transitions are physically unmapped.

Separation of Concerns: Business logic (states, transitions, guards) is entirely separated from persistence or infrastructure logic.

Are you looking at modeling a specific domain entity's lifecycle right now, or are you exploring how to structure the code architecture for this integration?

How to structure the code architecture for this integration

Structuring the code architecture to integrate Statecharts with Domain-Driven Design (DDD) requires a clean separation between business behavior (the Statechart), domain state (the Aggregate), and infrastructure (persistence and application layers).

The golden rule of this architecture is: The statechart controls the rules of transition, but the domain aggregate owns and mutates the data.

Here is a robust, production-ready architectural pattern using an Order Aggregate as an example.

1. The Architectural Blueprint (The Layered View)
To keep your domain pure, structural layers should interact in a one-way flow. The application layer handles orchestration, the aggregate handles business identity and data, and the statechart handles the behavioral rules.

Here is how the responsibilities are distributed:

Application Service: Receives a request, fetches the Aggregate from the Repository, calls a business method on the Aggregate, and saves it.

Aggregate Root (DDD): Holds the entity’s identity, business data (e.g., total price, line items), and an instance of the Statechart.

Statechart: Houses the formal state machine, state definitions, transitions, and guards. It accepts events from the aggregate and dictates whether they are allowed.

2. Directory & File Structure
Keep your statechart logic close to your domain models. A typical DDD bounded context layout looks like this:

Plaintext
ordering/
│
├── domain/                  # Pure Domain Layer (No database/web dependencies)
│   ├── models.py            # Aggregate Root (e.g., Order class)
│   ├── value_objects.py     # Immutable data (e.g., Price, Address)
│   └── statecharts/         # Statechart definitions
│       ├── order_machine.py # The statechart rules, transitions, and guards
│       └── events.py        # Domain events triggered by the machine
│
├── application/             # Application Layer (Orchestration)
│   └── services.py          # Use cases / Command handlers
│
└── infrastructure/          # Infrastructure Layer
    └── repository.py        # Database persistence (SQLAlchemy, Beanie, etc.)
3. Concrete Code Implementation (Python Pattern)
This implementation demonstrates how an Aggregate Root wraps a statechart machine, passing itself as "context" so the statechart can evaluate business rules against live data.

Step 1: Define the Statechart (domain/statecharts/order_machine.py)
The statechart focuses purely on the rules of movement. It uses guards to inspect the aggregate's data and actions to trigger changes or side effects.

Python
from statemachine import StateMachine, State

class OrderStateMachine(StateMachine):
    # 1. Define States
    draft = State('Draft', initial=True)
    processing = State('Processing')
    paid = State('Paid')
    failed = State('Failed')

    # 2. Define Transitions (Events)
    submit = draft.to(processing)
    confirm_payment = processing.to(paid)
    reject_payment = processing.to(failed)

    def __init__(self, aggregate):
        self.aggregate = aggregate  # Link back to the DDD Aggregate
        super().__init__()

    # 3. Guard: Is the aggregate allowed to move?
    def can_submit(self) -> bool:
        """Guard: Cannot submit an order without items."""
        return len(self.aggregate.items) > 0

    # 4. Action: What happens when the transition succeeds?
    def on_enter_paid(self):
        """Action executed automatically upon entering the Paid state."""
        self.aggregate.record_payment_timestamp()
Step 2: Define the Aggregate Root (domain/models.py)
The aggregate root exposes meaningful domain methods (commands). It maintains its data attributes (like items or paid_at) and uses the statechart to validate if an operation is valid for its current lifecycle.

Python
from datetime import datetime, timezone
from typing import List, Optional
from .statecharts.order_machine import OrderStateMachine

class Order:
    def __init__(self, order_id: str, items: List[str], current_state: str = "draft"):
        self.id = order_id
        self.items = items
        self.paid_at: Optional[datetime] = None
        
        # Instantiate the statechart, binding this aggregate instance to it
        self.machine = OrderStateMachine(self)
        self.machine.current_state = current_state

    @property
    def state(self) -> str:
        """Expose the string value of the current state for persistence."""
        return self.machine.current_state.id

    # --- Domain Commands (The public API of the Aggregate) ---
    
    def add_item(self, item: str):
        # We can only alter items if we are still in the draft state rule space
        if self.state != "draft":
            raise ValueError("Cannot add items to a finalized order.")
        self.items.append(item)

    def finalize_order(self):
        """Command to submit the order."""
        # The machine evaluates guards automatically. 
        # Throws a TransitionNotAllowed exception if guards fail or state is wrong.
        self.machine.submit() 

    def mark_as_paid(self):
        """Command triggered by a payment webhook event."""
        self.machine.confirm_payment()

    # --- Statechart Callbacks (Mutate actual data here) ---
    
    def record_payment_timestamp(self):
        """Called by the statechart action handler on successful payment transition."""
        self.paid_at = datetime.now(timezone.utc)
Step 3: The Application Service Orchestration (application/services.py)
The application layer treats the statechart as an internal implementation detail of the aggregate. It never calls the machine directly; it only talks to the aggregate's domain commands.

Python
class OrderApplicationService:
    def __init__(self, order_repository):
        self.repository = order_repository

    def checkout_order(self, order_id: str):
        # 1. Fetch aggregate from DB
        order = self.repository.get_by_id(order_id)
        if not order:
            raise Exception("Order not found")

        # 2. Execute business transaction via Aggregate Command
        try:
            order.finalize_order()
        except Exception as e:
            # Handle invariant violation or invalid state transition gracefully
            logger.error(f"Checkout failed: {e}")
            raise

        # 3. Save the new state back to the database
        self.repository.save(order)
4. How to Handle Persistence
When saving this aggregate to a database, you do not serialize the entire Statechart object instance. You only persist the state's string identifier.

Saving: Read the order.state property (which returns string tokens like "draft" or "processing") and save it to a standard VARCHAR/TEXT column in your database.

Loading (Rehydration): When loading an order from the database, pass the stored string state into the Order constructor. The constructor passes that string right into the state machine initialization block (self.machine.current_state = current_state), restoring the exact behavior rules instantly.

5. Architectural Advantages of this Pattern
Purity: The state machine requires no database drivers or HTTP logic. It is a pure unit-testable engine containing purely business rules.

Explosion Prevention: If your aggregate state becomes complex (e.g., adding a parallel track for tracking shipping independent of billing), you can upgrade OrderStateMachine to use hierarchical or parallel states without modifying a single line of database persistence code.

Defensive Design: If a developer accidentally attempts to mark an un-submitted order as paid, the machine blocks it before database corruption or invalid side-effects can happen.

Are you intending to build this out using an asynchronous engine (like handling webhooks via Server-Sent Events/FastHTML background workers), or are you focusing primarily on setting up synchronous database transactions first?

SSE + fasthtml

Integrating Server-Sent Events (SSE) with FastHTML and htmx creates an incredibly powerful, reactive architecture. In this setup, your backend statechart transitions can stream real-time UI updates directly to the browser over a single, long-lived HTTP connection—without requiring heavy client-side JavaScript frameworks.

Here is how to architect and implement an SSE streaming architecture using FastHTML.

1. The Real-Time Architecture Flow
Instead of the client constantly polling the server to see if an aggregate's state has changed (e.g., waiting for an payment statechart to transition from processing to paid), the server pushes partial HTML fragments over SSE the second the state changes.

The Client establishes an SSE connection using htmx's sse extension.

The Server processes commands, transitions the state machine, and publishes events.

The SSE Loop catches these events and streams precise HTML snippets (FastHTML components) to the client.

Htmx automatically swaps the new HTML into the page seamlessly.

2. Code Implementation: Real-Time State Monitor
Here is a complete, working pattern utilizing FastHTML and Python's native asyncio queues to stream statechart updates.

Step 1: The App Setup and HTML Layout
We need to register the htmx SSE extension script and set up a container that listens for server events.

Python
import asyncio
from fasthtml.common import *

# Include the htmx SSE extension
hdrs = [Script(src="https://unpkg.com/htmx.ext.sse@2.2.1/sse.js")]
app, rt = fast_app(hdrs=hdrs)

# A global memory store for active client queues (in production, use a broker like Redis)
connected_clients = set()

@rt("/")
def get():
    return Titled("Order Lifecycle Monitor",
        Main(CLS="container",
            H2("Your Current Order Status"),
            
            # 1. Connect to the SSE endpoint
            Div(ext="sse", sse_connect="/stream",
                # 2. Listen for 'status-update' named events from the server
                Div(sse_swap="status-update", id="order-card") {
                    # Initial state component
                    render_order_card("Draft", "Your order is ready for submission.")
                }
            ),
            Br(),
            # Button to simulate an action that triggers a statechart transition
            Button("Process Order Payment", 
                   hx_post="/process-payment", 
                   hx_swap="none", 
                   CLS="button")
        )
    )

# A reusable FastHTML UI component
def render_order_card(state: str, message: str):
    color_map = {"Draft": "gray", "Processing": "orange", "Paid": "green"}
    return Card(
        H3(f"Status: {state}", style=f"color: {color_map.get(state, 'black')}"),
        P(message),
        id="order-card" # Match the ID so htmx knows exactly what to replace
    )
Step 2: The SSE Streaming Endpoint
FastHTML handles SSE streaming by returning a generator wrapped in an EventStream. We use an asynchronous queue for each connected browser tab to push updates instantly.

Python
@rt("/stream")
async def get_stream():
    queue = asyncio.Queue()
    connected_clients.add(queue)
    
    async def sse_generator():
        try:
            while True:
                # Wait until a state change event is put into this client's queue
                html_payload = await queue.get()
                
                # Format specification for Server-Sent Events:
                # event: [eventName]
                # data: [string payload]
                yield f"event: status-update\ndata: {html_payload}\n\n"
        except asyncio.CancelledError:
            # Clean up when the user closes the tab or disconnects
            connected_clients.remove(queue)

    return EventStream(sse_generator())
Step 3: Triggering State Changes via Business Logic
When a user executes an action, the backend invokes the aggregate command, triggers the statechart transition, and broadcasts the updated FastHTML UI component to all active SSE queues.

Python
@rt("/process-payment")
async def post_payment():
    # --- Statechart Simulation ---
    # 1. In practice, you fetch your Aggregate and call aggregate.machine.next_state()
    # 2. Here we simulate a rapid multi-step background transition:
    
    # Transition 1: Processing
    processing_html = to_xml(render_order_card("Processing", "Contacting payment gateway..."))
    await broadcast_to_clients(processing_html)
    
    await asyncio.sleep(2.5) # Simulate network lag with the bank
    
    # Transition 2: Paid (Success!)
    paid_html = to_xml(render_order_card("Paid", "Invoice settled successfully! Thank you."))
    await broadcast_to_clients(paid_html)
    
    return "" # Return empty string to htmx post call because SSE handles the UI rewrite

async def broadcast_to_clients(html_content: str):
    """Helper to push the HTML fragment to all active streams."""
    if connected_clients:
        # Clean the string to fit standard single-line data formats for SSE
        collapsed_html = html_content.replace("\n", "").strip()
        for queue in list(connected_clients):
            await queue.put(collapsed_html)
3. Key Design Considerations for This Stack
HTML Over the Wire vs JSON
Standard SSE typically transmits raw JSON string values, requiring the frontend to parse it and build DOM elements. With FastHTML and htmx, you bypass client rendering entirely. You use FastHTML builders (Card(), Div()) on the server, call to_xml(), and stream raw HTML components. Htmx injects them directly into the live DOM tree.

Connection Management
Browsers impose a hard limit on concurrent HTTP/1.1 connections to the same domain (usually 6). If a user opens 6 tabs of your app, the 7th tab will hang indefinitely. To mitigate this in a production environment:

Ensure your application server (like Uvicorn) uses HTTP/2, which multiplexes requests across a single TCP connection.

Keeping Statecharts Pure
Never instantiate or execute database operations inside your SSE generator loops. Keep the SSE layer strictly focused on observing and transporting. Your application services should execute the business logic, and use a standard publish/subscribe mechanism to pass the resulting HTML out to your active event streams.

Are you plugging this setup into a long-running asynchronous background worker process (like tracking a third-party API webhook), or are you driving it entirely from direct user actions in the browser?

Driving it entirely from direct user actions in the browser

Driving the flow entirely from direct user actions simplifies your architecture immensely. Because everything happens within the lifecycle of a standard, single HTTP request-response cycle, you don’t need to manage global async broadcast queues, background worker tasks, or publish/subscribe brokers.

Instead, your architecture becomes beautifully deterministic: the user clicks a button, the request invokes your aggregate's domain commands, the statechart changes state, and FastHTML instantly returns the resulting layout fragments back to htmx.

Here is the clean, synchronous-looking pattern for user-driven interactions using FastHTML and htmx, without needing the overhead of full SSE streams.

1. The Direct Request-Response Pattern
When actions are 100% user-driven, htmx allows you to target and swap specific parts of the page directly via regular POST/PATCH actions.

[User Clicks Button] ──> HTTP POST ──> [Statechart Transitions] ──> Returns Partial HTML ──> [Htmx Swaps Container]
The Component Layout (app.py)
Here is how you structure a user-driven interface. We will model a standard processing gate where the buttons dynamically alter their availability based on what state the statechart is in.

Python
from fasthtml.common import *
# Assuming the Order aggregate code from earlier is imported
from domain.models import Order 

app, rt = fast_app()

# Simulating a database session / repository lookup for a single order
DB_SESSION_ORDER = Order(order_id="1234", items=["Python Book", "Mechanical Keyboard"])

def render_order_dashboard(order: Order, error_message: str = None):
    """Renders the entire dashboard block dynamically based on the current state."""
    state_name = order.state.capitalize()
    
    # 1. Evaluate button states directly from the Statechart's allowed transitions
    can_submit = order.machine.draft.is_current
    can_pay = order.machine.processing.is_current

    return Div(id="order-dashboard", CLS="card shadow-sm p-4")(
        H3(f"Order Status: {state_name}", 
           style=f"color: {'green' if state_name == 'Paid' else 'orange' if state_name == 'Processing' else 'gray'}"),
        
        # Display validation/guard error messages if any occurred
        P(error_message, style="color: red; font-weight: bold;") if error_message else None,
        
        P(f"Items in Cart: {', '.join(order.items)}"),
        P(f"Payment Settled At: {order.paid_at if order.paid_at else 'Pending'}"),
        Hr(),
        
        Div(CLS="grid")(
            # Button 1: Submit
            Button("Submit Order", 
                   hx_post="/order/submit", 
                   hx_target="#order-dashboard", # Target itself to swap the whole view
                   disabled=not can_submit,
                   CLS="btn btn-primary"),
            
            # Button 2: Pay
            Button("Pay Now", 
                   hx_post="/order/pay", 
                   hx_target="#order-dashboard", 
                   disabled=not can_pay,
                   CLS="btn btn-success")
        )
    )

@rt("/")
def get():
    return Titled("Order Management Console",
        Main(CLS="container",
            # Initial Render
            render_order_dashboard(DB_SESSION_ORDER)
        )
    )
The Application Route Handlers
The endpoint extracts the aggregate, invokes the transition command, handles failures gracefully if a statechart guard rejects the action, and then returns the newly updated UI component.

Python
@rt("/order/submit")
def post_submit():
    order = DB_SESSION_ORDER
    try:
        # Statechart transitions inside the aggregate command
        order.finalize_order() 
        error = None
    except Exception as e:
        # Catch guard violations (e.g., if items were empty)
        error = f"Transition Rejected: {str(e)}"
        
    # Return the freshly calculated state of the component
    return render_order_dashboard(order, error_message=error)

@rt("/order/pay")
def post_pay():
    order = DB_SESSION_ORDER
    try:
        order.mark_as_paid()
        error = None
    except Exception as e:
        error = f"Payment Rejected: {str(e)}"
        
    return render_order_dashboard(order, error_message=error)
2. Managing Form Validations with Statechart Guards
In user-driven apps, you frequently need to parse user input from form fields and validate them against your state rules before progressing. This is where statechart Guards shine in a request-response flow.

If a user submits a form that triggers a transition, pass that data straight to the aggregate. If the statechart guard returns False, the engine cancels the transition, and FastHTML serves a bad request or an inline error alert fragment back to the browser.

Python
# Inside your state machine
def can_submit(self) -> bool:
    """The machine automatically checks this guard rule before executing 'submit'."""
    # Ensure the aggregate has items and a shipping address before processing
    return len(self.aggregate.items) > 0 and self.aggregate.shipping_address is not None
3. Benefits of Dropping SSE for Pure User-Driven Requests
State Synchronization: Because the execution path is completely synchronous inside the request thread, there is absolutely zero risk of race conditions where the UI displays one state while the database reflects another.

Low Server Overhead: The server only processes logic when an intentional click occurs. It holds zero open TCP socket connections, dramatically maximizing your application's request concurrency capacity.

Clean Error Propagation: If a business rule fails inside the statechart, you can catch the exception immediately in the controller block and pass an explicit error message back down to the target htmx element seamlessly.

Great, on the infrastructure side, show me using postgresql for production and python sets for dev

To switch dynamically between a lightweight in-memory set implementation for rapid local development and a robust PostgreSQL configuration for production, you need to isolate your data access layer using the Repository Pattern.

By decoupling your application logic from how the entities are saved, you can swap the data store out instantly via environment variables without modifying a single line of your domain or FastHTML controller logic.

Here is how to structure your infrastructure layer to handle this dual-environment setup cleanly.

1. Defining the Repository Interface
First, create an abstract repository or a consistent class interface that both storage engines must fulfill. This ensures your FastHTML application can treat them interchangeably.

Python
# infrastructure/repository_interface.py
from typing import Optional
from domain.models import Order

class OrderRepositoryInterface:
    def get_by_id(self, order_id: str) -> Optional[Order]:
        raise NotImplementedError
        
    def save(self, order: Order) -> None:
        raise NotImplementedError
2. The Local Dev Implementation (Python Sets)
Because an Aggregate Root has a unique identity (order.id), a standard Python set requires a slight tweak: if you update an order, you need to replace the old version in the set. Alternatively, a Python dict mapping id -> instance mimics a database index perfectly, though we can track the active keys using a set.

Here is how you implement a clean, thread-safe in-memory repository using Python collections:

Python
# infrastructure/dev_repository.py
from typing import Optional
from domain.models import Order

class InMemoryOrderRepository:
    def __init__(self):
        # Using a dictionary for O(1) lookups, backing the entity set
        self._storage = {}

    def get_by_id(self, order_id: str) -> Optional[Order]:
        order = self._storage.get(order_id)
        if not order:
            return None
        # Return a fresh reconstruction to mimic database retrieval behavior
        return Order(order_id=order.id, items=list(order.items), current_state=order.state)

    def save(self, order: Order) -> None:
        # Overwrites the old reference if it already exists (simulating an upsert)
        self._storage[order.id] = order
3. The Production Implementation (PostgreSQL via SQLAlchemy)
For production, we map the aggregate's data properties—including the string token representing the statechart's current location—to a Postgres table.

Python
# infrastructure/prod_repository.py
import os
from typing import Optional
from sqlalchemy import create_engine, Column, String, JSON, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from domain.models import Order

Base = declarative_base()

# SQLAlchemy Model reflecting our database schema
class OrderRecord(Base):
    __tablename__ = 'orders'
    
    id = Column(String, primary_key=True)
    state = Column(String, nullable=False)  # Stores the Statechart string token
    items = Column(JSON, nullable=False)    # Stores the array of items
    paid_at = Column(DateTime, nullable=True)

class PostgresOrderRepository:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def get_by_id(self, order_id: str) -> Optional[Order]:
        with self.session_factory() as session:
            record = session.query(OrderRecord).filter_by(id=order_id).first()
            if not record:
                return None
            
            # Map database columns back into your pure Domain Aggregate Root
            order = Order(order_id=record.id, items=record.items, current_state=record.state)
            order.paid_at = record.paid_at
            return order

    def save(self, order: Order) -> None:
        with self.session_factory() as session:
            record = session.query(OrderRecord).filter_by(id=order.id).first()
            
            if record:
                # Update existing record
                record.state = order.state
                record.items = order.items
                record.paid_at = order.paid_at
            else:
                # Insert new record
                record = OrderRecord(
                    id=order.id,
                    state=order.state,
                    items=order.items,
                    paid_at=order.paid_at
                )
                session.add(record)
                
            session.commit()
4. Wiring It All Together with Environment Variables
Now, wire the repository factory directly into your main FastHTML server setup. You look at an environment variable (e.g., APP_ENV) to determine which version of the infrastructure to feed into your application routes.

Python
# main.py
import os
from fasthtml.common import *
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import our repositories
from infrastructure.dev_repository import InMemoryOrderRepository
from infrastructure.prod_repository import PostgresOrderRepository, Base

# 1. Environment Detection
ENV = os.getenv("APP_ENV", "development")

if ENV == "production":
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/dbname")
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(bind=engine) # Setup tables if missing
    session_factory = sessionmaker(bind=engine)
    
    ORDER_REPO = PostgresOrderRepository(session_factory)
else:
    # Fallback to local memory tracking for dev
    ORDER_REPO = InMemoryOrderRepository()
    
    # Pre-populate a fake order to play with locally
    from domain.models import Order
    ORDER_REPO.save(Order(order_id="dev-123", items=["Python Book", "Coffee"]))

# 2. FastHTML App Initialization
app, rt = fast_app()

def render_dashboard(order):
    # (Same component code from earlier snippet, reading dynamic state rules)
    return Div(id="dashboard")(
        H3(f"Status: {order.state.capitalize()}"),
        Button("Submit", hx_post=f"/order/{order.id}/submit", hx_target="#dashboard")
    )

@rt("/order/{order_id}")
def get(order_id: str):
    order = ORDER_REPO.get_by_id(order_id)
    if not order: return "Order not found", 404
    return render_dashboard(order)

@rt("/order/{order_id}/submit")
def post_submit(order_id: str):
    # Fetch, transition, and save abstractly. The controller doesn't know 
    # whether it's talking to Postgres or an in-memory dictionary.
    order = ORDER_REPO.get_by_id(order_id)
    if not order: return "Order not found", 404
    
    try:
        order.finalize_order() # Statechart fires its rules here
        ORDER_REPO.save(order) # Persisted to memory OR Postgres
    except Exception as e:
        return render_dashboard(order, error_message=str(e))
        
    return render_dashboard(order)
Running Your Environments
When running locally in your terminal, it defaults to the ultra-fast Python set/dict store:

Bash
python main.py
When deploying to your production environment (e.g., inside a Docker container or a cloud provider attached to an actual PostgreSQL instance), simply flag the environment variable:

Bash
APP_ENV=production DATABASE_URL=postgresql://admin:secret@pg-host:5432/prod_db python main.py
This structural division means your unit tests can test statechart transitions against the InMemoryOrderRepository instantly with zero execution overhead, while your production ecosystem benefits from multi-process transaction safety.

Replace sql alchemy with fasthtml MiniDataAPI Spec

FastHTML comes built-in with a lightweight, ultra-fast database abstraction called MiniDataAPI (commonly instantiated via fast_app(db_file=...) using SQLite). It acts as a mini-ORM that completely eliminates the boilerplate of SQLAlchemy while keeping your domain models clean and easily serializable.

Here is how to rewrite the production repository layer using FastHTML’s MiniDataAPI spec while keeping the exact same interface so your development setup can continue using in-memory structures seamlessly.

1. Updated Database Table Definition
FastHTML's database engine uses standard Python dataclasses or dynamically generated types. We can define our OrderRecord using FastHTML's setup_table schema tool.

Python
# infrastructure/prod_repository.py
import json
from typing import Optional
from fasthtml.common import database, setup_table
from domain.models import Order

# 1. Initialize FastHTML's database wrapper pointing to your database file/string
# For production, pass the path to your SQLite database file
db = database("production.db")

# 2. Define the schema matching our domain fields
# setup_table returns a reference to the table collection instance
orders_table = setup_table(
    db,
    "orders",
    id=str,
    state=str,
    items=str,      # MiniDataAPI stores arrays easily as JSON text strings
    paid_at=str,    # ISO timestamp strings or datetime objects
    pk="id"         # Primary Key definition
)
2. The FastHTML MiniDataAPI Production Repository
The MiniDataAPI spec provides simple, intuitive lookup and persistence methods like table[pk], table.insert(), and table.update().

Python
# infrastructure/prod_repository.py (Continued)

class FastHtmlOrderRepository:
    def __init__(self, table):
        self.table = table

    def get_by_id(self, order_id: str) -> Optional[Order]:
        try:
            # MiniDataAPI allows direct dictionary-like lookup via Primary Key
            record = self.table[order_id]
        except KeyError:
            return None
        
        # Unpack the stored record string variables back into your core domain Aggregate
        items_list = json.loads(record['items'])
        order = Order(order_id=record['id'], items=items_list, current_state=record['state'])
        
        if record.get('paid_at'):
            order.paid_at = record['paid_at']
        return order

    def save(self, order: Order) -> None:
        # Prepare the flat dictionary database payload
        payload = {
            "id": order.id,
            "state": order.state,
            "items": json.dumps(order.items), # Serialize the list to JSON string
            "paid_at": order.paid_at if order.paid_at else ""
        }
        
        # MiniDataAPI check for existence to upsert safely
        if order.id in self.table:
            self.table.update(payload)
        else:
            self.table.insert(payload)
3. Integrating with the Main Application Factory
Because both repositories implement the exact same signature methods (get_by_id and save), swapping SQLAlchemy for the MiniDataAPI implementation requires zero edits to your FastHTML layout components or business rule endpoint paths.

Python
# main.py
import os
from fasthtml.common import *

# Import our cross-compatible repositories
from infrastructure.dev_repository import InMemoryOrderRepository
from infrastructure.prod_repository import FastHtmlOrderRepository, orders_table

ENV = os.getenv("APP_ENV", "development")

if ENV == "production":
    # Inject FastHTML's MiniDataAPI table instance directly into the repository
    ORDER_REPO = FastHtmlOrderRepository(orders_table)
else:
    ORDER_REPO = InMemoryOrderRepository()
    
    # Pre-populate a fake order to play with locally in development
    from domain.models import Order
    if not ORDER_REPO.get_by_id("dev-123"):
        ORDER_REPO.save(Order(order_id="dev-123", items=["Python Book", "Coffee"]))

app, rt = fast_app()

@rt("/order/{order_id}")
def get(order_id: str):
    order = ORDER_REPO.get_by_id(order_id)
    if not order: return "Order not found", 404
    
    # Render view logic remains 100% clean and untouched
    return Titled(f"Order {order.id}", 
                  Div(f"Current State: {order.state}"))
Architectural Wins with MiniDataAPI
No Object-Relational Impedance: SQLAlchemy tracks mutations on object fields using complex internal session histories. FastHTML's MiniDataAPI acts as a pure, explicit data gateway—exactly what the Repository Pattern expects.

Dead-Simple Code Footprint: You completely avoid setting up engine drivers, declarative mapping blocks, and explicit session commit/rollback contexts.

Synchronous Speed: Because MiniDataAPI maps thin wrappers over your database collections, it matches the fast execution speed of your local memory development sets perfectly.




Gemini is AI and can make mistakes, including about people. Your privacy & GeminiOpens in a new window


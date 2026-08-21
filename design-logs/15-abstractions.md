Yes. **Intent: runtime orchestration / algebraic decomposition of your event-driven kernel.**

Looking at your code, I would make one fairly significant change:

> **Your managers should be pure state-transition functions. Your runtime should own the queues/bus and coordinate execution.**

Right now `TurnManager.apply()` is doing two jobs:

1. computing the next `TurnLoopState`
2. performing an event-bus effect

That is the boundary I would clean up first.

---

# 1. The abstraction hierarchy I would use

For your style, you really only need about **five core abstractions**:

$$
\boxed{
\mathrm{Runtime}
\rightarrow
\mathrm{Dispatcher}
\rightarrow
\mathrm{Manager}
\rightarrow
\mathrm{State}
}
$$

with the two effect channels:

$$
\boxed{
\mathrm{CommandQueue}
\qquad
\mathrm{EventBus}
}
$$

Concretely:

```text
ApplicationRuntime
    │
    ├── CommandQueue
    ├── EventBus
    └── SessionRuntime
            │
            ├── SessionManager
            ├── TurnManager
            └── ...
```

But the **managers don't own any of those things**.

---

# 2. Your `TurnManager` should become pure

Currently:

```python
TurnManager.apply(
    turn_loop_state,
    event_bus_state,
    event,
)
```

is suspicious because `event_bus_state` isn't actually part of the mathematical state transition of the turn loop.

Your turn state transition is really:

$$
\delta_T :
T \times E_T
\rightarrow
T + \mathrm{IllegalTransition}
$$

For example:

$$
\delta_T(\mathrm{Idle},\mathrm{Start}(r))
=========================================

\mathrm{Running}(r)
$$

and:

$$
\delta_T(\mathrm{Running},\mathrm{CompletionReceived}(r,None))
==============================================================

\mathrm{Idle}
$$

That's it.

So:

```python
class TurnManager:

    @staticmethod
    def apply(
        state: TurnLoopState,
        event: TurnLoopEvent,
    ) -> Result[TurnLoopState, IllegalTransition]:

        match event, state:
            case Start(request_id=rid), Idle():
                return Ok(Running(request_id=rid))

            case CompletionReceived(request_id=rid, tool_call_id=tc), Running() if tc is not None:
                return Ok(
                    AwaitingTool(
                        request_id=rid,
                        pending_tool_call=tc,
                    )
                )

            case CompletionReceived(), Running():
                return Ok(Idle())

            case ToolResultReceived(request_id=rid), AwaitingTool():
                return Ok(Running(request_id=rid))

            case Failed(reason=r, recoverable=rec), _:
                return Ok(Error(reason=r, recoverable=rec))

            case Recover(), Error(recoverable=True):
                return Ok(Idle())

            case _:
                return Err(
                    IllegalTransition(
                        f"{type(event).__name__} illegal from {type(state).__name__}"
                    )
                )
```

Now your manager is genuinely:

$$
\boxed{
\mathrm{TurnManager}
:
T\times E_T\rightarrow T+Error
}
$$

No event bus.

No queue.

No runtime.

No side effects.

That is a **state machine algebra**.

---

# 3. Then where does `TurnStateChanged` go?

This is where your runtime comes in.

The manager gives:

$$
T_0
\xrightarrow{e}
T_1
$$

The runtime can derive:

$$
\mathrm{TurnStateChanged}(T_0,T_1)
$$

and publish it.

So:

$$
\boxed{
\begin{aligned}
T_1 &= \delta_T(T_0,e)\
E_{\mathrm{state}} &= \mathrm{TurnStateChanged}(T_0,T_1)
\end{aligned}
}
$$

This means your state-transition logic remains pure while your runtime handles observation.

I'd actually make this a small generic concept:

```python
def transition(
    manager,
    state,
    event,
):
    result = manager.apply(state, event)

    match result:
        case Ok(new_state):
            return new_state, (
                StateChanged(
                    previous=state,
                    current=new_state,
                ),
            )

        case Err(error):
            return state, (
                TransitionRejected(error),
            )
```

You don't necessarily need this exact abstraction yet, but that's the semantic separation.

---

# 4. Your `Session` is currently trying to be both manager and runtime

This is the second major thing I'd change.

You currently have:

```python
Session.apply(state, event)
```

and:

```python
Session.run(state, events)
```

But those have fundamentally different meanings.

### `apply`

is a **state transition function**:

$$
\mathrm{SessionManager}
:
S\times E\rightarrow S
$$

### `run`

is an **orchestrator/interpreter**:

$$
\mathrm{SessionRuntime}
:
S\times E^*
\rightarrow
S
$$

Those should not be the same abstraction.

I'd split them.

---

# 5. `SessionManager`

This is the pure coordinator of domain state.

Your state is roughly:

$$
S_{\mathrm{session}}
====================

S_{\mathrm{command}}
\times
S_{\mathrm{event}}
\times
S_{\mathrm{turn}}
$$

and events form:

$$
E =
E_C + E_B + E_T
$$

where $+$ is the disjoint union/sum type.

Then:

$$
\delta_S:
S_{\mathrm{session}}\times E
\rightarrow
S_{\mathrm{session}}
$$

Your current `Session.apply()` is basically this.

I'd keep that concept.

But don't let it directly execute infrastructure.

---

# 6. Then create `SessionRuntime`

This is the abstraction you are currently missing.

It owns the **coordination loop**, not the domain state.

Conceptually:

```python
class SessionRuntime:

    def __init__(
        self,
        command_queue,
        event_bus,
    ):
        self.command_queue = command_queue
        self.event_bus = event_bus

    def run(self, state):
        ...
```

But given your preference for functional code, I would **not necessarily make this a mutable class**.

Instead:

```python
def run_session(
    runtime: Runtime,
    state: SessionState,
) -> SessionState:
    ...
```

where:

```python
@dataclass(frozen=True)
class Runtime:
    command_queue: CommandQueueCapability
    event_bus: EventBusCapability
```

Then:

$$
R =
C_Q\times C_B
$$

and:

$$
\mathrm{runSession}:R\times S\rightarrow S
$$

---

# 7. The runtime's job is orchestration

This is the crucial distinction.

Your managers answer:

> "Given state $S$ and event $e$, what is the next state?"

Your runtime answers:

> "What should I execute next, where does the resulting event go, and who receives it?"

So:

$$
\boxed{
\text{Manager} = \text{semantics}
}
$$

$$
\boxed{
\text{Runtime} = \text{orchestration}
}
$$

$$
\boxed{
\text{Queue/Bus} = \text{transport}
}
$$

That is the architecture I think you're converging toward.

---

# 8. Your queues should be outside the `SessionState`

This is another important correction.

I would distinguish:

$$
S_{\mathrm{session}}
$$

from:

$$
R_{\mathrm{runtime}}
$$

Don't make:

```python
SessionState(
    command_queue_state=...,
    event_bus_state=...,
    turn_loop_state=...,
)
```

unless those queue states are genuinely part of your **domain state**.

Instead:

$$
S_{\mathrm{session}}
====================

S_{\mathrm{turn}}
\times
S_{\mathrm{conversation}}
\times
S_{\mathrm{session-domain}}
$$

while:

$$
R_{\mathrm{runtime}}
====================

Q_C\times B_E\times \cdots
$$

The distinction is:

> **State describes what the session is. Runtime resources describe how the session executes.**

That's a very important architectural boundary.

---

# 9. So your types become roughly

I'd aim for:

```python
@dataclass(frozen=True)
class SessionState:
    turn_loop: TurnLoopState
    # conversation state
    # other domain state


@dataclass(frozen=True)
class Runtime:
    command_queue: CommandQueue
    event_bus: EventBus
```

Then pure managers:

```python
class TurnManager:
    @staticmethod
    def apply(
        state: TurnLoopState,
        event: TurnLoopEvent,
    ) -> Result[TurnLoopState, IllegalTransition]:
        ...
```

```python
class SessionManager:
    @staticmethod
    def apply(
        state: SessionState,
        event: Event,
    ) -> Result[SessionState, IllegalTransition]:
        ...
```

And finally:

```python
def run_session(
    runtime: Runtime,
    state: SessionState,
) -> SessionState:
    ...
```

---

# 10. But I would make one more abstraction: `Dispatcher`

Your `Session.apply()` currently has:

```python
match event:
    case CommandQueueEvent():
        ...
    case EventBusEvent():
        ...
    case TurnLoopEvent():
        ...
```

This is essentially a **dispatcher**.

You can make that role explicit.

$$
D:E\rightarrow M
$$

where $M$ is the manager responsible for the event.

Conceptually:

```python
def dispatch(
    state: SessionState,
    event: Event,
) -> Result[SessionState, IllegalTransition]:

    match event:
        case TurnLoopEvent():
            return apply_turn_event(state, event)

        case CommandQueueEvent():
            return apply_command_event(state, event)

        case EventBusEvent():
            return apply_event_bus_event(state, event)

        case _:
            assert_never(event)
```

You don't necessarily need a `Dispatcher` class.

In functional Python, **a function is probably better**.

---

# 11. Your final architecture becomes very small

I'd aim for these conceptual abstractions:

### Domain

$$
\boxed{\mathrm{State}}
$$

Values representing the current domain state.

### Managers

$$
\boxed{\mathrm{TurnManager}}
$$

$$
\boxed{\mathrm{SessionManager}}
$$

Pure transition functions.

### Dispatcher

$$
\boxed{\mathrm{dispatch}}
$$

Determines which manager handles an event.

### Runtime

$$
\boxed{\mathrm{SessionRuntime}}
$$

Coordinates queues, managers and effect interpretation.

### Infrastructure

$$
\boxed{\mathrm{CommandQueue}}
$$

$$
\boxed{\mathrm{EventBus}}
$$

Actual effect/transport mechanisms.

That's enough.

---

# 12. The resulting causal flow

Your runtime should conceptually do:

$$
\boxed{
\begin{aligned}
&\text{receive event}\
&\downarrow\
&\text{dispatch to manager}\
&\downarrow\
&\text{pure state transition}\
&\downarrow\
&\text{derive resulting events/commands}\
&\downarrow\
&\text{runtime interprets them}\
&\downarrow\
&\text{queue/bus}\
&\downarrow\
&\text{next event}
\end{aligned}}
$$

And the important loop is:

$$
S_t
\xrightarrow{E_t}
S_{t+1}
\xrightarrow{\text{derived effects}}
E_{t+1}
\xrightarrow{}
S_{t+2}
$$

This is essentially your kernel's **event-processing algebra**.

---

# 13. Where your LLM fits

This also resolves your previous question.

The LLM should **not** interact directly with the queue.

Instead:

$$
\mathrm{TurnManager}
\rightarrow
\mathrm{TurnRuntime}
\rightarrow
\mathrm{LLM}
$$

The LLM produces a result:

$$
L : \mathrm{Prompt}\rightarrow\mathrm{Completion}
$$

Then your turn logic interprets the completion:

$$
\mathrm{Completion}
\rightarrow
\mathrm{TurnLoopEvent}
$$

or produces:

$$
\mathrm{Command}^{*}
$$

The runtime puts those commands into the command system.

So your architecture becomes:

$$
\boxed{
\begin{aligned}
\mathrm{TUI}
&\rightarrow \mathrm{Command}\
\mathrm{LLM}
&\rightarrow \mathrm{Command}\
\
\mathrm{Command}
&\rightarrow \mathrm{CommandQueue}\
&\rightarrow \mathrm{CommandManager}\
&\rightarrow \mathrm{TurnLoopEvent}\
&\rightarrow \mathrm{TurnManager}\
&\rightarrow \mathrm{TurnLoopState}\
&\rightarrow \mathrm{EventBus}
\end{aligned}}
$$

The **runtime owns the coordination**, while the **managers own the state-transition semantics**.

---

## One change I'd make immediately

Your current:

```python
TurnManager.apply(
    turn_loop_state,
    event_bus_state,
    event,
)
```

should become:

```python
TurnManager.apply(
    turn_loop_state,
    event,
)
```

That single change expresses the architectural principle very clearly:

> **A manager computes state. It doesn't know where the resulting observation is published.**

Then your runtime becomes the place where:

$$
\text{state transition}
\rightarrow
\text{event emission}
\rightarrow
\text{queue scheduling}
$$

is coordinated.

That is much closer to the **small trusted coordinator + isolated state machines + explicit message passing** philosophy you were asking about with seL4/Zircon, while remaining idiomatic for your functional Python style.

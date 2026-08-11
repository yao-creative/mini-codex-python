Yes. Your intent is **state-space decomposition**: deciding whether `TurnLoopState` and `TurnLoopState` are two independent state machines or whether one is a refinement of the other.

I would **not nest `TurnLoopState` inside `TurnLoopState`**. Make them **orthogonal state components**, and let the `SessionState`/agent runtime hold their product.

### Recommended structure

```python
@dataclass
class AgentRuntimeState:
    agent: TurnLoopState
    turn_loop: TurnLoopState
```

with the typestates themselves immutable:

```python
@dataclass(frozen=True)
class Idle(TurnLoopState):
    pass


@dataclass(frozen=True)
class Running(TurnLoopState):
    request_id: str


@dataclass(frozen=True)
class AwaitingTool(TurnLoopState):
    request_id: str
    pending_tool_call: str
```

and separately:

```python
@dataclass(frozen=True)
class TurnIdle(TurnLoopState):
    pass


@dataclass(frozen=True)
class Processing(TurnLoopState):
    turn_id: str


@dataclass(frozen=True)
class WaitingForInput(TurnLoopState):
    pass
```

Then:

$$
AgentRuntimeState
=================

TurnLoopState
\times
TurnLoopState
$$

This is better than:

$$
TurnLoopState
==========

\cdots + (Running \times TurnLoopState) + \cdots
$$

because the two dimensions represent different concerns.

---

## Why they should be orthogonal

Think about what each machine answers.

### `TurnLoopState`

> **What is the agent currently doing with respect to its request/tool execution?**

For example:

$$
TurnLoopState =
Idle
+
Running
+
AwaitingTool
+
Error
$$

### `TurnLoopState`

> **What phase is the turn-processing loop currently in?**

For example:

$$
TurnLoopState =
Idle
+
CallingModel
+
ProcessingResponse
+
ExecutingTools
+
Completing
$$

Those are different axes.

You could have:

$$
Running \times CallingModel
$$

or:

$$
Running \times ExecutingTools
$$

etc.

That product is useful precisely because you **don't force every combination into a single giant sum type**.

---

# But be careful: maybe they aren't actually independent

This is the key design test.

Suppose your turn loop is:

```text
receive user message
→ call model
→ receive completion
→ execute tool
→ feed result back to model
→ receive completion
→ finish turn
```

Then perhaps:

```text
TurnLoopState
    Idle
    Running
    AwaitingTool
```

is already describing the lifecycle of the turn loop.

If so, having:

```text
TurnLoopState
TurnLoopState
```

could be redundant.

You should ask:

> **Can I change one without logically changing the other?**

If the answer is generally **yes**, they're separate state machines.

If the answer is **no**, you're probably representing the same state machine twice.

---

# I suspect your architecture has three different levels

From the architecture you've been building, I'd distinguish:

$$
SessionState
=========

ApplicationRuntimeState
\times
ConversationRuntimeState
\times
AgentRuntimeState
\times
WorkerRuntimeState
\times
CommandQueueState
\times
EventBusState
$$

Then:

$$
AgentRuntimeState
=================

TurnLoopState
\times
TurnLoopState
$$

This gives you a hierarchy of **ownership**, not nesting of semantic state machines:

```text
SessionState
└── AgentRuntimeState
    ├── TurnLoopState
    └── TurnLoopState
```

That's the structure I'd use.

---

## And your managers follow the same decomposition

```python
TurnManager.apply(
    turn_loop_state,
    agent_event,
)
```

while:

```python
TurnLoopManager.apply(
    turn_loop_state,
    turn_loop_event,
)
```

Then the agent runtime coordinates them.

Formally:

$$
T_A :
TurnLoopState \times AgentEvent
\rightarrow
Result(TurnLoopState, E_A)
$$

$$
T_T :
TurnLoopState \times TurnLoopEvent
\rightarrow
Result(TurnLoopState, E_T)
$$

And the runtime composes them:

$$
T_{AgentRuntime}
:
(TurnLoopState \times TurnLoopState)
\times
Event
\rightarrow
(TurnLoopState \times TurnLoopState)
$$

This is much cleaner than having `TurnManager` know everything about the turn loop.

---

### One naming suggestion

I'd use:

```python
AgentRuntimeState
```

rather than just:

```python
TurnLoopState
```

for the product:

```python
@dataclass
class AgentRuntimeState:
    state: TurnLoopState
    turn_loop: TurnLoopState
```

because then the semantic distinction is explicit:

* `TurnLoopState` = **domain typestate**
* `TurnLoopState` = **control-flow typestate**
* `AgentRuntimeState` = **runtime aggregate**

That fits very nicely with your broader separation of **domain state vs control/runtime state**.

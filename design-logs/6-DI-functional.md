**Intent: concrete functional dependency-injection pattern.**

Here is the minimal Python version I would use for your architecture. The important part is that **state, capabilities, and execution are separate**.

```python
from dataclasses import dataclass, field
from typing import Protocol


# ============================================================
# 1. DOMAIN STATE
# ============================================================

@dataclass(frozen=True)
class AgentState:
    messages: tuple[str, ...] = ()


@dataclass(frozen=True)
class ConversationState:
    agent: AgentState


@dataclass(frozen=True)
class SessionState:
    conversation: ConversationState | None = None


@dataclass(frozen=True)
class AppState:
    session: SessionState | None = None


# ============================================================
# 2. CAPABILITY INTERFACES
# ============================================================

class EventSink(Protocol):
    def emit(self, event: str) -> None: ...


class ModelClient(Protocol):
    def complete(self, prompt: str) -> str: ...


class Storage(Protocol):
    def save(self, key: str, value: str) -> None: ...


# ============================================================
# 3. CONCRETE INFRASTRUCTURE
# ============================================================

class EventBus:
    def emit(self, event: str) -> None:
        print(f"[event] {event}")


class OllamaClient:
    def complete(self, prompt: str) -> str:
        return f"response to: {prompt}"


class MemoryStorage:
    def __init__(self) -> None:
        self.data: dict[str, str] = {}

    def save(self, key: str, value: str) -> None:
        self.data[key] = value


# ============================================================
# 4. ENVIRONMENT / CAPABILITIES
# ============================================================

@dataclass(frozen=True)
class AppEnv:
    events: EventSink
    model: ModelClient
    storage: Storage


# ============================================================
# 5. PURE-ish DOMAIN TRANSITIONS
# ============================================================

def start_session(state: AppState) -> AppState:
    return AppState(
        session=SessionState()
    )


def start_conversation(state: SessionState) -> SessionState:
    return SessionState(
        conversation=ConversationState(
            agent=AgentState()
        )
    )


def agent_turn(
    state: AgentState,
    prompt: str,
    env: AppEnv,
) -> AgentState:
    response = env.model.complete(prompt)

    env.events.emit("AgentCompleted")
    env.storage.save("last_response", response)

    return AgentState(
        messages=state.messages + (
            prompt,
            response,
        )
    )
```

Then your **composition root** constructs everything:

```python
def bootstrap() -> tuple[AppState, AppEnv]:
    events = EventBus()
    model = OllamaClient()
    storage = MemoryStorage()

    env = AppEnv(
        events=events,
        model=model,
        storage=storage,
    )

    state = AppState()

    return state, env
```

And your runtime drives it:

```python
def main() -> None:
    state, env = bootstrap()

    # App state transition
    state = start_session(state)

    # Session state transition
    session = start_conversation(state.session)

    # Agent transition
    agent = agent_turn(
        session.conversation.agent,
        "Hello",
        env,
    )

    print(agent)
```

The dependency structure is therefore:

$$
\text{bootstrap}
\rightarrow
(\text{AppState},\text{AppEnv})
$$

and:

$$
\text{AppState}
\rightarrow
\text{SessionState}
\rightarrow
\text{ConversationState}
\rightarrow
\text{AgentState}
$$

while independently:

$$
\text{AppEnv}
=============

{
\text{EventSink},
\text{ModelClient},
\text{Storage}
}
$$

So **state does not recursively construct state + managers**.

---

## For your TUI + Session Loop

This is where the pattern becomes particularly useful.

Both can receive the **same environment**:

```python
def tui_step(
    state: AppState,
    env: AppEnv,
    input_event: str,
) -> AppState:
    env.events.emit(f"TUI:{input_event}")

    return state


def session_step(
    state: SessionState,
    env: AppEnv,
) -> SessionState:
    env.events.emit("SessionTick")

    return state
```

Then:

```python
def application_loop(
    state: AppState,
    env: AppEnv,
) -> None:

    state = tui_step(
        state,
        env,
        "keypress",
    )

    state = start_session(state)

    session = session_step(
        state.session,
        env,
    )
```

The EventBus is therefore **shared infrastructure**, not part of either state.

---

## One refinement I'd make for your architecture

I would actually distinguish **effects from capabilities**.

Instead of letting:

```python
agent_turn(...)
```

directly perform:

```python
env.events.emit(...)
env.storage.save(...)
```

you can make the domain transition return effects:

```python
@dataclass(frozen=True)
class AgentResult:
    state: AgentState
    events: tuple[str, ...]
    writes: tuple[tuple[str, str], ...]
```

Then:

```python
def agent_turn(
    state: AgentState,
    prompt: str,
    model: ModelClient,
) -> AgentResult:

    response = model.complete(prompt)

    return AgentResult(
        state=AgentState(
            messages=state.messages + (prompt, response)
        ),
        events=("AgentCompleted",),
        writes=(("last_response", response),),
    )
```

The runtime interprets those effects:

```python
def run_agent_turn(
    state: AgentState,
    prompt: str,
    env: AppEnv,
) -> AgentState:

    result = agent_turn(
        state,
        prompt,
        env.model,
    )

    for event in result.events:
        env.events.emit(event)

    for key, value in result.writes:
        env.storage.save(key, value)

    return result.state
```

Now you have an even cleaner functional boundary:

$$
\boxed{
\text{Domain}
:
S \times I
\rightarrow
S' \times E
}
$$

and:

$$
\boxed{
\text{Interpreter}
:
E \times C
\rightarrow
\text{Effects}
}
$$

That is the architecture I'd lean toward for your event-driven agent runtime: **immutable state hierarchy + explicit capability environment + effect-producing transitions + one composition root**.

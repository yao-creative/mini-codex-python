Your **intent** is to turn the algebra into a practical Python architecture: **capability-based dependency passing + Reader/Writer/State-style computations + `ControlFlow`**, while keeping the domain functions stateless.

The key is: **don't build a giant “Monad” framework first.** Python's functions, dataclasses, `Result`, and pattern matching are enough.

---

# 1. Capability-based systems

A capability is an object representing **authority to perform some operation**.

Instead of:

```python
def load_user(user_id):
    global_db.query(...)
```

pass the capability explicitly:

```python
def load_user(storage: Storage, user_id: UserId):
    return storage.load_user(user_id)
```

Algebraically:

$$
Storage \times UserId \to Result(User, Error)
$$

Or curry the capability:

$$
UserId \to (Storage \to Result(User, Error))
$$

The latter is the **Reader formulation**.

---

## 2. Build a capability environment

For your architecture, I'd use a small immutable-ish environment:

```python
from dataclasses import dataclass
from typing import Protocol


class Storage(Protocol):
    def load_user(self, user_id: str) -> "User": ...


class ModelClient(Protocol):
    def complete(self, prompt: str) -> str: ...


class EventSink(Protocol):
    def publish(self, event: "Event") -> None: ...


@dataclass(frozen=True)
class Env:
    storage: Storage
    model: ModelClient
    events: EventSink
```

The important thing is that `Env` **contains capabilities**.

It doesn't contain application state like:

```python
AgentState
ConversationState
CommandQueueState
```

Those are separate.

So conceptually:

$$
Env =
Storage\times ModelClient\times EventSink
$$

---

# 3. A capability-dependent function

```python
def load_user(
    env: Env,
    user_id: str,
) -> User:
    return env.storage.load_user(user_id)
```

Its type is:

$$
Env\times UserId\to User
$$

If you want the Reader form:

```python
def load_user(
    user_id: str,
):
    def computation(env: Env) -> User:
        return env.storage.load_user(user_id)

    return computation
```

Now:

```python
operation = load_user("alice")

user = operation(env)
```

Mathematically:

$$
loadUser :
UserId \to (Env\to User)
$$

That's Reader.

---

# 4. Make Reader explicit

If you're studying the algebra, an explicit wrapper is useful:

```python
from dataclasses import dataclass
from typing import Callable, Generic, TypeVar

R = TypeVar("R")
A = TypeVar("A")
B = TypeVar("B")


@dataclass(frozen=True)
class Reader(Generic[R, A]):
    run: Callable[[R], A]

    def map(self, f: Callable[[A], B]) -> "Reader[R, B]":
        return Reader(lambda env: f(self.run(env)))

    def and_then(
        self,
        f: Callable[[A], "Reader[R, B]"],
    ) -> "Reader[R, B]":
        return Reader(lambda env: f(self.run(env)).run(env))
```

The algebra is:

$$
Reader_R(A)=R\to A
$$

### `map`

$$
(A\to B)
\to
(R\to A)
\to
(R\to B)
$$

Implementation:

```python
Reader(lambda r: f(self.run(r)))
```

### `and_then`

$$
(R\to A)
\times
(A\to(R\to B))
\to
(R\to B)
$$

Implementation:

```python
lambda r:
    f(self.run(r)).run(r)
```

Notice that the **same environment** is passed through the entire computation.

---

# 5. Example: composing capabilities

```python
def get_user(user_id: str) -> Reader[Env, User]:
    return Reader(lambda env: env.storage.load_user(user_id))


def get_prompt(user: User) -> Reader[Env, str]:
    return Reader(lambda env: env.storage.build_prompt(user))


operation = get_user("alice").and_then(get_prompt)

prompt = operation.run(env)
```

The composition is:

$$
UserId
\to
Reader_{Env}(User)
$$

then:

$$
User
\to
Reader_{Env}(Prompt)
$$

giving:

$$
UserId
\to
Reader_{Env}(Prompt)
$$

No object owns the environment.

---

# 6. Reader + Result

This is probably the most useful version for your application:

$$
Reader_{Env}(Result(A,E))
=========================

Env\to(A+E)
$$

Explicitly:

```python
@dataclass(frozen=True)
class ReaderResult(Generic[R, A, E]):
    run: Callable[[R], Result[A, E]]
```

You want:

```python
def load_user(
    user_id: str,
) -> ReaderResult[Env, User, AppError]:
    return ReaderResult(lambda env: env.storage.load_user(user_id))
```

Then:

```python
def get_agent(
    user: User,
) -> ReaderResult[Env, Agent, AppError]:
    return ReaderResult(lambda env: env.storage.load_agent(user.id))
```

Composition:

```python
operation = load_user("alice").and_then(get_agent)

result = operation.run(env)
```

Conceptually:

$$
Env\to(User+E)
$$

followed by:

$$
User\to(Agent+E)
$$

giving:

$$
Env\to(Agent+E)
$$

This is an excellent model for **capability-dependent application services**.

---

# 7. Writer

Now suppose you don't want your domain function to directly publish events.

Instead:

$$
Writer_W(A)=A\times W
$$

For your event architecture:

$$
W=Event^*
$$

So:

$$
Writer(A)=A\times Event^*
$$

Python:

```python
@dataclass(frozen=True)
class Writer(Generic[A]):
    value: A
    output: tuple[Event, ...]

    def map(self, f: Callable[[A], B]) -> "Writer[B]":
        return Writer(
            value=f(self.value),
            output=self.output,
        )

    def and_then(
        self,
        f: Callable[[A], "Writer[B]"],
    ) -> "Writer[B]":
        next_result = f(self.value)

        return Writer(
            value=next_result.value,
            output=self.output + next_result.output,
        )
```

The important operation is accumulation:

$$
W\times W\to W
$$

For tuples:

$$
(events_1,events_2)
\mapsto
events_1\mathbin{+!!+}events_2
$$

where `++` is sequence concatenation.

---

# 8. Writer example for your event architecture

Instead of:

```python
def enqueue(state, command):
    state.queue.append(command)
    event_bus.publish(...)
```

you can have:

```python
def enqueue(
    state: CommandQueueState,
    command: Command,
) -> Writer[CommandQueueState]:
    state.queue.append(command)

    return Writer(
        value=state,
        output=(CommandEnqueued(command.id),),
    )
```

Then:

```python
result = enqueue(state, command)
```

produces:

$$
State\times Event^*
$$

The domain has **described** the event.

It hasn't published anything.

At the boundary:

```python
for event in result.output:
    env.events.publish(event)
```

That's the interpreter.

---

# 9. Reader + Writer

Now combine the two:

$$
Env\to(A\times W)
$$

Python:

```python
@dataclass(frozen=True)
class ReaderWriter(Generic[R, A]):
    run: Callable[[R], Writer[A]]

    def map(self, f):
        return ReaderWriter(lambda env: self.run(env).map(f))

    def and_then(self, f):
        return ReaderWriter(
            lambda env: self.run(env).and_then(lambda value: f(value).run(env))
        )
```

Now you have:

$$
Reader_W(A)
===========

R\to(A\times W)
$$

For your application:

$$
Env
\to
(State\times Events)
$$

That's quite powerful.

---

# 10. Reader + Writer + Result

Now we get close to a realistic application computation:

$$
\boxed{
Env
\to
Result(A,E)\times Events
}
$$

or, depending on your desired error/event semantics:

$$
Env\to Result(A\times Events,E)
$$

These are **not equivalent**.

For example:

### Version A

$$
Env\to(Result(A,E)\times Events)
$$

can return events even when the computation fails.

### Version B

$$
Env\to Result(A\times Events,E)
$$

means failure produces no successful output/events.

For your event-driven agent runtime, I would usually prefer **Version B** for domain transitions:

$$
A\to Result(B\times Events,E)
$$

because it gives a clean invariant:

> either the operation succeeds with its state/output and events, or it fails.

---

# 11. State + Writer

For your queue specifically, this is arguably more natural than a formal Writer monad:

$$
State\times Input
\to
Result(State\times Events,E)
$$

For example:

```python
@dataclass(frozen=True)
class Transition(Generic[S]):
    state: S
    events: tuple[Event, ...]
```

Then:

```python
def enqueue(
    state: CommandQueueState,
    command: Command,
) -> Result[Transition[CommandQueueState], QueueError]:
    state.queue.append(command)

    return Ok(
        Transition(
            state=state,
            events=(CommandEnqueued(command.id),),
        )
    )
```

Your runtime then does:

```python
result = enqueue(state, command)

match result:
    case Ok(transition):
        state = transition.state

        for event in transition.events:
            env.events.publish(event)

    case Err(error):
        ...
```

That is essentially your **functional core / imperative shell**.

---

# 12. `ControlFlow`

Python doesn't have a direct equivalent to Rust's:

```rust
std::ops::ControlFlow
```

but you can model it directly.

Rust:

```rust
enum ControlFlow<B, C> {
    Break(B),
    Continue(C),
}
```

Python:

```python
@dataclass(frozen=True)
class Continue(Generic[A]):
    value: A


@dataclass(frozen=True)
class Break(Generic[B]):
    value: B


ControlFlow = Continue[A] | Break[B]
```

Algebraically:

$$
ControlFlow(B,C)=B+C
$$

It is another tagged coproduct.

---

# 13. Implementing `try`-style traversal

Suppose:

```python
def visit(node) -> ControlFlow[Found, None]:
    if matches(node):
        return Break(Found(node))

    for child in node.children:
        result = visit(child)

        match result:
            case Break(found):
                return Break(found)

            case Continue(_):
                pass

    return Continue(None)
```

The semantics are:

$$
Continue(c)
$$

means:

> Keep going.

while:

$$
Break(b)
$$

means:

> Stop immediately and return `b`.

---

# 14. `ControlFlow` vs `Result`

This distinction is important for your event architecture.

`Result`:

$$
A+E
$$

means:

$$
Success+Failure
$$

`ControlFlow`:

$$
C+B
$$

means:

$$
Continue+Break
$$

A `Break` isn't necessarily an error.

For example:

```python
Break(UserFound(user))
```

is a successful early termination.

That's why `ControlFlow` is useful for:

* tree traversal
* graph search
* parsers
* visitor patterns
* folds
* recursive interpreters
* "find first"
* short-circuiting algorithms

---

# 15. How I'd actually structure your Python system

I would **not** make everything a monad.

Use these layers:

$$
\boxed{
Domain
}
$$

Pure state transition:

$$
S\times I
\to
Result(S\times Events,E)
$$

Then:

$$
\boxed{
Application
}
$$

Capability-dependent computation:

$$
I
\to
Env\to Result(A,E)
$$

Then:

$$
\boxed{
Runtime
}
$$

Interpret capabilities and effects:

$$
Env\times Events
\to
IO
$$

So your queue can be:

```python
def apply(
    state: CommandQueueState,
    event: CommandQueueEvent,
) -> Result[
    Transition[CommandQueueState],
    QueueError,
]:
    match event:
        case Enqueue(command):
            state.queue.append(command)

            return Ok(
                Transition(
                    state,
                    (CommandEnqueued(command.id),),
                )
            )

        case Dequeue():
            if not state.queue:
                return Err(QueueEmpty())

            command = state.queue.popleft()

            return Ok(
                Transition(
                    state,
                    (CommandDequeued(command.id),),
                )
            )
```

And the runtime:

```python
result = CommandQueueManager.apply(state, event)

match result:
    case Ok(transition):
        for emitted in transition.events:
            env.events.publish(emitted)

    case Err(error):
        ...
```

The key semantic separation is:

$$
\boxed{
\text{capability} \neq \text{state} \neq \text{event} \neq \text{effect}
}
$$

* **Capability:** `env.storage`, `env.events`, `env.model`
* **State:** `CommandQueueState`
* **Event:** `Enqueue(cmd)`
* **Transition output:** `Transition(state, events)`
* **Effect:** actually calling `env.events.publish(...)`

That separation is more valuable than whether you literally call the wrappers `Reader`, `Writer`, or `State`.

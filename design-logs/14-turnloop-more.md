**Intent: control-plane architecture — deciding who owns command production and where command queues belong in a microkernel-style functional runtime.**

I would **not make the TUI or the LLM own the `CommandQueue`**.

Make the **runtime/kernel own the queue**, while the TUI and turn loop are **producers of commands**.

The key principle borrowed from microkernel design is:

> **The component that owns a resource should mediate access to it; clients receive a narrow operation/interface, not the resource itself.**

### Recommended topology

$$
\boxed{
\begin{aligned}
\mathrm{TUI}
&\rightarrow \mathrm{Command}\
\mathrm{TurnLoop}
&\rightarrow \mathrm{Command}\
\
&\searrow\quad\downarrow\
&\quad \mathrm{CommandDispatcher}\
&\quad\downarrow\
&\mathrm{CommandQueue}\
&\quad\downarrow\
&\mathrm{CommandExecutor}
\end{aligned}}
$$

So both TUI and LLM can **submit commands**, but neither owns the queue.

---

## 1. Why the queue belongs to the runtime

A queue is not really a domain dependency.

It is **scheduling/transport infrastructure**.

Its job is to establish an ordering:

$$
Q_C = (c_1,c_2,\ldots,c_n)
$$

and potentially provide:

* serialization
* backpressure
* fairness
* scheduling
* cancellation
* prioritization
* concurrency control

Those are runtime concerns.

If the TUI owns the queue, you've implicitly made:

$$
\mathrm{TUI}
\rightarrow
\mathrm{KernelScheduling}
$$

which is backwards.

Likewise, if the LLM/turn loop owns it:

$$
\mathrm{TurnLoop}
\rightarrow
\mathrm{KernelScheduling}
$$

Again, the worker is now controlling the scheduler.

A microkernel-style design instead says:

$$
\boxed{
\mathrm{Runtime}
\owns
Q_C
}
$$

and gives clients a restricted capability:

$$
C_{\mathrm{submit}}
:
\mathrm{Command}\rightarrow 1
$$

---

# 2. This is very close to the seL4 mental model

In seL4, a user-level component doesn't own the kernel's global scheduling machinery.

It possesses capabilities to specific kernel objects and invokes operations through them.

The important architectural lesson is:

$$
\text{resource ownership}
\neq
\text{resource usage}
$$

A client can have authority to interact with an object without owning the object itself.

You should apply that distinction to your command queue.

Your runtime owns:

$$
Q_C
$$

The TUI gets:

$$
C_{\mathrm{tui}}
================

\mathrm{SubmitCommand}
$$

The turn loop gets:

$$
C_{\mathrm{turn}}
=================

\mathrm{SubmitCommand}
$$

Potentially they aren't even the same capability.

For example:

$$
C_{\mathrm{tui}}
================

{
\mathrm{SubmitUserCommand}
}
$$

while:

$$
C_{\mathrm{turn}}
=================

{
\mathrm{SubmitAgentCommand}
}
$$

The dispatcher can then enforce different policies.

---

# 3. The TUI and LLM have different semantic roles

This is where I'd avoid treating them symmetrically.

### TUI

The TUI is an **input adapter**.

It translates:

$$
\mathrm{UserInput}
\rightarrow
\mathrm{Command}
$$

For example:

$$
\mathrm{keypress}
\rightarrow
\mathrm{CancelTurn}
$$

or:

$$
\mathrm{text}
\rightarrow
\mathrm{SendMessage}
$$

### Turn loop

The turn loop is an **agent/control computation**.

It translates:

$$
\mathrm{LLMOutput}
\rightarrow
\mathrm{Command}
$$

For example:

$$
\mathrm{LLMToolCall}
\rightarrow
\mathrm{CallTool}
$$

Both produce commands, but their **provenance and authority are different**.

---

# 4. The LLM should not directly control the command queue

This is particularly important.

Don't conceptualize:

$$
\mathrm{LLM}
\rightarrow
Q_C
$$

Instead:

$$
\mathrm{LLM}
\rightarrow
\mathrm{Turn}
\rightarrow
\mathrm{Command}
\rightarrow
\mathrm{Dispatcher}
\rightarrow
Q_C
$$

Why?

Because the LLM is an **untrusted decision-maker**.

It produces data that your runtime interprets.

You don't want:

> "The model generated a tool call, therefore execute it."

You want:

$$
\mathrm{ModelOutput}
\rightarrow
\mathrm{Validate}
\rightarrow
\mathrm{Authorize}
\rightarrow
\mathrm{Command}
\rightarrow
\mathrm{Schedule}
\rightarrow
\mathrm{Execute}
$$

This is exactly where your capability model becomes useful.

---

# 5. Your turn loop should therefore look like this

Conceptually:

$$
\boxed{
\mathrm{TurnLoop}
:
\mathrm{Input}
\rightarrow
\mathrm{LLM}
\rightarrow
\mathrm{Decision}
\rightarrow
\mathrm{Command}^{*}
}
$$

It does **not** need to know the queue implementation.

Then:

$$
\boxed{
\mathrm{CommandDispatcher}
:
\mathrm{Command}
\rightarrow
\mathrm{ValidatedCommand}
}
$$

Then:

$$
\boxed{
\mathrm{Scheduler}
:
\mathrm{ValidatedCommand}
\rightarrow
Q_C
}
$$

This gives you a much cleaner separation.

---

# 6. What about events?

I would make the direction symmetrical:

$$
\mathrm{Command}
\rightarrow
\mathrm{Executor}
\rightarrow
\mathrm{StateTransition}
\rightarrow
\mathrm{Event}
\rightarrow
\mathrm{EventBus}
$$

The event bus is also runtime-owned.

So:

$$
\boxed{
\begin{aligned}
\mathrm{TUI} &\rightarrow C\
\mathrm{TurnLoop} &\rightarrow C\
\
C &\rightarrow \mathrm{CommandQueue}\
\
\mathrm{Executor} &\rightarrow E\
\
E &\rightarrow \mathrm{EventBus}\
\
\mathrm{TUI} &\leftarrow E\
\mathrm{TurnLoop} &\leftarrow E
\end{aligned}}
$$

Notice the beautiful property:

**neither TUI nor TurnLoop needs to know about the other.**

They communicate through the kernel's command/event planes.

---

# 7. This resembles microkernel architecture

The deeper inspiration isn't "copy seL4's queue."

It's the architectural pattern:

$$
\boxed{
\text{small trusted mediator}
+
\text{untrusted/independent clients}
+
\text{explicit authority}
+
\text{message passing}
}
$$

Your runtime becomes the mediator.

The TUI is one client.

The turn loop is another client.

The model is another component.

Tools are other components.

They don't directly manipulate each other's state.

They communicate through explicit protocols.

That is much closer to the microkernel philosophy.

---

# 8. And Jane Street's influence is different

From Jane Street/OCaml-style engineering, I'd borrow:

> **Make the dataflow and interfaces explicit, minimize ambient state, and make illegal dependencies difficult to express.**

So instead of:

```python
class TurnLoop:
    self.runtime.command_queue
    self.runtime.event_bus
    self.runtime.storage
    self.runtime.session
```

prefer something like:

```python
@dataclass(frozen=True)
class TurnEnv:
    model: Model
    submit: Callable[[Command], None]
```

or, even better for your functional architecture:

```python
def turn(
    state: TurnState,
    input: TurnInput,
) -> TurnResult:
    ...
```

where:

```python
@dataclass(frozen=True)
class TurnResult:
    state: TurnState
    commands: tuple[Command, ...]
    events: tuple[Event, ...]
```

Then your runtime owns the actual infrastructure:

```python
result = turn(state, input)

for command in result.commands:
    command_runtime.submit(command)

for event in result.events:
    event_bus.publish(event)
```

This is the version I would recommend **for your current kernel**.

---

# 9. The important architectural decision

You essentially have three levels:

### Level 1 — Pure domain

$$
\mathrm{Turn}
:
S\times I
\rightarrow
S\times C^*\times E^*
$$

No queues. No event bus. No runtime.

### Level 2 — Runtime

$$
\mathrm{TurnRuntime}
:
C_{\mathrm{submit}}\times C_{\mathrm{publish}}
\rightarrow
\mathrm{Execution}
$$

This owns the infrastructure and interprets the turn's results.

### Level 3 — Infrastructure

$$
\mathrm{CommandQueue}
$$

and:

$$
\mathrm{EventBus}
$$

These implement transport/scheduling.

So:

$$
\boxed{
\text{Turn}
\rightarrow
\text{Commands/Events}
\rightarrow
\text{Runtime}
\rightarrow
\text{Queues/Buses}
\rightarrow
\text{Services}
}
$$

---

## My recommendation for your specific system

**Do this:**

$$
\boxed{
\begin{array}{c}
\mathrm{TUI}\
\downarrow\
\mathrm{Command}\
\downarrow\
\mathrm{CommandDispatcher}
\leftarrow
\mathrm{TurnLoop}
\leftarrow
\mathrm{LLM}\
\downarrow\
\mathrm{CommandQueue}\
\downarrow\
\mathrm{Executor}\
\downarrow\
\mathrm{EventBus}\
\downarrow\
\begin{array}{c}
\mathrm{TUI}\
\mathrm{TurnLoop}\
\mathrm{Telemetry}\
\mathrm{Persistence}
\end{array}
\end{array}
}
$$

**Runtime owns queues. Components produce/consume messages. Capabilities control which messages/operations each component is authorized to use.**

And for your particular functional style, I'd go one step further: **make `Turn` pure and have the runtime interpret its `commands` and `events`.** That gives you the strongest separation and makes testing/replay extraordinarily easy.

The one thing I'd *not* do is have the TUI and LLM independently manipulate the same mutable queue object. They should both interact with a **runtime-owned command submission capability**, or preferably return command values that the runtime submits.

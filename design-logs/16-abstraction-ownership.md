**Intent: algebraic ownership decomposition** — you want to distinguish *what data/authority each abstraction owns* from *what functions it performs*.

The most useful rule is:

> **An abstraction should own the mathematical object whose invariants it is responsible for. It should not own merely the mechanism used to transport or observe that object.**

For your kernel, I would decompose ownership like this.

---

## 1. The whole system

Let:

* $S$ = domain state
* $E$ = events
* $C$ = commands
* $Q_C = C^*$ = command sequence/queue
* $Q_E = E^*$ = event sequence
* $R$ = runtime authorities/resources

Then the system is roughly:

$$
\boxed{
\mathrm{Runtime}
================

(S,;Q_C,;Q_E,;R)
}
$$

but these are **not all owned by the same abstraction**.

The ownership partition should be:

$$
\boxed{
S
=

S_{\mathrm{session}}
\times
S_{\mathrm{turn}}
\times
\cdots
}
$$

while:

$$
R
=

R_{\mathrm{queue}}
\times
R_{\mathrm{bus}}
\times
R_{\mathrm{model}}
\times
\cdots
$$

---

# 2. `TurnState`

**Owns: the mathematical state of the turn state machine.**

$$
\boxed{
\mathrm{TurnState}
\in
T
}
$$

For yours:

$$
T =
\mathrm{Idle}
+
\mathrm{Running}
+
\mathrm{AwaitingTool}
+
\mathrm{Error}
$$

This is a sum type:

$$
T =
I + R + A + F
$$

where each constructor represents a mutually exclusive state.

The state owns the invariants:

$$
\mathrm{Running}(r)
\Rightarrow
\text{there is an active request }r
$$

$$
\mathrm{AwaitingTool}(r,t)
\Rightarrow
\text{request }r\text{ has pending tool }t
$$

It does **not** own the event bus.

---

# 3. `TurnManager`

**Owns the transition relation, not the state itself.**

This distinction is important.

The state is:

$$
T
$$

The manager owns the transition function:

$$
\boxed{
\delta_T:T\times E_T\rightarrow T+\mathrm{IllegalTransition}
}
$$

So:

```python
TurnManager.apply(state, event)
```

means:

$$
\delta_T(t,e)
$$

The manager's responsibility is:

> Given a valid turn state and a turn event, determine the next turn state.

It should therefore **not own**:

$$
Q_C
$$

or:

$$
Q_E
$$

or:

$$
R_{\mathrm{model}}
$$

It owns the **transition semantics**.

---

# 4. `SessionState`

Your session aggregates several domain states.

For example:

$$
\boxed{
S_{\mathrm{session}}
====================

T
\times
C_{\mathrm{conversation}}
\times
U_{\mathrm{session}}
}
$$

where:

* $T$ = turn state
* $C_{\mathrm{conversation}}$ = conversation state
* $U_{\mathrm{session}}$ = other session state

The session state owns the invariants relating these pieces.

For example:

$$
\mathrm{TurnRunning}
\Rightarrow
\mathrm{SessionHasActiveTurn}
$$

So `SessionState` is the **domain aggregate**.

---

# 5. `SessionManager`

The SessionManager owns the aggregate transition function:

$$
\boxed{
\delta_S:
S_{\mathrm{session}}\times E
\rightarrow
S_{\mathrm{session}}+\mathrm{Error}
}
$$

It composes the smaller state machines.

For example:

$$
\delta_S
========

\begin{cases}
\delta_T & E\in E_T\
\delta_C & E\in E_C\
\delta_B & E\in E_B
\end{cases}
$$

This is essentially what your current:

```python
match event:
    case TurnLoopEvent():
        ...
    case CommandQueueEvent():
        ...
    case EventBusEvent():
        ...
```

is doing.

So `SessionManager` owns the **composition of state transitions**.

---

# 6. `Command`

A command owns **intent as data**.

$$
\boxed{
c\in C
}
$$

For example:

$$
\mathrm{CallModel}(p)
$$

$$
\mathrm{RunTool}(t)
$$

$$
\mathrm{PersistSession}(s)
$$

A command does **not** own the queue.

That's a crucial distinction.

The command says:

> "I request this operation."

It doesn't say:

> "I will execute myself."

---

# 7. `CommandQueue`

The queue owns **ordering/transport state**.

$$
\boxed{
Q_C\in C^*
}
$$

For example:

$$
Q_C =
[c_1,c_2,c_3]
$$

Its invariant might be:

$$
\mathrm{enqueue}(c):
Q_C\rightarrow Q_C\mathbin{+!!+}[c]
$$

and:

$$
\mathrm{dequeue}:
C^*
\rightarrow
C\times C^*
$$

So the queue owns:

* pending commands
* ordering
* possibly priority
* possibly backpressure
* possibly scheduling metadata

It does **not** own the semantics of the command.

---

# 8. `CommandManager`

If you have a `CommandQueueManager`, I'd define its ownership carefully.

It should own the **state transition semantics of the queue**, not the domain meaning of commands.

$$
\boxed{
\delta_Q:
Q_C\times E_C
\rightarrow
Q_C+\mathrm{Error}
}
$$

For example:

$$
\delta_Q(Q,\mathrm{Enqueue}(c))
===============================

Q\mathbin{+!!+}[c]
$$

This is distinct from:

$$
\mathrm{execute}(\mathrm{RunTool}(t))
$$

which belongs to the command executor/interpreter.

So:

$$
\boxed{
\mathrm{CommandManager}
\neq
\mathrm{CommandExecutor}
}
$$

The first manages queue state.

The second gives commands operational meaning.

---

# 9. `Event`

An event owns **a fact/observation as data**.

$$
\boxed{
e\in E
}
$$

For example:

$$
\mathrm{TurnStateChanged}(Idle,Running)
$$

$$
\mathrm{CompletionReceived}(r,c)
$$

The event does not own subscribers.

It is just a value.

This gives you the useful distinction:

$$
C=\text{intent}
$$

versus:

$$
E=\text{fact}
$$

---

# 10. `EventBus`

The EventBus owns **distribution state**.

Conceptually:

$$
B =
\mathrm{Event}
\rightarrow
\mathcal P(\mathrm{Subscriber})
$$

or, operationally, something like:

$$
B =
{e\mapsto(s_1,s_2,\ldots)}
$$

It owns:

* subscriber registrations
* event routing
* delivery order
* perhaps buffering

It does **not** own the meaning of the event.

So:

$$
\boxed{
\mathrm{Event}
==============

\text{semantic fact}
}
$$

$$
\boxed{
\mathrm{EventBus}
=================

\text{distribution mechanism}
}
$$

---

# 11. `EventBusManager`

Analogously:

$$
\boxed{
\delta_B:
B\times E_B
\rightarrow
B+\mathrm{Error}
}
$$

It manages the EventBus state.

For example:

$$
\delta_B(B,\mathrm{Subscribe}(s))
=================================

B'
$$

or:

$$
\delta_B(B,\mathrm{Publish}(e))
===============================

B'
$$

depending on whether you model delivery as state.

Again, it shouldn't know what a `TurnStateChanged` event **means**.

---

# 12. The `Runtime`

This is the interesting one.

The Runtime should own **coordination authority**, not domain state.

Think of:

$$
\boxed{
R =
C_Q
\times
C_B
\times
C_M
\times
C_S
\times\cdots
}
$$

where these are capabilities/references to infrastructure.

The Runtime therefore owns:

$$
\boxed{
\text{authority to coordinate}
}
$$

rather than:

$$
\boxed{
\text{all domain state}
}
$$

It performs the orchestration:

$$
E
\rightarrow
\mathrm{SessionManager}
\rightarrow
S'
\rightarrow
\mathrm{Commands/Events}
\rightarrow
\mathrm{Infrastructure}
$$

---

# 13. The `Dispatcher`

The dispatcher owns almost no state.

It owns a **routing function**:

$$
\boxed{
D:E\rightarrow M
}
$$

where $M$ is the appropriate manager.

For example:

$$
D(\mathrm{TurnLoopEvent})
=========================

\mathrm{TurnManager}
$$

$$
D(\mathrm{CommandQueueEvent})
=============================

\mathrm{CommandQueueManager}
$$

$$
D(\mathrm{EventBusEvent})
=========================

\mathrm{EventBusManager}
$$

In functional Python, this should probably just be a function rather than a class.

---

# 14. The interpreter

The interpreter owns **operational semantics**.

This is distinct from the manager.

A manager says:

$$
\delta_T(T,E)=T'
$$

An interpreter says:

$$
I(C,R)=\mathrm{Effect}
$$

For example:

$$
I(
\mathrm{RunTool}(x),
C_{\mathrm{tool}}
)
=

\mathrm{ToolExecution}(x)
$$

So:

$$
\boxed{
\mathrm{Manager}
================

\text{state semantics}
}
$$

while:

$$
\boxed{
\mathrm{Interpreter}
====================

\text{effect semantics}
}
$$

---

# 15. The complete ownership table

| Abstraction           | Algebraic object it owns | Main responsibility          |
| --------------------- | ------------------------ | ---------------------------- |
| `TurnState`           | $T$                      | turn invariants              |
| `TurnManager`         | $\delta_T$               | turn transitions             |
| `SessionState`        | $S$                      | session aggregate invariants |
| `SessionManager`      | $\delta_S$               | aggregate transitions        |
| `Command`             | $C$                      | effect intent                |
| `CommandQueue`        | $C^*$                    | pending-command ordering     |
| `CommandQueueManager` | $\delta_Q$               | queue transitions            |
| `Event`               | $E$                      | observed fact                |
| `EventBus`            | $B$                      | event distribution           |
| `EventBusManager`     | $\delta_B$               | bus transitions              |
| `Dispatcher`          | $D:E\to M$               | routing                      |
| `Interpreter`         | $I:C\to\mathrm{Effect}$  | operational semantics        |
| `Runtime`             | $R$                      | coordination authority       |

---

# 16. The key thing I would change in your current code

You currently have:

$$
\mathrm{TurnManager}
:
T\times B\times E_T
\rightarrow T
$$

I'd change it to:

$$
\boxed{
\mathrm{TurnManager}
:
T\times E_T
\rightarrow T
}
$$

Then:

$$
\mathrm{Runtime}
:
(T,B,Q_C,\ldots)
\rightarrow
(T',B',Q_C',\ldots)
$$

The Runtime is where the different worlds meet.

So your architecture becomes:

$$
\boxed{
\begin{aligned}
\text{Domain}
&:
S,E,C
\
\text{Managers}
&:
\delta:S\times E\to S
\
\text{Dispatcher}
&:
D:E\to M
\
\text{Interpreter}
&:
I:C\to\mathrm{Effect}
\
\text{Infrastructure}
&:
Q_C,B
\
\text{Runtime}
&:
\text{coordinates all of the above}
\end{aligned}}
$$

That gives you a very clean principle:

> **Managers own transition laws; queues own pending work; buses own distribution; commands own intent; events own facts; runtime owns coordination; capabilities own authority.**

And importantly, **none of those abstractions needs to own the entire system state**. Your functional style can therefore remain almost entirely value-transforming rather than object-state-mutating.

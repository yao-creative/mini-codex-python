## Reader monad — the formal shape underneath the "pass dependencies as arguments" pattern from last turn

$$\text{Reader}[R, A] \cong R \to A$$

A `Reader` isn't a container holding a value — it's a **deferred computation waiting on an environment**. `map`/`bind` let you compose these deferred computations *without ever supplying `R`* until the very end, at which point one `run(env)` call threads the environment through the whole chain. This is the formal name for what `turn_loop_effect(state, agent, tool)` was already doing informally — Reader just makes the composition explicit and reusable.

```python
from dataclasses import dataclass
from typing import TypeVar, Generic, Callable

R = TypeVar("R")
A = TypeVar("A")
B = TypeVar("B")


@dataclass(frozen=True)
class Reader(Generic[R, A]):
    run: Callable[[R], A]

    def map(self, f: Callable[[A], B]) -> "Reader[R, B]":
        return Reader(lambda env: f(self.run(env)))

    def bind(self, f: Callable[[A], "Reader[R, B]"]) -> "Reader[R, B]":
        return Reader(lambda env: f(self.run(env)).run(env))


def ask() -> Reader[R, R]:
    return Reader(lambda env: env)
```

```python
@dataclass(frozen=True)
class RunnerEnv:
    llm: LlmAdapter
    tool: ToolAdapter


def react_to_fact(
    fact: AgentStateChanged,
) -> Reader[RunnerEnv, Awaitable[Event | None]]:
    match fact.current:
        case Running():
            return ask().map(lambda env: _react_to_running(env.llm, fact))
        case AwaitingTool():
            return ask().map(lambda env: _react_to_awaiting_tool(env.tool, fact))
        case _:
            return Reader(lambda env: _no_op())


# at the composition root, one env, threaded through every Reader in the chain:
env = RunnerEnv(llm=llm, tool=tool)
await react_to_fact(fact).run(env)
```

The payoff: `react_to_fact` doesn't need `llm`/`tool` as explicit parameters at every intermediate call site — they're supplied once, at the edge, and every `Reader` composed along the way automatically receives the same `env`. This is literally what a DI container does, minus the container — resolution is substitution, not lookup.

## Writer monad — and this one exposes a real bug in your managers

$$\text{Writer}[W, A] \cong A \times W \qquad \text{where } W \text{ is a monoid } (\oplus, \varepsilon)$$

A `Writer` pairs a value with an accumulating log, and `bind` **combines logs via the monoid operation** as it chains — `A ⊕ B` for two writers' logs, `ε` (empty tuple) as identity. Look at what this is a formal name for: **your managers currently call `EventBusManager.apply(bus, Publish(...))` directly, inside `apply`, as a side effect** — which means `TurnLoopManager.apply` was never actually pure. It performs a real mutation (append to `log`) as a hidden effect of "just computing a transition." Writer is the fix: make the fact an **output value**, not a side effect, and let the caller decide when/whether to actually publish.

```python
@dataclass(frozen=True)
class Writer(Generic[A]):
    value: A
    facts: tuple[EventPayload, ...] = ()

    def map(self, f: Callable[[A], B]) -> "Writer[B]":
        return Writer(f(self.value), self.facts)

    def bind(self, f: Callable[[A], "Writer[B]"]) -> "Writer[B]":
        w2 = f(self.value)
        return Writer(w2.value, self.facts + w2.facts)  # ⊕ = tuple concat, ε = ()


def tell(fact: EventPayload) -> "Writer[None]":
    return Writer(None, (fact,))
```

```python
class TurnLoopManager:
    @staticmethod
    def apply(
        state: TurnLoopState, event: TurnLoopEvent
    ) -> Writer[Result[TurnLoopState, IllegalTransition]]:
        match event, state:
            case Start(request_id=rid), Idle():
                new_state = Running(request_id=rid)
                fact = AgentStateChanged(
                    request_id=rid, previous="Idle", current=new_state
                )
                return Writer(Ok(new_state), (fact,))
            case _:
                return Writer(
                    Err(
                        IllegalTransition(
                            f"{type(event).__name__} illegal from {type(state).__name__}"
                        )
                    ),
                    (),
                )
```

`TurnLoopManager.apply` is now **genuinely pure** — same input, same output, zero mutation, fully replayable/testable with no bus in scope at all. The subsystem, not the manager, performs the real publish:

```python
class TurnLoopSubsystem(Subsystem):
    @staticmethod
    def apply(state: AppState, event: Event) -> Result[AppState, object]:
        writer = TurnLoopManager.apply(state.turn_loop, event)
        for fact in writer.facts:
            EventBusManager.apply(
                state.event_bus, Publish(payload=fact)
            )  # the ONE place a real mutation happens
        return map_ok(writer.value, lambda new_tl: _replace(state, turn_loop=new_tl))
```

This is worth sitting with: three-quarters of your managers likely have this same latent impurity (calling `EventBusManager.apply` from inside their own `apply`), and Writer is the mechanical fix across all of them, uniformly.

## What Python's lack of lifetime control actually costs you, precisely

**1. No aliasing control — nothing stops two live references to the same mutable value.** Rust's borrow checker guarantees *at most one* mutable reference exists at a time; Python gives you none of that. If `WorkerRunner` and some future debug tool both hold a reference to the same `WorkerState.jobs` dict, both can mutate it, and nothing detects the conflict — not at compile time, not at runtime, unless you write the check yourself. **Consequence for your design:** immutability is your only real defense, not a preference — every `Fact`/`Event` must stay frozen-recursively (per the payload-design turn), because mutable aliasing is the one class of bug Python structurally cannot catch, and the only mitigation available is making the aliased thing unable to be mutated at all.

**2. Non-deterministic destruction — `__del__`/GC timing is unspecified, especially for cycles.** CPython's refcounting gives *mostly* deterministic cleanup for acyclic graphs, but any reference cycle (an `AgentState` holding a callback that closes over `AgentState` itself, say) defers to the generational cyclic collector, which runs on its own schedule — you cannot rely on "when the last reference drops" as "when cleanup happens." **Consequence:** end-of-lifetime must be an explicit, named event (`__aexit__`, a `_closed` flag checked on every call) — never something you infer from "presumably nothing references this anymore."

**3. The specific asyncio footgun this creates: dangling tasks.** `asyncio.create_task(coro)` returns a `Task` that is **only weakly referenced by the event loop** — if you don't keep a strong reference to it yourself, it can be garbage-collected mid-execution, silently cancelling work with no error raised at the call site. This is exactly the lifetime-tracking problem made concrete: nothing in the language enforces "this task's lifetime must be ≥ this scope's" the way structured concurrency's task-group does. **Consequence:** never call `create_task` bare — always either hold the reference in a set your scope owns (`self._tasks.add(task); task.add_done_callback(self._tasks.discard)`), or, better, use `asyncio.TaskGroup`/an `anyio` nursery so the *language construct itself* is the thing enforcing the containment, not your memory of "did I keep a reference."

**4. No `Send`/`Sync` — nothing marks a type as safe or unsafe to share across threads/tasks.** Rust's type system statically rejects sharing a non-`Sync` value across threads; Python has no such marker. If `EventBusState` were ever touched from two different `asyncio` tasks without an `await` point protecting the mutation, or from a real OS thread at all, nothing warns you — you get a data race indistinguishable from correct code until it isn't. **Consequence:** since you're on cooperative `asyncio` (not OS threads), the mitigation is structural rather than typed — every mutation of shared state (`EventBusManager.apply`, `WorkerManager.apply`) must complete **within one synchronous slice, with no `await` in the middle of the mutation**, so the cooperative scheduler can never interleave two mutations of the same object mid-write. This is worth auditing explicitly: does any manager's `apply` currently `await` anything internally? If none do, you're safe by construction; the moment one does, that's the seam where a real race becomes possible.

## The general design principle this all resolves to

Every one of these gaps has the same shape: Rust converts a **temporal property** (this reference must not outlive that scope; this value must not be touched from two places at once) into a **static type-level check**, resolved before the program runs. Python cannot do this, so every such property must be re-expressed as either (a) an **immutability guarantee** that makes the temporal property irrelevant (an aliased-but-frozen value can't be corrupted by aliasing), or (b) an **explicit runtime guard** that fails loudly the instant the property is violated (`_closed` flags, `assert_never`, the `Subsystem._assert_disjoint` check from two turns ago), or (c) a **structural container** that makes the violation physically impossible to express (task groups bounding task lifetime, single-owner-plus-borrow as an enforced calling convention even without compiler help). You've been doing all three throughout this conversation without naming them as the lifetime-substitute triad they are — worth treating that as the explicit checklist for every new component from here: *is this thing's problematic lifetime made irrelevant by immutability, caught by a guard, or contained by a structural scope* — if it's none of the three, that's an unenforced gap worth closing before it ships.
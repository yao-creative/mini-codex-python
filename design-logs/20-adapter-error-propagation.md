**Intent: architectural error-boundary design** — specifically, how to handle failures from **external adapters** while keeping the domain/runtime compositional.

For your Rust architecture, the best practice is:

> **Adapters produce concrete errors; the port translates them into a small application/domain error algebra at the boundary; the runtime composes `Result` without catching everything.**

### 1. Keep the adapter's error concrete

Suppose you have a storage port:

```rust
trait Storage {
    fn load(&self, id: UserId) -> Result<Option<User>, StorageError>;
}
```

The implementation can have infrastructure-specific failures:

```rust
struct SqliteStorage {
    // ...
}
```

Its internal error can contain SQLite details:

```rust
enum SqliteError {
    Connection(...),
    Query(...),
    Decode(...),
}
```

But **don't leak `SqliteError` into your domain**.

The dependency direction should be:

$$
\text{Domain}
\longleftarrow
\text{Port}
\longleftarrow
\text{Adapter}
$$

The adapter knows the port.

The port does **not** know SQLite.

---

### 2. Translate at the adapter boundary

For example:

```rust
impl Storage for SqliteStorage {
    fn load(&self, id: UserId) -> Result<Option<User>, StorageError> {
        self.query(id)
            .map_err(StorageError::from)
    }
}
```

Now the rest of your system sees:

```rust
Result<Option<User>, StorageError>
```

rather than:

```rust
Result<Option<User>, rusqlite::Error>
```

This gives you an important abstraction:

$$
\text{ConcreteError}_{adapter}
\longrightarrow
\text{PortError}
$$

The adapter is responsible for the morphism between those error algebras.

---

### 3. Don't immediately catch the error

This is the mistake I would particularly avoid:

```rust
match storage.load(id) {
    Ok(user) => ...,
    Err(_) => {
        // somehow recover
    }
}
```

at every layer.

Instead, **propagate until you reach the abstraction that actually has enough semantic information to decide what to do**.

For example:

```rust
fn load_user(
    storage: &impl Storage,
    id: UserId,
) -> Result<User, RuntimeError> {
    let user = storage
        .load(id)?
        .ok_or(RuntimeError::UserNotFound)?;

    Ok(user)
}
```

The storage adapter says:

> "I couldn't perform this storage operation."

The application layer decides:

> "What does that mean for this use case?"

That's the critical distinction.

---

## 4. Think in three error levels

For the architecture you've been designing, I'd use something like:

$$
\boxed{
\text{Infrastructure Error}
\to
\text{Port Error}
\to
\text{Application Error}
}
$$

For example:

```rust
SqliteError
    ↓
StorageError
    ↓
RuntimeError
```

But **don't mechanically create three enums for every error**.

The translation should happen only when the semantic meaning changes.

Example:

```rust
enum StorageError {
    Unavailable,
    CorruptData,
    PermissionDenied,
}
```

Then:

```rust
enum RuntimeError {
    Persistence(StorageError),
    Authentication(AuthError),
    Agent(AgentError),
    Configuration(ConfigError),
}
```

Your runtime can then compose everything:

```rust
fn run(...) -> Result<(), RuntimeError> {
    let user = storage.load(id)?;
    let identity = authenticator.authenticate()?;
    let response = agent.run(user, identity)?;
    
    ui.render(response)?;
    
    Ok(())
}
```

This is where Rust's `?` becomes extremely powerful.

---

## 5. The runtime should usually **propagate**, not catch

Your `ApplicationRuntime` shouldn't normally do:

```rust
match storage.load(...) {
    Err(e) => {
        log(e);
        recover();
    }
}
```

Instead:

```rust
storage.load(...)?
```

The runtime orchestrates.

The **policy-bearing layer** handles.

For example:

```rust
fn execute_command(...) -> Result<CommandResult, CommandError> {
    match command {
        Command::LoadConversation(id) => {
            let conversation = storage.load(id)?;
            Ok(CommandResult::Conversation(conversation))
        }

        Command::Logout => {
            authenticator.logout()?;
            Ok(CommandResult::LoggedOut)
        }
    }
}
```

Then your outermost session/TUI boundary can finally decide how to present failure:

```rust
match runtime.run(command) {
    Ok(result) => render(result),
    Err(error) => render_error(error),
}
```

So you get:

$$
\text{Adapter}
\xrightarrow{\text{failure}}
\text{Port}
\xrightarrow{?}
\text{Application}
\xrightarrow{?}
\text{Runtime}
\xrightarrow{}
\text{UI}
$$

Only the UI/session boundary needs to turn the failure into something visible to the user.

---

## 6. A useful rule for adapters

For every external dependency, ask:

> **Who has enough semantic information to decide whether this failure is recoverable?**

For example:

| Failure                     | Best place to decide             |
| --------------------------- | -------------------------------- |
| SQLite connection failed    | Application/runtime              |
| SQLite constraint violation | Adapter → semantic storage error |
| HTTP 500                    | Application retry policy         |
| HTTP 401                    | Auth/application layer           |
| Model timeout               | Agent/runtime policy             |
| Invalid JSON from API       | Adapter                          |
| User doesn't exist          | Application/domain               |
| TUI rendering failure       | Session/UI boundary              |

The adapter should **classify**, but generally shouldn't **decide application policy**.

---

## 7. External APIs are particularly important

Suppose:

```rust
trait ModelClient {
    fn complete(&self, request: Request)
        -> Result<Response, ModelError>;
}
```

Your OpenAI/Anthropic/etc. adapter might internally distinguish:

```rust
enum ProviderError {
    RateLimited { retry_after: Duration },
    Timeout,
    Authentication,
    InvalidRequest,
    ServerError,
    MalformedResponse,
}
```

You don't necessarily want all of that leaking into the agent domain.

Instead:

```rust
enum ModelError {
    Unavailable,
    RateLimited(Duration),
    Authentication,
    InvalidResponse,
}
```

Then your **runtime owns retry policy**:

```rust
match model.complete(request) {
    Ok(response) => response,

    Err(ModelError::RateLimited(delay)) => {
        retry_after(delay)
    }

    Err(ModelError::Unavailable) => {
        retry_with_backoff()
    }

    Err(error) => {
        return Err(error.into());
    }
}
```

That separation is extremely useful:

$$
\text{Adapter}
==============

\text{mechanism}
$$

$$
\text{Runtime}
==============

\text{policy}
$$

---

## 8. The architectural pattern I'd use for your project

Given your `ApplicationRuntime → UserSessionRuntime → AgentRuntime → ports → adapters` structure:

$$
\begin{aligned}
\text{External system}
&\to \text{Adapter} \
&\to \text{Port error} \
&\to \text{Agent/Application error} \
&\to \text{Runtime error} \
&\to \text{Session/UI presentation}
\end{aligned}
$$

And the control flow is mostly:

```rust
fn run(...) -> Result<_, RuntimeError> {
    let x = adapter_operation()?;
    let y = domain_operation(x)?;
    let z = another_operation(y)?;
    Ok(z)
}
```

rather than a forest of `match` statements.

### The key principle

**Don't "catch" an external error merely because you've crossed a boundary.**

Instead:

1. **Adapter:** convert implementation failure → meaningful port error.
2. **Application/domain:** convert port failure → semantic use-case error where necessary.
3. **Runtime:** apply recovery/retry/fallback policy.
4. **Outer boundary:** finally catch/handle and present the failure.

This keeps your functional core clean while making the imperative shell responsible for effects and recovery policy.

Formally, you're separating the **error algebra** from the **error-handling policy**:

$$
\underbrace{E}*{\text{what can go wrong}}
\qquad\neq\qquad
\underbrace{H:E\to\text{Policy}}*{\text{what we do about it}}
$$

That distinction is especially valuable for external adapters because the external system's failure taxonomy is almost never the right abstraction for your application's domain.

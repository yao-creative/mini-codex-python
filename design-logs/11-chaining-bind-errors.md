Your **intent** is to understand whether Rust error composition induces a **partial order / lattice of error types**, and whether that is a good architectural principle for your capability/effect system.

**Short answer:** there often *is* a useful partial order, but **Rust's type system does not automatically make error types a poset**, and I would not force every error hierarchy into one. The useful structure is usually an **information/abstraction ordering** induced by error conversion.

## 1. The `map_err` situation

Suppose:

$$
f : A \to Result(B,E_1)
$$

and the next operation expects:

$$
g : B \to Result(C,E_2)
$$

To chain them, you need to convert:

$$
E_1 \to E_2
$$

Rust:

```rust
let c = f(a)
    .map_err(AppError::from)?
    .and_then(g)?;
```

or more idiomatically:

```rust
let b = f(a).map_err(AppError::from)?;
let c = g(b)?;
```

The conversion is a function:

$$
i_{12}:E_1\to E_2
$$

If `E₂` is a more general application error, you can think of this as:

$$
E_1 \preceq E_2
$$

where "`E₁` is more specific than `E₂`."

But **this is an architectural relation, not a built-in Rust relation**.

---

# 2. Example: error abstraction

Imagine:

```rust
enum StorageError {
    NotFound,
    PermissionDenied,
    ConnectionLost,
}

enum ModelError {
    Timeout,
    InvalidResponse,
}

enum AppError {
    Storage(StorageError),
    Model(ModelError),
}
```

You have:

$$
StorageError \to AppError
$$

and:

$$
ModelError \to AppError
$$

through constructors:

```rust
impl From<StorageError> for AppError {
    fn from(e: StorageError) -> Self {
        AppError::Storage(e)
    }
}

impl From<ModelError> for AppError {
    fn from(e: ModelError) -> Self {
        AppError::Model(e)
    }
}
```

Then:

```rust
fn load_user(...) -> Result<User, StorageError>;

fn generate(...) -> Result<Response, ModelError>;
```

can be lifted to:

```rust
fn application_operation(...) -> Result<Response, AppError>
```

The structure looks like:

$$
StorageError
\longrightarrow
AppError
$$

$$
ModelError
\longrightarrow
AppError
$$

with `AppError` being a **common abstraction boundary**.

---

# 3. Is this really a poset?

You can define a relation:

$$
E_1\preceq E_2
$$

iff there exists a canonical embedding/conversion:

$$
E_1\to E_2
$$

For example:

$$
StorageError\preceq AppError
$$

and:

$$
ModelError\preceq AppError
$$

This gives you something **poset-like**.

But there is a problem.

Suppose:

$$
E_1\to E_2
$$

and:

$$
E_2\to E_1
$$

That does not necessarily mean the two Rust types are literally identical.

So to get a genuine partial order, you should quotient types by an appropriate notion of equivalence/isomorphism.

More practically, I'd call this an **error abstraction preorder** rather than claiming Rust itself gives you a poset.

---

# 4. The more useful interpretation: information ordering

There's a very good way to think about it.

Suppose:

```rust
StorageError::ConnectionLost
```

becomes:

```rust
AppError::Storage(...)
```

You haven't necessarily lost the underlying information.

But if you instead do:

```rust
AppError::ExternalFailure
```

you have deliberately thrown information away.

So you can distinguish:

$$
\text{specific error}
\longrightarrow
\text{general error}
$$

as **abstraction**.

For example:

$$
ConnectionLost
\preceq
StorageError
\preceq
AppError
$$

Conceptually:

```text
more specific
      │
      ▼
ConnectionLost
      │
      ▼
StorageError
      │
      ▼
AppError
      │
      ▼
ExternalFailure
less specific
```

I would not literally build this as an inheritance hierarchy in Rust.

It is an **architectural ordering of representations**.

---

# 5. Why this is useful

It gives you a clean rule for error boundaries.

Your low-level capability has a precise error:

```rust
trait Storage {
    fn load(...) -> Result<Value, StorageError>;
}
```

Your application layer doesn't necessarily want to know every storage implementation's errors.

So:

$$
StorageError
\to
AppError
$$

At the application boundary:

```rust
fn execute(...) -> Result<Response, AppError>
```

This gives you:

### Inside capability

High precision:

$$
StorageError
$$

### Across application boundary

Stable abstraction:

$$
AppError
$$

### At UI boundary

Potentially even more abstract:

$$
UserFacingError
$$

So you can have:

$$
StorageError
\preceq
AppError
\preceq
UserFacingError
$$

although the last conversion should usually be deliberate because it may discard diagnostic information.

---

# 6. But don't make a single giant error lattice

This is the important best-practice qualification.

I **wouldn't** design:

$$
EverythingError
$$

with hundreds of nodes.

That usually produces an error taxonomy that is harder to understand than the original problem.

Instead, define **error domains** around architectural boundaries.

For your system, something like:

$$
\begin{aligned}
StorageError &\to AppError\
ModelError &\to AppError\
AuthError &\to AppError\
ToolError &\to AppError
\end{aligned}
$$

Then:

$$
AppError
\to
RuntimeError
$$

if the runtime has a broader boundary.

This is essentially a **join structure**:

$$
AppError
\approx
StorageError
+
ModelError
+
AuthError
+
ToolError
+\cdots
$$

where `+` means coproduct/tagged union, not arithmetic.

---

# 7. Rust's `From` is the mechanism that makes this pleasant

Rust's standard pattern is:

```rust
impl From<StorageError> for AppError
```

Then:

```rust
fn foo() -> Result<Value, AppError> {
    let value = storage.load()?;
    Ok(value)
}
```

The `?` operator can use `From` to convert the error.

Conceptually:

$$
?
:
A+E_1
\to
A+E_2
$$

when Rust knows:

$$
E_1\to E_2
$$

So your earlier generalized composition:

$$
(A+E_1)
\times
(A\to B+E_2)
\to
B+E_2
$$

is implemented by error conversion.

---

# 8. What are chained error types?

This is a slightly different concept.

A **chained error** means an error contains another error as its source.

For example:

```rust
#[derive(Debug, thiserror::Error)]
enum AppError {
    #[error("failed to load conversation")]
    Storage {
        #[source]
        source: StorageError,
    },

    #[error("model request failed")]
    Model {
        #[source]
        source: ModelError,
    },
}
```

Then you can have:

$$
AppError
\supset
StorageError
\supset
IoError
$$

For example:

```text
AppError
  └── StorageError
        └── IoError
```

This is **not the same thing as an error-type poset**.

It's a **runtime causal chain**.

---

# 9. Error type vs error chain

This distinction is extremely useful.

### Error type conversion

$$
StorageError
\to
AppError
$$

means:

> "Treat this particular error as an instance of the application's error domain."

### Error source chain

$$
AppError
\supset
StorageError
\supset
IoError
$$

means:

> "This error was caused by another error."

The first is **type-level abstraction**.

The second is **runtime causal provenance**.

You generally want both.

---

# 10. Example with `thiserror`

A very idiomatic Rust design is:

```rust
#[derive(Debug, thiserror::Error)]
pub enum StorageError {
    #[error("database I/O failed")]
    Io(#[source] std::io::Error),

    #[error("conversation not found")]
    NotFound,
}
```

Then:

```rust
#[derive(Debug, thiserror::Error)]
pub enum AppError {
    #[error("storage operation failed")]
    Storage(#[source] StorageError),

    #[error("model operation failed")]
    Model(#[source] ModelError),
}
```

Now you have both structures:

### Abstraction

$$
StorageError\to AppError
$$

### Causal provenance

$$
AppError
\to StorageError
\to IoError
$$

That's excellent for diagnostics.

---

# 11. Why not just flatten everything?

You might be tempted to do:

```rust
enum AppError {
    Io,
    Database,
    Model,
    Auth,
    Tool,
}
```

and throw away the nested source.

That's usually worse.

You lose semantic information such as:

$$
AppError
\to StorageError
\to SqlError
\to IoError
$$

The chain lets you answer:

> What failed?

and:

> Why did it fail?

while the outer type answers:

> Which architectural domain owns this failure?

Those are different questions.

---

# 12. A useful error architecture for your system

Given your capability architecture, I'd use something like:

$$
\boxed{
Capability\ Error
\to
Application\ Error
\to
Runtime/UI\ Error
}
$$

For example:

$$
StorageError
\to
AppError
$$

$$
ModelError
\to
AppError
$$

$$
ToolError
\to
AppError
$$

Then:

$$
AppError
\to
RuntimeError
$$

But preserve the source chain:

$$
RuntimeError
\supset
AppError
\supset
StorageError
\supset
IoError
$$

So there are actually **two different graphs**:

### Abstraction graph

$$
StorageError \preceq AppError
$$

$$
ModelError \preceq AppError
$$

$$
ToolError \preceq AppError
$$

### Causal graph

$$
RuntimeError
\rightarrow
AppError
\rightarrow
StorageError
\rightarrow
IoError
$$

The first answers **"what abstraction boundary does this belong to?"**

The second answers **"what caused this failure?"**

That's the distinction I'd preserve in your design.

---

## 13. One final refinement: don't make errors "more general" just because they are higher-level

A good abstraction boundary should preserve the information needed by its consumer.

For example:

```rust
enum AppError {
    Storage(StorageError),
    Model(ModelError),
}
```

is usually better than:

```rust
enum AppError {
    InternalFailure,
}
```

because the former preserves the coproduct structure:

$$
AppError
=

StorageError+ModelError
$$

while the latter collapses many distinct errors into one equivalence class.

So the practical rule is:

> **Widen the error type at architectural boundaries, but preserve the original error as a source whenever it remains diagnostically meaningful.**

That gives you a controlled **error-abstraction preorder** without turning the entire application into one enormous error hierarchy.

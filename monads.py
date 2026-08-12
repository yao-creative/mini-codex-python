from collections.abc import Callable
from dataclasses import dataclass
from typing import Generic, TypeVar, Union

# Monads
T = TypeVar("T")
E = TypeVar("E")
U = TypeVar("U")


@dataclass(frozen=True)
class Ok(Generic[T]):
    value: T


@dataclass(frozen=True)
class Err(Generic[E]):
    error: E


Result = Union[Ok[T], Err[E]]


# map_ok:(T→U)→(Result[T,E]→Result[U,E])
def map_ok(r: Result[T, E], f: Callable[[T], U]) -> Result[U, E]:
    match r:
        case Ok(value=v):
            return Ok(f(v))
        case Err() as e:
            return e


def bind(r: Result[T, E], f: Callable[[T], Result[U, E]]) -> Result[U, E]:
    match r:
        case Ok(value=v):
            return f(v)
        case Err() as e:
            return e


def catching(
    f: Callable[[], T],
    error: Callable[[Exception], E],
) -> Result[T, E]:
    try:
        return Ok(f())
    except Exception as exc:
        return Err(error(exc))


# map_err: (E → U) → (Result[T, E] → Result[T, U])
def map_err(
    r: Result[T, E],
    f: Callable[[E], U],
) -> Result[T, U]:
    match r:
        case Ok():
            return r
        case Err(error=e):
            return Err(f(e))


# Generic Reader Monad:
from __future__ import annotations

R = TypeVar("R")
@dataclass(frozen=True)
class Reader(Generic[R, T]):
    run: Callable[[R], T]

    def map(self, f: Callable[[T], U]) -> Reader[R, U]:
        return Reader(lambda env: f(self.run(env)))

    def and_then(
        self,
        f: Callable[[T], Reader[R, U]],
    ) -> Reader[R, U]:
        return Reader(lambda env: f(self.run(env)).run(env))


# Writer Monad:
A = TypeVar("A")
B = TypeVar("B")
W = TypeVar("W")


@dataclass(frozen=True)
class Writer(Generic[A, W]):
    value: A
    output: W
    def map(
        self,
        f: Callable[[A], B],
    ) -> Writer[B, W]:
        return Writer(
            value=f(self.value),
            output=self.output,
        )

    def and_then(
        self,
        f: Callable[[A], Writer[B, W]],
        combine: Callable[[W, W], W],
    ) -> Writer[B, W]:
        next_result = f(self.value)

        return Writer(
            value=next_result.value,
            output=combine(
                self.output,
                next_result.output,
            ),
        )
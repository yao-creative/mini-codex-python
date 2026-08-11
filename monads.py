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


def map_err(
    r: Result[T, E],
    f: Callable[[E], U],
) -> Result[T, U]:
    match r:
        case Ok():
            return r
        case Err(error=e):
            return Err(f(e))
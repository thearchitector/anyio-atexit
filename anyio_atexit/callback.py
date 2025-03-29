import inspect
from functools import partial
from typing import TYPE_CHECKING, cast
from warnings import warn

import sniffio

if TYPE_CHECKING:  # pragma: no cover
    from types import FrameType
    from typing import Any, Awaitable, Callable

    from typing_extensions import ParamSpec, Protocol

    P = ParamSpec("P")

    class AsyncClosable(Protocol):
        def is_closed(self) -> bool: ...
        async def aclose(self) -> Any: ...


def run_finally(
    task: "Callable[P, Awaitable[None]]", *args: "P.args", **kwargs: "P.kwargs"
) -> None:
    """
    Schedule a task to run before the current async context finalizes. If using this to
    ensure resource cleanup, make sure to make your closing logic idempotent.
    """
    t: "Callable[[], Awaitable[None]]" = partial(task, *args, **kwargs)

    match sniffio.current_async_library():
        case "trio":
            import trio

            trio.lowlevel.spawn_system_task(_trio_finalize, t)
        case "asyncio":
            try:
                import asyncio_atexit
            except ImportError:
                raise RuntimeError("'asyncio-atexit' not installed.") from None

            asyncio_atexit.register(t)  # type: ignore[no-untyped-call]
        case _:
            warn("Unsupported async framework for finalizer task.", stacklevel=1)


async def _trio_finalize(task: "Callable[[], Awaitable[None]]") -> None:
    import trio

    try:
        await trio.sleep_forever()
    except trio.Cancelled:
        with trio.CancelScope(shield=True):
            await task()
        raise


def ensure_resource_closure(resource: "AsyncClosable") -> None:
    """
    Ensure that the given AsyncResource gets closed when the current async context finalizes. The resource must implemented `.is_closed` and `.aclose`.
    """
    run_finally(
        _close_resource,
        resource,
        cast("FrameType", cast("FrameType", inspect.currentframe()).f_back),
    )


async def _close_resource(
    res: "AsyncClosable", res_creation_frame: "FrameType"
) -> None:
    if not res.is_closed():
        warn(
            f"Unclosed async resource. Ensure to explicitly close resources to guarantee graceful cleanup: \n{res_creation_frame}",
            ResourceWarning,
            stacklevel=1,
        )
    await res.aclose()

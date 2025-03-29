import inspect
from typing import TYPE_CHECKING
from warnings import warn

import sniffio
from anyio.abc import AsyncResource

if TYPE_CHECKING:  # pragma: no cover
    from typing import Callable

    import trio
    from typing_extensions import ParamSpec, Protocol

    P = ParamSpec("P")

    class AsyncClosable(Protocol, AsyncResource):
        def is_closed(self) -> bool: ...


def run_finally(task: "Callable[P, None]", *args: P.args, **kwargs: P.kwargs) -> None:
    """
    Schedule a task to run before the current async context finalizes. If using this to
    ensure resource cleanup, make sure to make your closing logic idempotent.
    """
    match sniffio.current_async_library():
        case "trio":
            import trio

            trio.lowlevel.spawn_system_task(_trio_finalize, task, *args, **kwargs)
        case "asyncio":
            from functools import partial

            try:
                import asyncio_atexit
            except ImportError:
                raise RuntimeError("'asyncio-atexit' not installed.")

            asyncio_atexit.register(partial(task, *args, **kwargs))
        case _:
            warn("Unsupported async framework for finalizer task.")


async def _trio_finalize(
    task: "Callable[P, None]", *args: P.args, **kwargs: P.kwargs
) -> None:
    try:
        await trio.sleep_forever()
    except trio.Cancelled:
        with trio.CancelScope(shield=True):
            await task(*args, **kwargs)


def ensure_resource_closure(resource: "AsyncClosable") -> None:
    """
    Ensure that the given AsyncResource gets closed when the current async context finalizes. The resource must implemented `.is_closed` and `.aclose`.
    """
    run_finally(_close_resource, resource, inspect.currentframe().f_back)


async def _close_resource(res: "AsyncClosable", res_creation_frame: str) -> None:
    if not res.is_closed():
        warn(
            f"Unclosed async resource. Ensure to explicitly close resources to guarantee graceful cleanup: \n{res_creation_frame}",
            ResourceWarning,
        )
    await res.aclose()

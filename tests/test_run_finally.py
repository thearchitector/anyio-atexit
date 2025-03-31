import functools

import pytest
from anyio import run, sleep
from anyio.abc import AsyncResource
from anyio.to_thread import run_sync

from anyio_atexit.callback import run_finally

was_closed = False


class Foo(AsyncResource):
    def __init__(self, id):
        self.id = id
        self._closed = False
        run_finally(self.aclose)

    def is_closed(self):
        return self._closed

    async def aclose(self) -> None:
        if self._closed:
            return

        self._closed = True
        await sleep(0.1)
        global was_closed
        was_closed = True


async def explicit():
    async with Foo("a") as f:
        await sleep(0.1)
    assert f.is_closed()


async def implicit():
    f = Foo("a")
    await sleep(0.1)
    assert not f.is_closed()


@pytest.mark.anyio
@pytest.mark.parametrize("fn", [explicit, implicit])
async def test_run_finally(fn, anyio_backend):
    global was_closed
    was_closed = False

    await run_sync(
        functools.partial(
            run, fn, backend=anyio_backend[0], backend_options=anyio_backend[1]
        )
    )

    assert was_closed

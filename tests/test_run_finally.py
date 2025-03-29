import pytest
from anyio import AsyncResource, sleep

from anyio_atexit import run_finally


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
        print(f"done {self.id}")


@pytest.mark.anyio
async def test_run_finally():
    f = Foo("a")
    await sleep(0.1)
    # await f.aclose()

    async with Foo("b"):
        await sleep(0.1)

import sys

import pytest


@pytest.fixture(
    params=[
        pytest.param(("asyncio", {"use_uvloop": False}), id="asyncio"),
        pytest.param(
            ("asyncio", {"use_uvloop": True}),
            id="uvloop",
            marks=[
                pytest.mark.skipif(
                    sys.platform == "win32", reason="uvloop not available on windows"
                ),
            ],
        ),
        pytest.param(
            ("trio", {"restrict_keyboard_interrupt_to_checkpoints": True}), id="trio"
        ),
    ]
)
def anyio_backend(request):
    return request.param

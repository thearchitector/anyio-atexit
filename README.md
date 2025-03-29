# anyio-atexit

![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/thearchitector/anyio-atexit/test.yaml?label=tests&style=flat-square)
![PyPI - Downloads](https://img.shields.io/pypi/dm/anyio-atexit?style=flat-square)
![GitHub](https://img.shields.io/github/license/thearchitector/anyio-atexit?style=flat-square)

A small AnyIO utility for ensuring some tasks run before the current async context finishes.

This doesn't provide the same API as `atexit`, only shares a name for the sake of communicating intention.

#### Important Disclaimer:

It should be noted that this package is really intended for cases where you're porting or otherwise migrating an existing asyncio library / application to [AnyIO](https://anyio.readthedocs.io/en/stable/). The idea of unmanaged and unaccountable "global" tasks is antithetical to structured concurrency principles, so should be considered carefully. In most cases, if you have the choice, refactoring using asynchronous context managers and task groups is likely a better long-term solution.

## Installation

```bash
$ pdm add anyio-atexit
```

**Optional extras:**

- `trio` to use in a trio runtime.
- `asyncio` to use in an asyncio runtime. This installs `asyncio-atexit`.

## Usage

A common use case is to ensure some free-floating asynchronous resource (like an IO client) gets gracefully closed before the loop exits in order to release a connection.

```python
import anyio
from anyio_atexit import run_finally


class Foo:
    def __init__(self):
        # protect against users forgetting to close the client
        run_finally(self.disconnect)

    async def disconnect(self) -> None: ...


async def main():
    some_client = Foo()


anyio.run(main)
```

For anyio `AsyncResource`s, you can also use the `ensure_resource_closure` function to automatically register the `.aclose` method, as well as get resource warnings and instantiation stack traces for unclosed resources.

You must implement a sync `is_closed(self) -> bool` method for the resource to be used with `ensure_resource_closure`.

Registering a finalizer for a resource does not make the async runtime aware of explicit closures. If you register a finalizer for a resource, you are also responsible for ensuring that the resource can be closed repeatedly without error for when the finalizer runs.

```python
import anyio
from anyio_atexit import ensure_resource_closure


class Foo(AsyncResource):
    def __init__(self):
        self._closed = False
        ensure_resource_closure(self)

    def is_closed(self) -> bool:
        return self._closed

    async def aclose(self) -> None:
        if not self.is_closed():
            self._closed = True
            ...


async def main():
    some_client = Foo()


anyio.run(main)
```

## License

This software is licensed under the [Clear BSD License](LICENSE).

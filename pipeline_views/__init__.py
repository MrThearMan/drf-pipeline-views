from .views import BasePipelineView

try:
    import uvloop  # noqa

    uvloop.install()  # pragma: no cover
except Exception:  # noqa
    pass  # noqa


__all__ = [
    "BasePipelineView",
]

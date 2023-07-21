from .views import BasePipelineView

try:
    import uvloop

    uvloop.install()  # pragma: no cover
except ImportError:
    pass


__all__ = [
    "BasePipelineView",
]

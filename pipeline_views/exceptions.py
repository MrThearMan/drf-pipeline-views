from .typing import Any


__all__ = [
    "NextLogicBlock",
]


class NextLogicBlock(Exception):
    """Used to escape from pipeline logic blocks prematurely.
    Saves the kwargs that are given to it for the next step in the pipeline.
    """

    def __init__(self, **kwargs: Any):
        self.output = kwargs
        super().__init__()

    @classmethod
    def with_output(cls, output: Any):
        instance = cls()
        instance.output = output
        return instance

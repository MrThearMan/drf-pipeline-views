from typing import Any


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

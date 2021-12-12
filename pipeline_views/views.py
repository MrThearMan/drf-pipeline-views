from rest_framework import status
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from rest_framework.views import APIView

from .exceptions import NextLogicBlock
from .typing import Any, DataDict, DataReturn, Iterable, PipelineLogic, PipelinesDict, SerializerType, ViewContext
from .utils import is_serializer_class, sentinel, serializer_from_callable


__all__ = [
    "BaseAPIView",
]


class BaseAPIView(APIView):
    """Base view for pipeline views."""

    pipelines: PipelinesDict = {}
    """Dictionary describing the HTTP method pipelines."""

    def _process_request(self, data: DataDict) -> Response:
        """Process request in a pipeline-fashion."""
        pipeline = self._get_pipeline_for_current_request_method()
        data = self._run_logic(logic=pipeline, data=data)  # type: ignore

        if data:
            return Response(data=data, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _get_pipeline_for_current_request_method(self) -> PipelineLogic:
        """Get pipeline for the current HTTP method."""
        try:
            return self.pipelines[self.request.method]  # type: ignore
        except KeyError as missing_method:
            raise KeyError(f"Pipeline not configured for HTTP method '{self.request.method}'") from missing_method

    def _run_logic(self, logic: PipelineLogic, data: DataDict) -> DataReturn:
        """Run pipeline logic recursively."""
        if callable(logic):
            return logic(**data)  # type: ignore

        try:
            for step in logic:  # type: ignore
                if isinstance(data, tuple):
                    key, data = data
                    step = step[key]

                if is_serializer_class(step):
                    data = self._run_serializer(serializer_class=step, data=data)
                elif isinstance(step, Iterable) or callable(step):  # pylint: disable=W1116
                    data = self._run_logic(logic=step, data=data if data is not None else {})  # type: ignore
                else:
                    raise TypeError("Only Serializers and callables are supported in the pipeline.")

        except NextLogicBlock as premature_return:
            return premature_return.output

        return data

    def _run_serializer(self, serializer_class: SerializerType, data: DataDict) -> DataDict:
        """Build and validate a serializer"""
        serializer = self._initialize_serializer(serializer_class=serializer_class, data=data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        return data

    def get_serializer(self, *args: Any, **kwargs: Any) -> BaseSerializer:
        """Initialize serializer for current request HTTP method."""
        kwargs["serializer_class"] = self.get_serializer_class(output=kwargs.pop("output", False))
        return self._initialize_serializer(*args, **kwargs)

    def _initialize_serializer(self, serializer_class: SerializerType, *args: Any, **kwargs: Any) -> BaseSerializer:
        kwargs.setdefault("context", self.get_serializer_context())
        kwargs.setdefault("many", getattr(serializer_class, "many", False))
        if kwargs.get("data", sentinel) is None:
            kwargs["data"] = [] if kwargs["many"] else {}
        return serializer_class(*args, **kwargs)

    def get_serializer_class(self, output: bool = False) -> SerializerType:
        """Get the first step in the current HTTP method's pipeline.
        If it's a Serializer, return it. Otherwise, try to infer a serializer from the
        logic callable's parameters.
        """
        step = self._get_pipeline_for_current_request_method()

        while isinstance(step, Iterable):  # pylint: disable=W1116
            if output:
                *_, step = step
            else:
                step = next(iter(step))

        if is_serializer_class(step):
            return step  # type: ignore
        if callable(step):
            return serializer_from_callable(step, output=output)

        raise TypeError("Only Serializers and callables are supported in the pipeline.")

    def get_serializer_context(self) -> ViewContext:
        """Return serializer context, mainly for browerable api."""
        return {"request": self.request, "format": self.format_kwarg, "view": self}

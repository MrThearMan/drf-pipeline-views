from inspect import isclass

from rest_framework import status
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.views import APIView

from .exceptions import NextLogicBlock
from .typing import Any, Dict, Iterable, PipelineDefinition, PipelineLogic, PipelinesDict, Type, ViewContext
from .utils import serializer_from_callable


__all__ = [
    "BaseAPIView",
]


class BaseAPIView(APIView):
    """Base view for pipeline views."""

    pipelines: PipelinesDict = {}
    """Dictionary describing the HTTP method pipelines."""

    def _process_request(self, data: Dict[str, Any]) -> Response:
        """Process request in a pipeline-fashion."""
        pipeline = self._get_pipeline_for_current_request_method()

        for step in pipeline:
            if isclass(step):
                data = self._run_serializer(serializer_class=step, data=data)
            else:
                data = self._run_logic(logic=step, data=data)

        if data:
            return Response(data=data, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _get_pipeline_for_current_request_method(self) -> PipelineDefinition:
        """Get pipeline for the current HTTP method."""
        try:
            return self.pipelines[self.request.method]  # type: ignore
        except KeyError as missing_method:
            raise KeyError(f"Pipeline not configured for HTTP method '{self.request.method}'") from missing_method

    def _run_logic(self, logic: PipelineLogic, data: Dict[str, Any]) -> Dict[str, Any]:
        """Run pipeline logic recursively."""
        if not isinstance(logic, Iterable):
            return logic(**data) or {}

        try:
            for step in logic:
                data = self._run_logic(logic=step, data=data)
        except NextLogicBlock as premature_return:
            return premature_return.output

        return data

    def _run_serializer(self, serializer_class: Type[Serializer], data: Dict[str, Any]) -> Dict[str, Any]:
        """Build and validate a serializer"""
        serializer = self._initialize_serializer(serializer_class=serializer_class, data=data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        return data

    def get_serializer(self, *args: Any, **kwargs: Any) -> Serializer:
        """Initialize serializer for current request HTTP method."""
        kwargs["serializer_class"] = self.get_serializer_class(output=kwargs.pop("output", False))
        return self._initialize_serializer(*args, **kwargs)

    def _initialize_serializer(self, serializer_class: Type[Serializer], *args: Any, **kwargs: Any) -> Serializer:
        kwargs.setdefault("context", self.get_serializer_context())
        kwargs.setdefault("many", getattr(serializer_class, "many", False))
        return serializer_class(*args, **kwargs)

    def get_serializer_class(self, output: bool = False) -> Type[Serializer]:
        """Get the first step in the current HTTP method's pipeline.
        If it's a Serializer, return it. Otherwise, try to infer a serializer from the
        logic callable's parameters.
        """
        pipeline = self._get_pipeline_for_current_request_method()
        if output:
            *_, step = pipeline
        else:
            step = next(iter(pipeline))

        if isclass(step):
            return step

        return serializer_from_callable(step)

    def get_serializer_context(self) -> ViewContext:
        """Return serializer context, mainly for browerable api."""
        return {"request": self.request, "format": self.format_kwarg, "view": self}

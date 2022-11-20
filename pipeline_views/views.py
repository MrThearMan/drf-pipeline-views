import asyncio

from asgiref.sync import async_to_sync
from rest_framework import status
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from rest_framework.views import APIView

from .exceptions import NextLogicBlock
from .inference import serializer_from_callable
from .meta import PipelineMetadata
from .schema import PipelineSchema
from .typing import (
    Any,
    DataDict,
    DataReturn,
    Iterable,
    Optional,
    PipelineLogic,
    PipelinesDict,
    SerializerType,
    Tuple,
    ViewContext,
)
from .utils import Sentinel, get_view_method, is_pydantic_model, is_serializer_class, run_parallel, translate


__all__ = [
    "BasePipelineView",
]


class BasePipelineView(APIView):

    pipelines: PipelinesDict = {}
    """Dictionary describing the HTTP method pipelines."""

    schema = PipelineSchema()
    metadata_class = PipelineMetadata

    ignored_get_params = {"lang", "format"}
    ignored_post_params = {"csrfmiddlewaretoken", "lang", "format"}
    ignored_put_params = {"lang", "format"}
    ignored_patch_params = {"lang", "format"}
    ignored_delete_params = {"lang", "format"}

    def __new__(cls, *args, **kwargs):
        for key in cls.pipelines:
            if not hasattr(cls, key.lower()):
                setattr(cls, key.lower(), get_view_method(key))

        return super().__new__(cls)

    def process_request(self, data: DataDict) -> Response:
        """Process request in a pipeline-fashion."""
        pipeline = self.get_pipeline_for_current_request_method()

        with translate(self.request):
            data = self.run_logic(logic=pipeline, data=data)

        if data:
            return Response(data=data, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_pipeline_for_current_request_method(self) -> PipelineLogic:
        """Get pipeline for the current HTTP method."""
        try:
            return self.pipelines[self.request.method]  # type: ignore
        except KeyError as missing_method:
            raise KeyError(f"Pipeline not configured for HTTP method '{self.request.method}'") from missing_method

    def run_logic(self, logic: PipelineLogic, data: DataDict) -> DataReturn:  # noqa: C901
        """Run pipeline logic recursively."""
        if callable(logic):
            if asyncio.iscoroutinefunction(logic):
                logic = async_to_sync(logic)

            return logic(**data)

        try:
            for step in logic:

                # Conditional logic path
                if isinstance(data, tuple):
                    key, data = data
                    try:
                        step = step[key]
                    except (KeyError, TypeError) as error:
                        raise TypeError(f"Next logic step doesn't have a conditional logic path '{key}'.") from error

                # Serializer
                if is_serializer_class(step):
                    data = self.run_serializer(serializer_class=step, data=data)

                # Pydantic Model
                elif is_pydantic_model(step):
                    data = self.run_model(model_class=step, data=data)

                # Parallel block
                elif isinstance(step, tuple):
                    old_kwargs: Optional[DataDict] = None
                    try:
                        step.index(...)
                        step = tuple(task for task in step if task is not ...)
                        old_kwargs = data
                    except ValueError:
                        pass

                    results: Tuple[DataDict, ...] = async_to_sync(run_parallel)(step, data)
                    data = {key: value for result in results for key, value in result.items()}

                    if old_kwargs is not None:
                        old_kwargs.update(data)
                        data = old_kwargs

                # Logic block or callable
                elif isinstance(step, list) or callable(step):
                    data = self.run_logic(logic=step, data=data if data is not None else {})

                else:
                    raise TypeError("Only Serializers, Pydantic Models, and callables are supported in the pipeline.")

        except NextLogicBlock as premature_return:
            return premature_return.output

        return data

    def run_serializer(self, serializer_class: SerializerType, data: DataDict) -> DataDict:
        """Build and validate a serializer"""
        serializer = self.initialize_serializer(serializer_class=serializer_class, data=data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        return data

    def run_model(self, model_class: Any, data: DataDict) -> DataDict:
        """Build and validate a pydantic model"""
        return model_class(**data).dict()

    def get_serializer(self, *args: Any, **kwargs: Any) -> BaseSerializer:
        """Initialize serializer for current request HTTP method."""
        kwargs["serializer_class"] = self.get_serializer_class(output=kwargs.pop("output", False))
        return self.initialize_serializer(*args, **kwargs)

    def initialize_serializer(self, *args: Any, **kwargs: Any) -> BaseSerializer:
        serializer_class: SerializerType = kwargs.pop("serializer_class")
        kwargs.setdefault("context", self.get_serializer_context())
        kwargs.setdefault("many", getattr(serializer_class, "many", False))
        if kwargs.get("data", Sentinel) is None:
            kwargs["data"] = [] if kwargs["many"] else {}
        return serializer_class(*args, **kwargs)

    def get_serializer_class(self, output: bool = False) -> SerializerType:
        """Get the first step in the current HTTP method's pipeline.
        If it's a Serializer, return it. Otherwise, try to infer a serializer from the
        logic callable's parameters.
        """
        step = self.get_pipeline_for_current_request_method()

        while isinstance(step, Iterable):
            # Conditional block flattened
            if isinstance(step, dict):
                step = list(step.values())

            if output:
                *_, step = step
            else:
                step = next(iter(step))

        if is_serializer_class(step):
            return step

        if is_pydantic_model(step):
            return serializer_from_callable(step)

        if callable(step):
            return serializer_from_callable(step, output=output)

        raise TypeError("Only Serializers and callables are supported in the pipeline.")

    def get_serializer_context(self) -> ViewContext:
        """Return serializer context, mainly for browerable api."""
        return {"request": self.request, "format": self.format_kwarg, "view": self}

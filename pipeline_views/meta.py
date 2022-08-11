from django.utils.encoding import force_str
from rest_framework.fields import DictField, Field, SerializerMethodField
from rest_framework.metadata import SimpleMetadata
from rest_framework.request import Request, clone_request
from rest_framework.serializers import (
    HiddenField,
    ListSerializer,
    ManyRelatedField,
    ReadOnlyField,
    RelatedField,
    Serializer,
)

from .typing import TYPE_CHECKING, Dict, List, Set, Type, Union


if TYPE_CHECKING:
    from .views import BasePipelineView


__all__ = [
    "PipelineMetadata",
]


class PipelineMetadata(SimpleMetadata):
    """Metadata class that adds input and output info for
    each of the attached views methods based on
    the serializers for that method.
    """

    recognized_methods: Set[str] = {"GET", "POST", "PUT", "PATCH", "DELETE"}
    skip_fields: Set[Type[Field]] = {ReadOnlyField, HiddenField, SerializerMethodField}
    used_attrs: List[str] = ["label", "help_text", "min_length", "max_length", "min_value", "max_value"]

    def determine_actions(self, request: Request, view: "BasePipelineView"):
        """Return information about the fields that are accepted for methods in self.recognized_methods."""
        actions = {}
        for method in self.recognized_methods & set(view.allowed_methods):
            view.request = clone_request(request, method)

            input_serializer = view.get_serializer()
            output_serializer = view.get_serializer(output=True)

            actions[method] = {
                "input": self.get_serializer_info(input_serializer),
                "output": self.get_serializer_info(output_serializer),
            }

            view.request = request

        return actions

    def get_serializer_info(self, serializer: Serializer) -> Union[Dict, List]:
        """Given an instance of a serializer, return a dictionary of metadata about its fields."""
        data_serializer = getattr(serializer, "child", serializer)

        input_data = {
            field_name: self.get_field_info(field)
            for field_name, field in data_serializer.fields.items()
            if not any(isinstance(field, field_type) for field_type in self.skip_fields)
        }

        if isinstance(serializer, ListSerializer):
            input_data = [input_data]

        return input_data

    def get_field_info(self, field: Union[Field, Serializer, ListSerializer]) -> Union[Dict, List]:
        if getattr(field, "child", False):
            if isinstance(field, DictField):
                return {"<key>": self.get_field_info(field.child)}
            return [self.get_field_info(field.child)]

        if getattr(field, "fields", False):
            return self.get_serializer_info(field)

        field_info = {
            "type": self.label_lookup[field],
            "required": getattr(field, "required", False),
        }

        for attr in self.used_attrs:
            value = getattr(field, attr, None)
            if value is not None and value != "":
                info = force_str(value, strings_only=True)
                if attr == "label" and info.lower() == field.field_name.lower().replace("_", " "):
                    continue
                field_info[attr] = info

        if (
            not getattr(field, "read_only", False)
            and hasattr(field, "choices")
            and not isinstance(field, (RelatedField, ManyRelatedField))
        ):
            field_info["choices"] = list(field.choices)

        return field_info

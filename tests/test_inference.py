import pytest
from rest_framework import fields
from rest_framework.serializers import Serializer

from pipeline_views import MockSerializer
from pipeline_views.inference import (
    _parameter_types,
    _return_types,
    _snake_case_to_pascal_case,
    _to_comparable_dict,
    inline_serializer,
    serializer_from_callable,
)
from pipeline_views.typing import ForwardRef, Optional, Union
from tests.arg_spec_functions import *


def test_parameter_types():
    assert _parameter_types(function_01) == {"name": None, "age": None}
    assert _parameter_types(function_02) == {"name": int, "age": None}
    assert _parameter_types(function_03) == {"name": None, "age": int}
    assert _parameter_types(function_04) == {"name": int, "age": int}
    assert _parameter_types(function_05) == {"name": None, "age": float}
    assert _parameter_types(function_06) == {"name": int, "age": float}
    assert _parameter_types(function_07) == {"name": None, "age": int}
    assert _parameter_types(function_08) == {"name": int, "age": int}
    assert _parameter_types(function_09) == {"name": float, "age": float}
    assert _parameter_types(function_10) == {"name": int, "age": float}
    assert _parameter_types(function_11) == {"name": float, "age": int}
    assert _parameter_types(function_12) == {"name": int, "age": int}
    assert _parameter_types(function_13) == {"name": None, "age": None}
    assert _parameter_types(function_14) == {"name": int, "age": None}
    assert _parameter_types(function_15) == {"name": None, "age": int}
    assert _parameter_types(function_16) == {"name": int, "age": int}
    assert _parameter_types(function_17) == {"name": None, "age": float}
    assert _parameter_types(function_18) == {"name": int, "age": float}
    assert _parameter_types(function_19) == {"name": None, "age": int}
    assert _parameter_types(function_20) == {"name": int, "age": int}
    assert _parameter_types(function_21) == {"name": float, "age": float}
    assert _parameter_types(function_22) == {"name": int, "age": float}
    assert _parameter_types(function_23) == {"name": float, "age": int}
    assert _parameter_types(function_24) == {"name": int, "age": int}
    assert _parameter_types(function_25) == {"name": None}
    assert _parameter_types(function_26) == {"name": int}
    assert _parameter_types(function_27) == {"name": None}
    assert _parameter_types(function_28) == {"name": int}
    assert _parameter_types(function_29) == {"name": None}
    assert _parameter_types(function_30) == {"name": int}
    assert _parameter_types(function_31) == {"name": None}
    assert _parameter_types(function_32) == {"name": int}
    assert _parameter_types(function_33) == {"name": float}
    assert _parameter_types(function_34) == {"name": int}
    assert _parameter_types(function_35) == {"name": float}
    assert _parameter_types(function_36) == {"name": int}
    assert _parameter_types(function_37) == {"name": None}
    assert _parameter_types(function_38) == {"name": int}
    assert _parameter_types(function_39) == {"name": None}
    assert _parameter_types(function_40) == {"name": int}
    assert _parameter_types(function_41) == {"name": None}
    assert _parameter_types(function_42) == {"name": int}
    assert _parameter_types(function_43) == {"name": None}
    assert _parameter_types(function_44) == {"name": int}
    assert _parameter_types(function_45) == {"name": float}
    assert _parameter_types(function_46) == {"name": int}
    assert _parameter_types(function_47) == {"name": float}
    assert _parameter_types(function_48) == {"name": int}
    assert _parameter_types(function_49) == {"name": float}
    assert _parameter_types(function_50) == {"name": int}
    assert _parameter_types(function_51) == {"name": float}
    assert _parameter_types(function_52) == {"name": int}
    assert _parameter_types(function_53) == {"name": None, "age": None}
    assert _parameter_types(function_54) == {"name": int, "age": None}
    assert _parameter_types(function_55) == {"name": None, "age": int}
    assert _parameter_types(function_56) == {"name": int, "age": int}
    assert _parameter_types(function_57) == {"name": float, "age": None}
    assert _parameter_types(function_58) == {"name": int, "age": None}
    assert _parameter_types(function_59) == {"name": float, "age": int}
    assert _parameter_types(function_60) == {"name": int, "age": int}
    assert _parameter_types(function_61) == {"name": None, "age": float}
    assert _parameter_types(function_62) == {"name": int, "age": float}
    assert _parameter_types(function_63) == {"name": None, "age": int}
    assert _parameter_types(function_64) == {"name": int, "age": int}

    foo = {"age": int, "name": str}
    bar = {
        "item": foo,
        "things": [foo],
        "other": {"str": foo},
    }

    assert _parameter_types(function_78) == {"foo": {"name": str, "age": int}}
    assert _parameter_types(function_79) == {
        "foo": {
            "union": Union[int, float],
            "optional": Optional[str],
        },
    }
    assert _parameter_types(function_80) == {
        "foo": {
            "item": foo,
            "things": [foo],
            "other": {"str": foo},
        }
    }
    assert _parameter_types(function_82) == {
        "foo": {
            "weird": bar,
            "nested": [{"str": bar}],
            "another": {"str": [bar]},
        },
    }
    assert _parameter_types(function_83) == {
        "foo": {
            "weird": bar,
            "nested": [{"str": bar}],
            "another": {"str": [bar]},
        },
    }
    assert _parameter_types(function_90) == {"foo": {"name": str, "age": int}}

    # Cannot find test type from globals
    assert _parameter_types(function_94) == {"foo": {"not_available": ForwardRef("TestType")}}


def test_return_types():

    foo = {"age": int, "name": str}
    bar = {
        "item": foo,
        "things": [foo],
        "other": {"str": foo},
    }

    assert _return_types(function_84) == {"name": str, "age": int}
    assert _return_types(function_85) == {
        "union": Union[int, float],
        "optional": Optional[str],
    }
    assert _return_types(function_86) == {
        "item": foo,
        "things": [foo],
        "other": {"str": foo},
    }
    assert _return_types(function_88) == {
        "weird": bar,
        "nested": [{"str": bar}],
        "another": {"str": [bar]},
    }
    assert _return_types(function_89) == {
        "weird": bar,
        "nested": [{"str": bar}],
        "another": {"str": [bar]},
    }
    assert _return_types(function_91) == {"name": str, "age": int}
    assert _return_types(function_92) == [{"name": str, "age": int}]

    # Cannot find test type from globals
    assert _return_types(function_95) == {"not_available": ForwardRef("TestType")}


def test_serializer_from_callable():
    assert _to_comparable_dict(serializer_from_callable(function_65)()) == {"x": "CharField()"}
    assert _to_comparable_dict(serializer_from_callable(function_66)()) == {"x": "IntegerField()"}
    assert _to_comparable_dict(serializer_from_callable(function_67)()) == {"x": "FloatField()"}
    assert _to_comparable_dict(serializer_from_callable(function_68)()) == {"x": "BooleanField()"}
    assert _to_comparable_dict(serializer_from_callable(function_69)()) == {"x": "DictField()"}
    assert _to_comparable_dict(serializer_from_callable(function_70)()) == {"x": "ListField()"}
    assert _to_comparable_dict(serializer_from_callable(function_71)()) == {"x": "DateField()"}
    assert _to_comparable_dict(serializer_from_callable(function_72)()) == {"x": "DateTimeField()"}
    assert _to_comparable_dict(serializer_from_callable(function_73)()) == {"x": "TimeField()"}
    assert _to_comparable_dict(serializer_from_callable(function_74)()) == {"x": "DurationField()"}
    assert _to_comparable_dict(serializer_from_callable(function_75)()) == {
        "x": "DecimalField(decimal_places=3, max_digits=13)"
    }
    assert _to_comparable_dict(serializer_from_callable(function_76)()) == {"x": "CharField()"}
    assert _to_comparable_dict(serializer_from_callable(function_77)()) == {"x": "CharField()"}
    assert _to_comparable_dict(serializer_from_callable(function_78)()) == {
        "foo": {"name": "CharField()", "age": "IntegerField()"}
    }
    assert _to_comparable_dict(serializer_from_callable(function_79)()) == {
        "foo": {"optional": "CharField()", "union": "CharField()"}
    }
    assert _to_comparable_dict(serializer_from_callable(function_80)()) == {
        "foo": {
            "item": {"age": "IntegerField()", "name": "CharField()"},
            "other": {"str": {"age": "IntegerField()", "name": "CharField()"}},
            "things": [{"age": "IntegerField()", "name": "CharField()"}],
        }
    }
    assert _to_comparable_dict(serializer_from_callable(function_82)()) == {
        "foo": {
            "another": {
                "str": [
                    {
                        "item": {"age": "IntegerField()", "name": "CharField()"},
                        "other": {"str": {"age": "IntegerField()", "name": "CharField()"}},
                        "things": [{"age": "IntegerField()", "name": "CharField()"}],
                    }
                ]
            },
            "nested": [
                {
                    "str": {
                        "item": {"age": "IntegerField()", "name": "CharField()"},
                        "other": {"str": {"age": "IntegerField()", "name": "CharField()"}},
                        "things": [{"age": "IntegerField()", "name": "CharField()"}],
                    }
                }
            ],
            "weird": {
                "item": {"age": "IntegerField()", "name": "CharField()"},
                "other": {"str": {"age": "IntegerField()", "name": "CharField()"}},
                "things": [{"age": "IntegerField()", "name": "CharField()"}],
            },
        }
    }
    assert _to_comparable_dict(serializer_from_callable(function_83)()) == {
        "foo": {
            "another": {
                "str": [
                    {
                        "item": {"age": "IntegerField()", "name": "CharField()"},
                        "other": {"str": {"age": "IntegerField()", "name": "CharField()"}},
                        "things": [{"age": "IntegerField()", "name": "CharField()"}],
                    }
                ]
            },
            "nested": [
                {
                    "str": {
                        "item": {"age": "IntegerField()", "name": "CharField()"},
                        "other": {"str": {"age": "IntegerField()", "name": "CharField()"}},
                        "things": [{"age": "IntegerField()", "name": "CharField()"}],
                    }
                }
            ],
            "weird": {
                "item": {"age": "IntegerField()", "name": "CharField()"},
                "other": {"str": {"age": "IntegerField()", "name": "CharField()"}},
                "things": [{"age": "IntegerField()", "name": "CharField()"}],
            },
        }
    }
    assert _to_comparable_dict(serializer_from_callable(function_90)()) == {
        "foo": {"age": "IntegerField()", "name": "CharField()"}
    }
    assert _to_comparable_dict(serializer_from_callable(function_94)()) == {"foo": {"not_available": "JSONField()"}}

    assert _to_comparable_dict(serializer_from_callable(function_96)()) == {
        "foo": {
            "field": "IntegerField()",
            "other": "ListField(child=CharField())",
        }
    }


def test_serializer_from_callable__output():
    # assert to_comparable_dict(serializer_from_callable(function_84, output=True)()) == {
    #     "name": "CharField()",
    #     "age": "IntegerField()",
    # }
    # assert to_comparable_dict(serializer_from_callable(function_85, output=True)()) == {
    #     "optional": "CharField()",
    #     "union": "CharField()",
    # }
    # assert to_comparable_dict(serializer_from_callable(function_86, output=True)()) == {
    #     "item": {"age": "IntegerField()", "name": "CharField()"},
    #     "other": {"str": {"age": "IntegerField()", "name": "CharField()"}},
    #     "things": [{"age": "IntegerField()", "name": "CharField()"}],
    # }
    # assert to_comparable_dict(serializer_from_callable(function_88, output=True)()) == {
    #     "another": {
    #         "str": [
    #             {
    #                 "item": {"age": "IntegerField()", "name": "CharField()"},
    #                 "other": {"str": {"age": "IntegerField()", "name": "CharField()"}},
    #                 "things": [{"age": "IntegerField()", "name": "CharField()"}],
    #             }
    #         ]
    #     },
    #     "nested": [
    #         {
    #             "str": {
    #                 "item": {"age": "IntegerField()", "name": "CharField()"},
    #                 "other": {"str": {"age": "IntegerField()", "name": "CharField()"}},
    #                 "things": [{"age": "IntegerField()", "name": "CharField()"}],
    #             }
    #         }
    #     ],
    #     "weird": {
    #         "item": {"age": "IntegerField()", "name": "CharField()"},
    #         "other": {"str": {"age": "IntegerField()", "name": "CharField()"}},
    #         "things": [{"age": "IntegerField()", "name": "CharField()"}],
    #     },
    # }
    # assert to_comparable_dict(serializer_from_callable(function_89, output=True)()) == {
    #     "another": {
    #         "str": [
    #             {
    #                 "item": {"age": "IntegerField()", "name": "CharField()"},
    #                 "other": {"str": {"age": "IntegerField()", "name": "CharField()"}},
    #                 "things": [{"age": "IntegerField()", "name": "CharField()"}],
    #             }
    #         ]
    #     },
    #     "nested": [
    #         {
    #             "str": {
    #                 "item": {"age": "IntegerField()", "name": "CharField()"},
    #                 "other": {"str": {"age": "IntegerField()", "name": "CharField()"}},
    #                 "things": [{"age": "IntegerField()", "name": "CharField()"}],
    #             }
    #         }
    #     ],
    #     "weird": {
    #         "item": {"age": "IntegerField()", "name": "CharField()"},
    #         "other": {"str": {"age": "IntegerField()", "name": "CharField()"}},
    #         "things": [{"age": "IntegerField()", "name": "CharField()"}],
    #     },
    # }
    # assert to_comparable_dict(serializer_from_callable(function_91, output=True)()) == {
    #     "age": "IntegerField()",
    #     "name": "CharField()",
    # }
    # assert to_comparable_dict(serializer_from_callable(function_92, output=True)(many=True)) == [
    #     {"name": "CharField()", "age": "IntegerField()"},
    # ]
    # assert to_comparable_dict(serializer_from_callable(function_93, output=True)()) == {
    #     "str": {"name": "CharField()", "age": "IntegerField()"},
    # }
    # assert to_comparable_dict(serializer_from_callable(function_95, output=True)()) == {"not_available": "JSONField()"}

    assert _to_comparable_dict(serializer_from_callable(function_97, output=True)()) == {
        "field": "IntegerField()",
        "other": "ListField(child=CharField())",
    }


def test_inline_serializer__defaults():
    inline = inline_serializer("Name")

    assert issubclass(inline, Serializer)
    assert inline().fields == {}
    assert str(inline()) == "Name():"


def test_inline_serializer__subclass_another_serializer():
    inline = inline_serializer("Name", super_class=MockSerializer)

    assert issubclass(inline, MockSerializer)
    assert inline().fields == {}
    assert str(inline()) == "Name():"


def test_inline_serializer__set_attributes():
    inline = inline_serializer("Name", fields={"name": fields.CharField()})

    assert issubclass(inline, Serializer)
    assert str(inline().fields) == str({"name": fields.CharField()})
    assert str(inline()) == "Name():\n    name = CharField()"


@pytest.mark.parametrize(
    "name,result",
    [
        ["logic_method", "LogicMethod"],
        ["logic_method_", "LogicMethod"],
        ["LogicMethod", "Logicmethod"],
        ["__logic_method__", "LogicMethod"],
        ["logic__method", "LogicMethod"],
    ],
)
def test_snake_case_to_pascal_case(name, result):
    assert _snake_case_to_pascal_case(name) == result

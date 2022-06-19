from datetime import date, datetime, time, timedelta
from decimal import Decimal

# For testing functions parameters to types
from functools import wraps

from pipeline_views.typing import TYPE_CHECKING, Dict, List, Optional, TypedDict, Union


if TYPE_CHECKING:
    from tests.conftest import TestType


__all__ = [
    "function_01",
    "function_02",
    "function_03",
    "function_04",
    "function_05",
    "function_06",
    "function_07",
    "function_08",
    "function_09",
    "function_10",
    "function_11",
    "function_12",
    "function_13",
    "function_14",
    "function_15",
    "function_16",
    "function_17",
    "function_18",
    "function_19",
    "function_20",
    "function_21",
    "function_22",
    "function_23",
    "function_24",
    "function_25",
    "function_26",
    "function_27",
    "function_28",
    "function_29",
    "function_30",
    "function_31",
    "function_32",
    "function_33",
    "function_34",
    "function_35",
    "function_36",
    "function_37",
    "function_38",
    "function_39",
    "function_40",
    "function_41",
    "function_42",
    "function_43",
    "function_44",
    "function_45",
    "function_46",
    "function_47",
    "function_48",
    "function_49",
    "function_50",
    "function_51",
    "function_52",
    "function_53",
    "function_54",
    "function_55",
    "function_56",
    "function_57",
    "function_58",
    "function_59",
    "function_60",
    "function_61",
    "function_62",
    "function_63",
    "function_64",
    "function_65",
    "function_66",
    "function_67",
    "function_68",
    "function_69",
    "function_70",
    "function_71",
    "function_72",
    "function_73",
    "function_74",
    "function_75",
    "function_76",
    "function_77",
    "function_78",
    "function_79",
    "function_80",
    "function_81",
    "function_82",
    "function_83",
    "function_84",
    "function_85",
    "function_86",
    "function_87",
    "function_88",
    "function_89",
    "function_90",
    "function_91",
    "function_92",
    "function_93",
    "function_94",
    "function_95",
    "Foo",
    "Bar",
    "Barr",
    "Baz",
    "Bazz",
    "Fizz",
    "Buzz",
]


class Foo(TypedDict):
    name: str
    age: int


class Bar(TypedDict):
    item: Foo
    things: List[Foo]
    other: Dict[str, Foo]


class Barr(TypedDict):
    item: "Foo"
    things: List["Foo"]
    other: Dict[str, "Foo"]


class Baz(TypedDict):
    weird: Bar
    nested: List[Dict[str, Bar]]
    another: Dict[str, List[Bar]]


class Bazz(TypedDict):
    weird: "Barr"
    nested: List[Dict[str, "Barr"]]
    another: Dict[str, List["Barr"]]


class Fizz(TypedDict):
    union: Union[int, float]
    optional: Optional[str]


class Buzz(TypedDict):
    not_available: "TestType"


def function_01(name, age):
    pass


def function_02(name: int, age):
    pass


def function_03(name, age: int):
    pass


def function_04(name: int, age: int):
    pass


def function_05(name, age=2.0):
    pass


def function_06(name: int, age=2.0):
    pass


def function_07(name, age: int = 2.0):
    pass


def function_08(name: int, age: int = 2.0):
    pass


def function_09(name=1.0, age=2.0):
    pass


def function_10(name: int = 1.0, age=2.0):
    pass


def function_11(name=1.0, age: int = 2.0):
    pass


def function_12(name: int = 1.0, age: int = 2.0):
    pass


def function_13(*, name, age):
    pass


def function_14(*, name: int, age):
    pass


def function_15(*, name, age: int):
    pass


def function_16(*, name: int, age: int):
    pass


def function_17(*, name, age=2.0):
    pass


def function_18(*, name: int, age=2.0):
    pass


def function_19(*, name, age: int = 2.0):
    pass


def function_20(*, name: int, age: int = 2.0):
    pass


def function_21(*, name=1.0, age=2.0):
    pass


def function_22(*, name: int = 1.0, age=2.0):
    pass


def function_23(*, name=1.0, age: int = 2.0):
    pass


def function_24(*, name: int = 1.0, age: int = 2.0):
    pass


def function_25(name, *args):
    pass


def function_26(name: int, *args):
    pass


def function_27(name, *args: int):
    pass


def function_28(name: int, *args: int):
    pass


def function_29(name, **kwargs):
    pass


def function_30(name: int, **kwargs):
    pass


def function_31(name, **kwargs: int):
    pass


def function_32(name: int, **kwargs: int):
    pass


def function_33(name=1.0, **kwargs):
    pass


def function_34(name: int = 1.0, **kwargs):
    pass


def function_35(name=1.0, **kwargs: int):
    pass


def function_36(name: int = 1.0, **kwargs: int):
    pass


def function_37(name, *args, **kwargs):
    pass


def function_38(name: int, *args, **kwargs):
    pass


def function_39(name, *args: int, **kwargs):
    pass


def function_40(name: int, *args: int, **kwargs):
    pass


def function_41(name, *args, **kwargs: int):
    pass


def function_42(name: int, *args, **kwargs: int):
    pass


def function_43(name, *args: int, **kwargs: int):
    pass


def function_44(name: int, *args: int, **kwargs: int):
    pass


def function_45(name=1.0, *args, **kwargs):
    pass


def function_46(name: int = 1.0, *args, **kwargs):
    pass


def function_47(name=1.0, *args: int, **kwargs):
    pass


def function_48(name: int = 1.0, *args: int, **kwargs):
    pass


def function_49(name=1.0, *args, **kwargs: int):
    pass


def function_50(name: int = 1.0, *args, **kwargs: int):
    pass


def function_51(name=1.0, *args: int, **kwargs: int):
    pass


def function_52(name: int = 1.0, *args: int, **kwargs: int):
    pass


def function_53(name, *, age):
    pass


def function_54(name: int, *, age):
    pass


def function_55(name, *, age: int):
    pass


def function_56(name: int, *, age: int):
    pass


def function_57(name=1.0, *, age):
    pass


def function_58(name: int = 1.0, *, age):
    pass


def function_59(name=1.0, *, age: int):
    pass


def function_60(name: int = 1.0, *, age: int):
    pass


def function_61(name, *, age=2.0):
    pass


def function_62(name: int, *, age=2.0):
    pass


def function_63(name, *, age: int = 2.0):
    pass


def function_64(name: int, *, age: int = 2.0):
    pass


# For testing callables to serializers


def decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return {}

    return wrapper


def function_65(x: str):
    pass


def function_66(x: int):
    pass


def function_67(x: float):
    pass


def function_68(x: bool):
    pass


def function_69(x: dict):
    pass


def function_70(x: list):
    pass


def function_71(x: date):
    pass


def function_72(x: datetime):
    pass


def function_73(x: time):
    pass


def function_74(x: timedelta):
    pass


def function_75(x: Decimal):
    pass


def function_76(x: type):
    pass


def function_77(x: Exception):
    pass


def function_78(foo: "Foo"):
    pass


def function_79(foo: "Fizz"):
    pass


def function_80(foo: "Bar"):
    pass


def function_81(foo: "Barr"):
    pass


def function_82(foo: "Baz"):
    pass


def function_83(foo: "Bazz"):
    pass


def function_84() -> "Foo":
    pass


def function_85() -> "Fizz":
    pass


def function_86() -> "Bar":
    pass


def function_87() -> "Barr":
    pass


def function_88() -> "Baz":
    pass


def function_89() -> "Bazz":
    pass


@decorator
def function_90(foo: "Foo"):
    pass


@decorator
def function_91() -> "Foo":
    pass


def function_92() -> List["Foo"]:
    pass


def function_93() -> Dict[str, "Foo"]:
    pass


def function_94(foo: "Buzz"):
    pass


def function_95() -> "Buzz":
    pass

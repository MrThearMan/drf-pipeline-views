import pytest
from django.utils.translation import get_language
from rest_framework.fields import CharField, IntegerField
from rest_framework.serializers import Serializer

from pipeline_views.exceptions import NextLogicBlock
from pipeline_views.typing import TypedDict


def test_BaseAPIView__one_logic_callable(base_api_view):
    def callable_method(testing: int):
        return {"testing": testing * 2}

    base_api_view.request.method = "GET"
    base_api_view.pipelines = {"GET": [callable_method]}

    response = base_api_view.process_request(data={"testing": 1212})

    assert response.data == {"testing": 2424}
    assert response.status_code == 200


def test_BaseAPIView__two_logic_callables(base_api_view):
    def callable_method1(testing: int):
        return {"testing": testing * 2}

    def callable_method2(testing: int):
        return {"testing": testing * 2}

    base_api_view.request.method = "GET"
    base_api_view.pipelines = {"GET": [callable_method1, callable_method2]}

    response = base_api_view.process_request(data={"testing": 1212})

    assert response.data == {"testing": 4848}
    assert response.status_code == 200


def test_BaseAPIView__two_logic_callables__same_step(base_api_view):
    def callable_method1(testing: int):
        return {"testing": testing * 2}

    def callable_method2(testing: int):
        return {"testing": testing * 2}

    base_api_view.request.method = "GET"
    base_api_view.pipelines = {"GET": [[callable_method1, callable_method2]]}

    response = base_api_view.process_request(data={"testing": 1212})

    assert response.data == {"testing": 4848}
    assert response.status_code == 200


def test_BaseAPIView__three_logic_callables__two_in_same_step(base_api_view):
    def callable_method1(testing: int):
        return {"testing": testing * 2}

    def callable_method2(testing: int):
        return {"testing": testing * 2}

    def callable_method3(testing: int):
        return {"testing": testing * 2}

    base_api_view.request.method = "GET"
    base_api_view.pipelines = {"GET": [[callable_method1, callable_method2], callable_method3]}

    response = base_api_view.process_request(data={"testing": 1212})

    assert response.data == {"testing": 9696}
    assert response.status_code == 200


def test_BaseAPIView__three_logic_callables__recursive(base_api_view):
    def callable_method1(testing: int):
        return {"testing": testing * 2}

    def callable_method2(testing: int):
        return {"testing": testing * 2}

    def callable_method3(testing: int):
        return {"testing": testing * 2}

    base_api_view.request.method = "GET"
    base_api_view.pipelines = {"GET": [[callable_method1, [callable_method2, [callable_method3]]]]}

    response = base_api_view.process_request(data={"testing": 1212})

    assert response.data == {"testing": 9696}
    assert response.status_code == 200


def test_BaseAPIView__broken_pipeline(base_api_view):
    base_api_view.request.method = "GET"
    base_api_view.pipelines = {"GET": [1, 2, 3]}

    with pytest.raises(TypeError, match="Only Serializers and callables are supported in the pipeline."):
        base_api_view.process_request(data={"testing": 1212})


def test_BaseAPIView__get_pipeline(base_api_view):
    def callable_method(testing: int):
        return {"testing": testing * 2}

    base_api_view.request.method = "GET"
    base_api_view.pipelines = {"GET": [callable_method]}

    pipeline = base_api_view.get_pipeline_for_current_request_method()

    assert pipeline == base_api_view.pipelines["GET"]


def test_BaseAPIView__get_pipeline__no_pipeline_defined(base_api_view):
    base_api_view.request.method = "GET"

    with pytest.raises(KeyError, match="Pipeline not configured for HTTP method 'GET'"):
        base_api_view.get_pipeline_for_current_request_method()


def test_BaseAPIView__three_logic_callables__NextLogicBlock__base_level(base_api_view):
    def callable_method1(testing: int):
        return {"testing": testing * 2}

    def callable_method2(testing: int):
        raise NextLogicBlock(break_point="error")

    def callable_method3(testing: int):
        return {"testing": testing * 2}

    base_api_view.request.method = "GET"
    base_api_view.pipelines = {"GET": [callable_method1, callable_method2, callable_method3]}

    response = base_api_view.process_request(data={"testing": 1212})

    assert response.data == {"break_point": "error"}
    assert response.status_code == 200


def test_BaseAPIView__three_logic_callables__NextLogicBlock__inside_logic_block(base_api_view):
    def callable_method1(testing: int):
        return {"testing": testing * 2}

    def callable_method2(testing: int):
        raise NextLogicBlock(break_point="error")

    def callable_method3(testing: int):
        return {"testing": testing * 2}

    base_api_view.request.method = "GET"
    base_api_view.pipelines = {"GET": [[callable_method1, callable_method2, callable_method3]]}

    response = base_api_view.process_request(data={"testing": 1212})

    assert response.data == {"break_point": "error"}
    assert response.status_code == 200


def test_BaseAPIView__three_logic_callables__NextLogicBlock__next_block_exists(base_api_view):
    def callable_method1(testing: int):
        raise NextLogicBlock(testing=testing)

    def callable_method2(testing: int):
        return {"testing": testing * 2}

    def callable_method3(testing: int):
        return {"testing": testing * 2}

    base_api_view.request.method = "GET"
    base_api_view.pipelines = {"GET": [[callable_method1, callable_method2], callable_method3]}

    response = base_api_view.process_request(data={"testing": 1212})

    assert response.data == {"testing": 2424}
    assert response.status_code == 200


def test_BaseAPIView__three_logic_callables__NextLogicBlock__different_arguments(base_api_view):
    def callable_method1(testing: int):
        raise NextLogicBlock(error=123)

    def callable_method2(testing: int):
        return {"testing": testing * 2}

    def callable_method3(testing: int):
        return {"testing": testing * 2}

    base_api_view.request.method = "GET"
    base_api_view.pipelines = {"GET": [[callable_method1, callable_method2], callable_method3]}

    with pytest.raises(TypeError):
        response = base_api_view.process_request(data={"testing": 1212})


def test_BaseAPIView__three_logic_callables__NextLogicBlock__with_output(base_api_view):
    def callable_method1(testing: int):
        raise NextLogicBlock.with_output(output=["this", "is", "the", "output"])

    def callable_method2(testing: int):
        return {"testing": testing * 2}

    def callable_method3(testing: int):
        return {"testing": testing * 2}

    base_api_view.request.method = "GET"
    base_api_view.pipelines = {"GET": [[callable_method1, callable_method2, callable_method3]]}

    response = base_api_view.process_request(data={"testing": 1212})

    assert response.data == ["this", "is", "the", "output"]
    assert response.status_code == 200


def test_BaseAPIView__logic_missing_for_http_method(base_api_view):

    base_api_view.request.method = "GET"

    with pytest.raises(KeyError):
        response = base_api_view.process_request(data={"testing": 1212})


def test_BaseAPIView__logic_for_different_http_method(base_api_view):
    def callable_method1(testing: int):
        return {"testing": testing * 2}

    base_api_view.request.method = "POST"
    base_api_view.pipelines = {"GET": [callable_method1]}

    with pytest.raises(KeyError):
        response = base_api_view.process_request(data={"testing": 1212})


def test_BaseAPIView__return_204(base_api_view):
    def callable_method(testing: int):
        pass

    base_api_view.request.method = "GET"
    base_api_view.pipelines = {"GET": [callable_method]}

    response = base_api_view.process_request(data={"testing": 1212})

    assert response.data is None
    assert response.status_code == 204


def test_BaseAPIView__one_serializer(base_api_view):
    class InputSerializer(Serializer):
        name = CharField()
        age = IntegerField()

    base_api_view.request.method = "GET"
    base_api_view.pipelines = {"GET": [InputSerializer]}

    response = base_api_view.process_request(data={"name": "John", "age": 26})

    assert response.data == {"name": "John", "age": 26}
    assert response.status_code == 200


def test_BaseAPIView__one_serializer__data_is_none(base_api_view):
    class InputSerializer(Serializer):
        name = CharField(required=False)
        age = IntegerField(required=False)

    base_api_view.request.method = "GET"
    base_api_view.pipelines = {"GET": [InputSerializer]}

    response = base_api_view.process_request(data=None)

    assert response.data is None
    assert response.status_code == 204


def test_BaseAPIView__one_serializer__inside_logic_block(base_api_view):
    class InputSerializer(Serializer):
        name = CharField()
        age = IntegerField()

    base_api_view.request.method = "GET"
    base_api_view.pipelines = {"GET": [[InputSerializer]]}

    response = base_api_view.process_request(data={"name": "John", "age": 26})

    assert response.data == {"name": "John", "age": 26}
    assert response.status_code == 200


def test_BaseAPIView__two_serializers_one_logic_callable(base_api_view):
    class InputSerializer(Serializer):
        name = CharField()
        age = IntegerField()

    def callable_method1(name: str, age: int):
        return {"full_name": f"{name} Doe", "age": age}

    class OutputSerializer(Serializer):
        full_name = CharField()
        age = IntegerField()

    base_api_view.request.method = "GET"
    base_api_view.pipelines = {"GET": [InputSerializer, callable_method1, OutputSerializer]}

    response = base_api_view.process_request(data={"name": "John", "age": 26})

    assert response.data == {"full_name": "John Doe", "age": 26}
    assert response.status_code == 200


def test_BaseAPIView__two_serializers_one_logic_callable__inside_logic_block(base_api_view):
    class InputSerializer(Serializer):
        name = CharField()
        age = IntegerField()

    def callable_method1(name: str, age: int):
        return {"full_name": f"{name} Doe", "age": age}

    class OutputSerializer(Serializer):
        full_name = CharField()
        age = IntegerField()

    base_api_view.request.method = "GET"
    base_api_view.pipelines = {"GET": [[InputSerializer, callable_method1, OutputSerializer]]}

    response = base_api_view.process_request(data={"name": "John", "age": 26})

    assert response.data == {"full_name": "John Doe", "age": 26}
    assert response.status_code == 200


def test_BaseAPIView__two_serializers_one_logic_callable__output_serializer_is_list_serializer(base_api_view):
    class InputSerializer(Serializer):
        name = CharField()
        age = IntegerField()

    def callable_method1(name: str, age: int):
        return [{"full_name": f"{name} Doe", "age": age}, {"full_name": f"{name} Doe", "age": age}]

    class OutputSerializer(Serializer):
        many = True
        full_name = CharField()
        age = IntegerField()

    base_api_view.request.method = "GET"
    base_api_view.pipelines = {"GET": [InputSerializer, callable_method1, OutputSerializer]}

    response = base_api_view.process_request(data={"name": "John", "age": 26})

    assert response.data == [{"full_name": f"John Doe", "age": 26}, {"full_name": f"John Doe", "age": 26}]
    assert response.status_code == 200


def test_BaseAPIView__get_serializer(base_api_view):
    class InputSerializer(Serializer):
        name = CharField()
        age = IntegerField()

    base_api_view.request.method = "GET"
    base_api_view.pipelines = {"GET": [InputSerializer]}

    serializer = base_api_view.get_serializer()

    assert str(serializer.fields) == str({"name": CharField(), "age": IntegerField()})
    assert serializer._context == {
        "request": base_api_view.request,
        "format": base_api_view.format_kwarg,
        "view": base_api_view,
    }


def test_BaseAPIView__get_serializer__not_a_serializer(base_api_view):
    base_api_view.request.method = "GET"
    base_api_view.pipelines = {"GET": [1, 2, 3]}

    with pytest.raises(TypeError, match="Only Serializers and callables are supported in the pipeline."):
        base_api_view.get_serializer()


def test_BaseAPIView__get_serializer__infer_from_logic_callable(base_api_view):
    def callable_method1(name: str, age: int) -> int:
        pass

    base_api_view.request.method = "GET"
    base_api_view.pipelines = {"GET": [callable_method1]}

    serializer = base_api_view.get_serializer()

    assert str(serializer.fields) == "{'name': CharField(), 'age': IntegerField()}"
    assert serializer._context == {
        "request": base_api_view.request,
        "format": base_api_view.format_kwarg,
        "view": base_api_view,
    }
    assert type(serializer).__name__ == "CallableMethod1Serializer"


def test_BaseAPIView__get_serializer__infer_from_logic_callable__inside_logic_block(base_api_view):
    def callable_method1(name: str, age: int) -> int:
        pass

    base_api_view.request.method = "GET"
    base_api_view.pipelines = {"GET": [[callable_method1]]}

    serializer = base_api_view.get_serializer()

    assert str(serializer.fields) == "{'name': CharField(), 'age': IntegerField()}"
    assert serializer._context == {
        "request": base_api_view.request,
        "format": base_api_view.format_kwarg,
        "view": base_api_view,
    }
    assert type(serializer).__name__ == "CallableMethod1Serializer"


def test_BaseAPIView__get_serializer__infer_from_logic_callable__typeddict(base_api_view):
    class InnerOutput(TypedDict):
        bar: int

    class Output(TypedDict):
        testing: int
        inner: InnerOutput

    def callable_method1(foo: Output) -> int:
        pass

    base_api_view.request.method = "GET"
    base_api_view.pipelines = {"GET": [callable_method1]}

    serializer = base_api_view.get_serializer()

    assert str(serializer.fields) == (
        "{'foo': foo():\n" "    testing = IntegerField()\n" "    inner = inner():\n" "        bar = IntegerField()}"
    )
    assert serializer._context == {
        "request": base_api_view.request,
        "format": base_api_view.format_kwarg,
        "view": base_api_view,
    }
    assert type(serializer).__name__ == "CallableMethod1Serializer"


def test_BaseAPIView__get_serializer__output_serializer(base_api_view):
    class InputSerializer(Serializer):
        name = CharField()
        age = IntegerField()

    def callable_method1(name: str, age: int):
        return {"full_name": f"{name} Doe", "age": age}

    class OutputSerializer(Serializer):
        full_name = CharField()
        age = IntegerField()

    base_api_view.request.method = "GET"
    base_api_view.pipelines = {"GET": [InputSerializer, callable_method1, OutputSerializer]}

    serializer = base_api_view.get_serializer(output=True)

    assert str(serializer.fields) == str({"full_name": CharField(), "age": IntegerField()})
    assert serializer._context == {
        "request": base_api_view.request,
        "format": base_api_view.format_kwarg,
        "view": base_api_view,
    }


def test_BaseAPIView__get_serializer__output_serializer__infer_from_logic_callable(base_api_view):
    class InnerOutput(TypedDict):
        foo: int

    class Output(TypedDict):
        testing: int
        inner: InnerOutput

    def callable_method1(param1: int):
        return {"param2": param1 * 2}

    def callable_method2(param2: int):
        return {"param3": param2 * 2}

    def callable_method3(param3: int) -> Output:
        return {"testing": param3 * 2, "inner": {"foo": 1}}

    base_api_view.request.method = "GET"
    base_api_view.pipelines = {"GET": [[callable_method1, callable_method2, callable_method3]]}

    serializer = base_api_view.get_serializer(output=True)

    assert str(serializer.fields) == ("{'testing': IntegerField(), 'inner': inner():\n    foo = IntegerField()}")
    assert serializer._context == {
        "request": base_api_view.request,
        "format": base_api_view.format_kwarg,
        "view": base_api_view,
    }


@pytest.mark.parametrize("key,result", [[1, 20], [2, 40]])
def test_BaseAPIView__conditional(base_api_view, key: int, result: int):
    def callable_method1(param: int):
        return key, {"param": param}

    def callable_method2(param: int):
        return {"result": param * 2}

    def callable_method3(param: int):
        return {"result": param * 4}

    base_api_view.request.method = "GET"
    base_api_view.pipelines = {"GET": [callable_method1, {1: callable_method2, 2: callable_method3}]}

    response = base_api_view.process_request(data={"param": 10})

    assert response.data == {"result": result}
    assert response.status_code == 200


@pytest.mark.parametrize("key,result", [[1, 20], [2, 40]])
def test_BaseAPIView__conditional__inside_logic_block(base_api_view, key: int, result: int):
    def callable_method1(param: int):
        return key, {"param": param}

    def callable_method2(param: int):
        return {"result": param * 2}

    def callable_method3(param: int):
        return {"result": param * 4}

    base_api_view.request.method = "GET"
    base_api_view.pipelines = {"GET": [[callable_method1, {1: callable_method2, 2: callable_method3}]]}

    response = base_api_view.process_request(data={"param": 10})

    assert response.data == {"result": result}
    assert response.status_code == 200


@pytest.mark.parametrize("key,result", [[0, 20], [1, 40]])
def test_BaseAPIView__conditional__select_only_one_method_from_next_logic_block(base_api_view, key: int, result: int):
    def callable_method1(param: int):
        return key, {"param": param}

    def callable_method2(param: int):
        return {"param": param * 2}

    def callable_method3(param: int):
        return {"param": param * 4}

    base_api_view.request.method = "GET"
    base_api_view.pipelines = {"GET": [callable_method1, [callable_method2, callable_method3]]}

    response = base_api_view.process_request(data={"param": 10})

    assert response.data == {"param": result}
    assert response.status_code == 200


def test_BaseAPIView__conditional__no_conditional_path(base_api_view):
    def callable_method1(param: int):
        return 3, {"param": param}

    def callable_method2(param: int):
        return {"result": param * 2}

    def callable_method3(param: int):
        return {"result": param * 4}

    base_api_view.request.method = "GET"
    base_api_view.pipelines = {"GET": [callable_method1, {1: callable_method2, 2: callable_method3}]}

    with pytest.raises(TypeError, match="Next logic step doesn't have a conditional logic path '3'."):
        base_api_view.process_request(data={"param": 10})


def test_BaseAPIView__conditional__next_step_is_not_conditional_path(base_api_view):
    def callable_method1(param: int):
        return 1, {"param": param}

    def callable_method2(param: int):
        return {"result": param * 2}

    def callable_method3(param: int):
        return {"result": param * 4}

    base_api_view.request.method = "GET"
    base_api_view.pipelines = {"GET": [callable_method1, callable_method2, callable_method3]}

    with pytest.raises(TypeError, match="Next logic step doesn't have a conditional logic path '1'."):
        base_api_view.process_request(data={"param": 10})


def test_BaseAPIView__translated_en(base_api_view):
    def callable_method():
        return {"lang": str(get_language())}

    base_api_view.request.method = "GET"
    base_api_view.request.LANGUAGE_CODE = "en"
    base_api_view.pipelines = {"GET": [callable_method]}

    response = base_api_view.process_request(data={})

    assert response.data == {"lang": "en"}
    assert response.status_code == 200


def test_BaseAPIView__translated_fi(base_api_view):
    def callable_method():
        return {"lang": str(get_language())}

    base_api_view.request.method = "GET"
    base_api_view.request.LANGUAGE_CODE = "fi"
    base_api_view.pipelines = {"GET": [callable_method]}

    response = base_api_view.process_request(data={})

    assert response.data == {"lang": "fi"}
    assert response.status_code == 200


def test_BaseAPIView__one_logic_coroutine(base_api_view):
    async def callable_method(testing: int):
        return {"testing": testing * 2}

    base_api_view.request.method = "GET"
    base_api_view.pipelines = {"GET": [callable_method]}

    response = base_api_view.process_request(data={"testing": 1212})

    assert response.data == {"testing": 2424}
    assert response.status_code == 200


def test_BaseAPIView__three_logic_coroutines__two_in_parallel(base_api_view):
    async def callable_method1(testing: int):
        return {"testing": testing * 2}

    async def callable_method2(testing: int):
        return {"foo": testing * 2}

    async def callable_method3(testing: int):
        return {"bar": testing * 4}

    base_api_view.request.method = "GET"
    base_api_view.pipelines = {"GET": [callable_method1, (callable_method2, callable_method3)]}

    response = base_api_view.process_request(data={"testing": 1212})

    assert response.data == {"foo": 4848, "bar": 9696}
    assert response.status_code == 200


def test_BaseAPIView__three_logic_coroutines__two_in_parallel__pass_values_from_previous_step(base_api_view):
    async def callable_method1(testing: int):
        return {"testing": testing * 2}

    async def callable_method2(testing: int):
        return {"foo": testing * 2}

    async def callable_method3(testing: int):
        return {"bar": testing * 4}

    base_api_view.request.method = "GET"
    base_api_view.pipelines = {"GET": [callable_method1, (callable_method2, callable_method3, ...)]}

    response = base_api_view.process_request(data={"testing": 1212})

    assert response.data == {"testing": 2424, "foo": 4848, "bar": 9696}
    assert response.status_code == 200

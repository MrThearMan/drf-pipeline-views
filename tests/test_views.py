import pytest
from rest_framework.fields import CharField, IntegerField
from rest_framework.serializers import Serializer

from pipeline_views.exceptions import NextLogicBlock


def test_BaseAPIView__one_logic_callable(base_api_view):
    def callable_method(testing: int):
        return {"testing": testing * 2}

    base_api_view.request.method = "GET"
    base_api_view.pipelines = {"GET": [callable_method]}

    response = base_api_view._process_request(data={"testing": 1212})

    assert response.data == {"testing": 2424}
    assert response.status_code == 200


def test_BaseAPIView__two_logic_callables(base_api_view):
    def callable_method1(testing: int):
        return {"testing": testing * 2}

    def callable_method2(testing: int):
        return {"testing": testing * 2}

    base_api_view.request.method = "GET"
    base_api_view.pipelines = {"GET": [callable_method1, callable_method2]}

    response = base_api_view._process_request(data={"testing": 1212})

    assert response.data == {"testing": 4848}
    assert response.status_code == 200


def test_BaseAPIView__two_logic_callables__same_step(base_api_view):
    def callable_method1(testing: int):
        return {"testing": testing * 2}

    def callable_method2(testing: int):
        return {"testing": testing * 2}

    base_api_view.request.method = "GET"
    base_api_view.pipelines = {"GET": [(callable_method1, callable_method2)]}

    response = base_api_view._process_request(data={"testing": 1212})

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
    base_api_view.pipelines = {"GET": [(callable_method1, callable_method2), callable_method3]}

    response = base_api_view._process_request(data={"testing": 1212})

    assert response.data == {"testing": 9696}
    assert response.status_code == 200


def test_BaseAPIView__three_logic_callables__next_step_prematurely__no_next_step(base_api_view):
    def callable_method1(testing: int):
        return {"testing": testing * 2}

    def callable_method2(testing: int):
        raise NextLogicBlock(break_point="error")

    def callable_method3(testing: int):
        return {"testing": testing * 2}

    base_api_view.request.method = "GET"
    base_api_view.pipelines = {"GET": [(callable_method1, callable_method2, callable_method3)]}

    response = base_api_view._process_request(data={"testing": 1212})

    assert response.data == {"break_point": "error"}
    assert response.status_code == 200


def test_BaseAPIView__three_logic_callables__next_step_prematurely__next_step_exists(base_api_view):
    def callable_method1(testing: int):
        raise NextLogicBlock(testing=testing)

    def callable_method2(testing: int):
        return {"testing": testing * 2}

    def callable_method3(testing: int):
        return {"testing": testing * 2}

    base_api_view.request.method = "GET"
    base_api_view.pipelines = {"GET": [(callable_method1, callable_method2), callable_method3]}

    response = base_api_view._process_request(data={"testing": 1212})

    assert response.data == {"testing": 2424}
    assert response.status_code == 200


def test_BaseAPIView__three_logic_callables__next_step_prematurely__different_arguments(base_api_view):
    def callable_method1(testing: int):
        raise NextLogicBlock(error=123)

    def callable_method2(testing: int):
        return {"testing": testing * 2}

    def callable_method3(testing: int):
        return {"testing": testing * 2}

    base_api_view.request.method = "GET"
    base_api_view.pipelines = {"GET": [(callable_method1, callable_method2), callable_method3]}

    with pytest.raises(TypeError):
        response = base_api_view._process_request(data={"testing": 1212})


def test_BaseAPIView__logic_missing_for_http_method(base_api_view):

    base_api_view.request.method = "GET"

    with pytest.raises(KeyError):
        response = base_api_view._process_request(data={"testing": 1212})


def test_BaseAPIView__logic_for_different_http_method(base_api_view):
    def callable_method1(testing: int):
        return {"testing": testing * 2}

    base_api_view.request.method = "POST"
    base_api_view.pipelines = {"GET": [callable_method1]}

    with pytest.raises(KeyError):
        response = base_api_view._process_request(data={"testing": 1212})


def test_BaseAPIView__return_204(base_api_view):
    def callable_method(testing: int):
        pass

    base_api_view.request.method = "GET"
    base_api_view.pipelines = {"GET": [callable_method]}

    response = base_api_view._process_request(data={"testing": 1212})

    assert response.data is None
    assert response.status_code == 204


def test_BaseAPIView__one_serializer(base_api_view):
    class InputSerializer(Serializer):
        name = CharField()
        age = IntegerField()

    base_api_view.request.method = "GET"
    base_api_view.pipelines = {"GET": [InputSerializer]}

    response = base_api_view._process_request(data={"name": "John", "age": 26})

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

    response = base_api_view._process_request(data={"name": "John", "age": 26})

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

    response = base_api_view._process_request(data={"name": "John", "age": 26})

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


def test_BaseAPIView__get_serializer__infer_from_logic_callable(base_api_view):
    def callable_method1(name: str, age: int):
        pass

    base_api_view.request.method = "GET"
    base_api_view.pipelines = {"GET": [callable_method1]}

    serializer = base_api_view.get_serializer()

    assert str(serializer.fields) == str({"name": CharField(), "age": IntegerField()})
    assert serializer._context == {
        "request": base_api_view.request,
        "format": base_api_view.format_kwarg,
        "view": base_api_view,
    }
    assert type(serializer).__name__ == "CallableMethod1Serializer"

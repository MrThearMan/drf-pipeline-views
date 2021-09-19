from rest_framework.fields import CharField, IntegerField

from pipeline_views.serializers import MockSerializer


def test_mock_serializer():
    serializer = MockSerializer(data={"testing": 1212})
    serializer.is_valid(raise_exception=True)
    validated_data = serializer.validated_data
    data = serializer.data

    assert validated_data == {"testing": 1212}
    assert data == {"testing": 1212}


def test_mock_serializer__subclass__used_like_reqular_serializer():
    class SubSerializer(MockSerializer):
        name = CharField()
        age = IntegerField()

    serializer = SubSerializer(data={"name": "John", "age": 26})
    serializer.is_valid(raise_exception=True)
    validated_data = serializer.validated_data
    data = serializer.data

    assert validated_data == {"name": "John", "age": 26}
    assert data == {"name": "John", "age": 26}


def test_mock_serializer__subclass__fields_are_skipped():
    class SubSerializer(MockSerializer):
        name = CharField()
        age = IntegerField()

    serializer = SubSerializer(data={"testing": 123, "age": "unknown"})
    serializer.is_valid(raise_exception=True)
    validated_data = serializer.validated_data
    data = serializer.data

    assert validated_data == {"testing": 123, "age": "unknown"}
    assert data == {"testing": 123, "age": "unknown"}

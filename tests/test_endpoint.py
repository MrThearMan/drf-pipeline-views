from rest_framework.test import APIClient, APIRequestFactory

from tests.django.urls import ExampleView


def test_example_endpoint__APIRequestFactory():
    factory = APIRequestFactory()
    view = ExampleView.as_view()

    request = factory.post("/api/example/", {"name": "Matti", "age": 26}, format="json")
    response = view(request)

    assert response.data == {"email": "matti@email.com", "age": 26}


def test_example_endpoint__APIClient():
    client = APIClient()

    response = client.post("/api/example/", {"name": "Matti", "age": 26}, format="json")

    assert response.data == {"email": "matti@email.com", "age": 26}

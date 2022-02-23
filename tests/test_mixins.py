from pipeline_views.mixins import DeleteMixin, GetMixin, PatchMixin, PostMixin, PutMixin
from pipeline_views.views import BasePipelineView


def test_get_mixin(drf_request):
    def callable_method(testing: int):
        return {"testing": testing * 2}

    class BasicView(GetMixin, BasePipelineView):

        pipelines = {"GET": [callable_method]}

    drf_request._request.GET["testing"] = 1212
    drf_request._request.GET["format"] = "foo"
    drf_request.method = "GET"

    view = BasicView()
    view.request = drf_request
    view.format_kwarg = None

    response = view.get(drf_request)

    assert response.data == {"testing": 2424}
    assert response.status_code == 200


def test_post_mixin(drf_request):
    def callable_method(testing: int):
        return {"testing": testing * 2}

    class BasicView(PostMixin, BasePipelineView):

        pipelines = {"POST": [callable_method]}

    drf_request._full_data = {"testing": 1212, "csrfmiddlewaretoken": "foo"}
    drf_request.method = "POST"

    view = BasicView()
    view.request = drf_request
    view.format_kwarg = None

    response = view.post(drf_request)

    assert response.data == {"testing": 2424}
    assert response.status_code == 200


def test_patch_mixin(drf_request):
    def callable_method(testing: int):
        return {"testing": testing * 2}

    class BasicView(PatchMixin, BasePipelineView):

        pipelines = {"PATCH": [callable_method]}

    drf_request._full_data = {"testing": 1212, "format": "foo"}
    drf_request.method = "PATCH"

    view = BasicView()
    view.request = drf_request
    view.format_kwarg = None

    response = view.patch(drf_request)

    assert response.data == {"testing": 2424}
    assert response.status_code == 200


def test_put_mixin(drf_request):
    def callable_method(testing: int):
        return {"testing": testing * 2}

    class BasicView(PutMixin, BasePipelineView):

        pipelines = {"PUT": [callable_method]}

    drf_request._full_data = {"testing": 1212, "format": "foo"}
    drf_request.method = "PUT"

    view = BasicView()
    view.request = drf_request
    view.format_kwarg = None

    response = view.put(drf_request)

    assert response.data == {"testing": 2424}
    assert response.status_code == 200


def test_delete_mixin(drf_request):
    def callable_method(testing: int):
        return {"testing": testing * 2}

    class BasicView(DeleteMixin, BasePipelineView):

        pipelines = {"DELETE": [callable_method]}

    drf_request._full_data = {"testing": 1212, "format": "foo"}
    drf_request.method = "DELETE"

    view = BasicView()
    view.request = drf_request
    view.format_kwarg = None

    response = view.delete(drf_request)

    assert response.data == {"testing": 2424}
    assert response.status_code == 200

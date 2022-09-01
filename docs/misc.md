# Miscellaneous

## Modifying endpoint data

If you wish to add data to a request, you can do that on the endpoint
level by overriding `process_request`, or on the endpoint HTTP method
level by overriding the specific method, like `get`.

```python
from rest_framework.exceptions import NotAuthenticated
from rest_framework.authentication import get_authorization_header
from pipeline_views import BasePipelineView
from pipeline_views.utils import get_view_method


class BasicView(BasePipelineView):
    pipelines = {
        "GET": ...
    }

    def get(self, request, *args, **kwargs):
        # Add language to every get request for this endpoint
        kwargs["lang"] = request.LANGUAGE_CODE
        # View method needs to be added manually, since we defined `get` ourselves
        return get_view_method("GET")(self, request, *args, **kwargs)

    def process_request(self, data):
        # Add authorization token to every http method
        data["token"] = self.token_from_headers()
        return super().process_request(data=data)

    def token_from_headers(self):
        auth_header = get_authorization_header(self.request)
        if not auth_header:
            raise NotAuthenticated("You must be logged in for this endpoint.")
        return auth_header.split()[1].decode()
```

## Translation

The pipeline use a `translate` context manager to enable translations based on what the
client is asking for. Use the `LANGUAGES` setting in django to define supported languages.
Used language is determined from 1. a `lang` query parameter, or 2. `request.LANGUAGE_CODE`
fetched from Accept-Language header (requires [LocaleMiddleware]). Failing that, the
tranlation falls back to the currently active language.

## Ignoring input parameters

If some endpoint input parameter is not required in the pipeline logic, it can be ignored
from the input data by placing it in a corresponding set on the endpoint level:

```python hl_lines="5 6 8 9"
from pipeline_views import BasePipelineView


class BasicView(BasePipelineView):
    # Redefine ignored values
    ignored_get_params = {...}

    # Extend the ignored values
    ignored_post_params = BasePipelineView.ignored_post_params | {...}

    pipelines = {
        "GET": ...,
        "POST": ...
    }
```

By default, the ignored keys include: "format" (used by DRF Rendered classes)
and "lang" (used by `@translate` decorator) parameters. POST requests also ignore the
`csrfmiddlewaretoken` given by forms.

[LocaleMiddleware]: https://docs.djangoproject.com/en/dev/ref/middleware/#django.middleware.locale.LocaleMiddleware
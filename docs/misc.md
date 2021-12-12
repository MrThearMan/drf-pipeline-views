# Miscellaneous

## Modifying endpoint data

If you wish to add data to a request, you can do that on the endpoint level by overriding
`_process_request`, or on the endpoint HTTP method level by overriding the spesific method, like `get`.

```python
from rest_framework.exceptions import NotAuthenticated
from rest_framework.authentication import get_authorization_header
from pipeline_views import BaseAPIView, GetMixin


class BasicView(GetMixin, BaseAPIView):

    pipelines = {"GET": ...}

    def get(self, request, *args, **kwargs):
        # Add language to every get request for this endpoint
        kwargs["lang"] = request.LANGUAGE_CODE
        return super().get(request, *args, **kwargs)

    def _process_request(self, data):
        # Add authorization token to every http method
        data["token"] = self._token_from_headers()
        return super()._process_request(data)

    def _token_from_headers(self):
        auth_header = get_authorization_header(self.request)
        if not auth_header:
            raise NotAuthenticated("You must be logged in for this endpoint.")
        return auth_header.split()[1].decode()
```

## Translation

The HTTP method mixins use a `@translate` decorator to enable translations based on what the
client is asking for. Use the `LANGUAGES` setting in django to define supported languages.
Used language is determined from 1. a `lang` query parameter, or 2. `request.LANGUAGE_CODE` fetched from Accept-Language header
(requires [LocaleMiddleware](https://docs.djangoproject.com/en/3.1/ref/middleware/#django.middleware.locale.LocaleMiddleware)).
Failing that, the tranlation falls back to English (i.e. no translation), or to the first language in the `LANGUAGES`
setting if English is not an option.


## Ignoring input parameters

If some endpoint input parameter is not required in the pipeline logic, it can be ignored
from the input data by placing it in a set on the endpoint level:

```python
from pipeline_views import BaseAPIView, GetMixin, PostMixin


class BasicView(GetMixin, PostMixin, BaseAPIView):
    ignored_get_params = {...}  # Redefine ignored values
    ignored_post_params = PostMixin.ignored_post_params | {...}  # Extend the ignored values

    pipelines = {
        "GET": ...,
        "POST": ...
    }
```

By default, the mixin classes ignore the "format" (used by DRF Rendered classes)
and "lang" (used by `@translate` decorator) parameters. POST mixin class also ignores the
`csrfmiddlewaretoken` given by forms.


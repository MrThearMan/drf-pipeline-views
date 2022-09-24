# Django REST Framework Pipeline Views

[![Coverage Status][coverage-badge]][coverage]
[![Workflow Status][status-badge]][status]
[![PyPI][pypi-badge]][pypi]
[![Licence][licence-badge]][licence]
[![Last Commit][commit-badge]][repo]
[![Issues][issues-badge]][issues]
[![Downloads][downloads-badge]][pypi]

[![Python Version][version-badge]][pypi]
[![Django Version][django-badge]][pypi]
[![DRF Version][drf-badge]][pypi]

```shell
pip install drf-pipeline-views
```

---

**Documentation**: [https://mrthearman.github.io/drf-pipeline-views/](https://mrthearman.github.io/drf-pipeline-views/)

**Source Code**: [https://github.com/MrThearMan/drf-pipeline-views/](https://github.com/MrThearMan/drf-pipeline-views/)

---

Inspired by a talk on [The Clean Architecture in Python][clean] by Brandon Rhodes,
**drf-pipeline-views** aims to simplify writing testable API endpoints with
[Django REST framework][drf] using the *[Pipeline Design Pattern][pipeline]*.

The main idea behind the pipeline pattern is to process data in steps. Input from the previous step
is passed to the next, resulting in a collection of "_data-in, data-out_" -functions. These functions
can be easily unit tested, since none of the functions depend on the state of the objects in the other parts
of the pipeline. Furthermore, IO can be separated into its own step, making the other parts of the
logic simpler and faster to test by not having to mock or do any other special setup around the IO.
This also means that the IO block, or in fact any other part of the application, can be replaced as long as the
data flowing through the pipeline remains the same.

```python
from pipeline_views import BasePipelineView

from .my_serializers import InputSerializer, OutputSerializer
from .my_validators import validator
from .my_services import io_func, logging_func, integration_func


class SomeView(BasePipelineView):
    pipelines = {
        "GET": [
            InputSerializer,
            validator,
            io_func,
            integration_func,
            logging_func,
            OutputSerializer,
        ],
    }
```

Have a look at the [quickstart][quickstart] section in the documentation on basic usage.

[clean]: https://archive.org/details/pyvideo_2840___The_Clean_Architecture_in_Python
[drf]: https://www.django-rest-framework.org/
[pipeline]: https://java-design-patterns.com/patterns/pipeline/
[quickstart]: https://mrthearman.github.io/drf-pipeline-views/quickstart

[coverage-badge]: https://coveralls.io/repos/github/MrThearMan/drf-pipeline-views/badge.svg?branch=main
[status-badge]: https://img.shields.io/github/workflow/status/MrThearMan/drf-pipeline-views/Test
[pypi-badge]: https://img.shields.io/pypi/v/drf-pipeline-views
[licence-badge]: https://img.shields.io/github/license/MrThearMan/drf-pipeline-views
[commit-badge]: https://img.shields.io/github/last-commit/MrThearMan/drf-pipeline-views
[issues-badge]: https://img.shields.io/github/issues-raw/MrThearMan/drf-pipeline-views
[version-badge]: https://img.shields.io/pypi/pyversions/drf-pipeline-views
[downloads-badge]: https://img.shields.io/pypi/dm/drf-pipeline-views
[django-badge]: https://img.shields.io/pypi/djversions/drf-pipeline-views
[drf-badge]: https://img.shields.io/badge/drf%20versions-3.12%20%7C%203.13%20%7C%203.14-blue

[coverage]: https://coveralls.io/github/MrThearMan/drf-pipeline-views?branch=main
[status]: https://github.com/MrThearMan/drf-pipeline-views/actions/workflows/test.yml
[pypi]: https://pypi.org/project/drf-pipeline-views
[licence]: https://github.com/MrThearMan/drf-pipeline-views/blob/main/LICENSE
[repo]: https://github.com/MrThearMan/drf-pipeline-views/commits/main
[issues]: https://github.com/MrThearMan/drf-pipeline-views/issues
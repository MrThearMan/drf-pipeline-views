# Django REST Framework Pipeline Views

[![Coverage Status](https://coveralls.io/repos/github/MrThearMan/drf-pipeline-views/badge.svg?branch=main)](https://coveralls.io/github/MrThearMan/drf-pipeline-views?branch=main)
[![GitHub Workflow Status](https://img.shields.io/github/workflow/status/MrThearMan/drf-pipeline-views/Tests)](https://github.com/MrThearMan/drf-pipeline-views/actions/workflows/main.yml)
[![PyPI](https://img.shields.io/pypi/v/drf-pipeline-views)](https://pypi.org/project/drf-pipeline-views)
[![GitHub](https://img.shields.io/github/license/MrThearMan/drf-pipeline-views)](https://github.com/MrThearMan/drf-pipeline-views/blob/main/LICENSE)
[![GitHub last commit](https://img.shields.io/github/last-commit/MrThearMan/drf-pipeline-views)](https://github.com/MrThearMan/drf-pipeline-views/commits/main)
[![GitHub issues](https://img.shields.io/github/issues-raw/MrThearMan/drf-pipeline-views)](https://github.com/MrThearMan/drf-pipeline-views/issues)


[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/drf-pipeline-views)](https://pypi.org/project/drf-pipeline-views)
[![PyPI - Django Version](https://img.shields.io/pypi/djversions/drf-pipeline-views)](https://pypi.org/project/drf-pipeline-views)
[![Custom - Django REST Framework Version](https://img.shields.io/badge/drf%20versions-3.7%20%7C%203.8%20%7C%203.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue)](https://pypi.org/project/drf-pipeline-views)

```shell
pip install drf-pipeline-views
```
---

**Documentation**: [https://mrthearman.github.io/drf-pipeline-views/](https://mrthearman.github.io/drf-pipeline-views/)

**Source Code**: [https://github.com/MrThearMan/drf-pipeline-views](https://github.com/MrThearMan/drf-pipeline-views)

---

Inspired by a talk on [The Clean Architecture in Python](https://archive.org/details/pyvideo_2840___The_Clean_Architecture_in_Python)
by Brandon Rhodes, **drf-pipeline-views** aims to simplify writing testable API endpoints with
[Django REST framework](https://www.django-rest-framework.org/) using the
*[Pipeline Design Pattern](https://java-design-patterns.com/patterns/pipeline/)*.

The main idea behind the pipeline pattern is to process data in steps. Input from the previous step
is passed to the next, resulting in a collection of "data-in, data-out" -functions. These functions
can be easily unit tested, since none of the functions depend on the state of the objects in the other parts
of the pipeline. Furthermore, IO can be separated into its own step, making the other parts of the
logic simpler and faster to test by not having to mock or do any other special setup around the IO.
This also means that the IO block, or in fact any other part of the application, can be replaced as long as the
data flowing through the pipeline remains the same.

Have a look at the [quickstart](https://mrthearman.github.io/drf-pipeline-views/quickstart)
section in the documentation on basic usage.

# Quickstart

## Example

Let's create a basic pipeline. For this contrived example we are going to build
a pipeline that takes product reviews from users, saves them to our database,
contacts some outside system for recommendations based on the given review, and
responds with the user's review and recommendation.

It's a good idea to first define an InputSerializer, and an OutputSerializer that define
the input and output of the pipeline respectively. This forces verification of the incoming
and outcoming data, so that if something changes in the pipeline, or some unexpected values
are produced, the endpoint will break instead of creating side effects in the application
using the API.

```python title="serializers.py"
from django.contrib.auth.models import User
from rest_framework import serializers


class ReviewInputSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    score = serializers.ChoiceField(choices=[1, 2, 3, 4, 5])
    review = serializers.CharField()
    user = serializers.SerializerMethodField()

    # Current request object is always included
    # in the serializer context
    def get_user(self, obj) -> User:
        return self.context["request"].user


class ReviewOutputSerializer(serializers.Serializer):

    class RecommendationSerializer(serializers.Serializer):
        product_id = serializers.CharField()
        avg_score = serializers.FloatField()

    score = serializers.ChoiceField(choices=[1, 2, 3, 4, 5])
    review = serializers.CharField()
    recommendations = RecommendationSerializer(many=True)


```

Now let's create the pipeline steps that will be handling. The implementations
details are just made up and not important here, rather the separation of logic.

```python title="services.py"
from uuid import UUID
from typing import TypedDict

import requests
from django.contrib.auth.models import User
from .models import Product, Review


class Recommencation(TypedDict):
    product_id: str
    avg_score: float


def review_product(product_id: UUID, score: int, review: str, user: User):
    product = Product.objects.get(product_id)
    user_review = Review.objects.add_review(product, user, score, review)

    return {"product": product, "review": user_review}

def get_recommendations(product: Product, review: Review):
    payload = {"product": str(product.id), "score": review.score}
    response = requests.get("...", params=payload)
    data: list[Recommencation] = response.json()

    return {
        "score": review.score,
        "review": review.content,
        "recommendations": data
    }
```

Finally, let's put those together in the pipeline.

```python title="views.py"
from pipeline_views import BasePipelineView, PostMixin
from .serializers import ReviewInputSerializer, ReviewOutputSerializer
from .services import review_product, get_recommendations


class SomeView(PostMixin, BasePipelineView):

    pipelines = {
        "POST": [
            ReviewInputSerializer,
            add_review_for_product,
            get_recommendations,
            ReviewOutputSerializer,
        ],
    }
```

---

## A Closer Look

Notice that the output from the previous function is used as the input of for
the next function.

```python hl_lines="5 6 7"
def review_product(product_id: UUID, score: int, review: str, user: User):
    product = Product.objects.get(product_id)
    user_review = Review.objects.add_review(product, user, score, review)

    return {"product": product, "review": user_review}

def get_recommendations(product: Product, review: Review):
    payload = {"product": str(product.id), "score": review.score}
    response = requests.get("...", params=payload)
    data: list[Recommencation] = response.json()

    return {
        "score": review.score,
        "review": review.content,
        "recommendations": data
    }
```

Depending on your needs, you might want to reuse a logic fuction in a different context,
and you might not always give the same input. You can make the functions more generic
by specifying `**kwargs`.

```python hl_lines="1 2 3 4 5 12 13 14"
def review_product(**kwargs):
    product_id: UUID = kwargs["product_id"]
    score: int = kwargs["score"]
    review: str = kwargs["review"]
    user: User = kwargs["user"]

    product = Product.objects.get(product_id)
    user_review = Review.objects.add_review(product, user, score, review)

    return {"product": product, "review": user_review}

def get_recommendations(**kwargs):
    product: Product = kwargs["product"]
    review: Review = kwargs["review"]

    payload = {"product": str(product.id), "score": review.score}
    response = requests.get("...", params=payload)
    data: list[Recommencation] = response.json()

    return {
        "score": review.score,
        "review": review.content,
        "recommendations": data
    }
```

You can even make functions that are only used to verify input,
but do not modify the output at all (or only add data to it).

```python
def validate_data(**kwargs):

    # Validation goes here.
    # Might raise an exception,
    # which interrupts the pipeline.

    return kwargs

```

Another point no note is that the functions are easily testable.
`review_product` can be tested without mocking the GET request
to the outside system, `get_recommendations` can be tested
without making database queries. Some functions, like validators,
have no side effects, which makes them easy and fast to unit test.

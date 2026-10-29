from app.models.review import Review


def test_convert_review():
    raw_data = {
        "asin": "B0FFGXYXQV",
        "rating": 5,
        "review_header": "Works well",
        "review_text": "Easy to install.",
        "is_verified": True,
    }

    review = Review.model_validate(raw_data)

    assert review.asin == "B0FFGXYXQV"
    assert review.rating == 5
    assert review.is_verified is True
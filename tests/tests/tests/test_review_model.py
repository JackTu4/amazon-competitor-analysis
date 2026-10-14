from app.models.review import Review, ReviewCollection


def test_review_model():
    review = Review(
        asin="B0FFGXYXQV",
        rating=5,
        review_header="Works well",
        review_text="Easy to install and works as expected.",
        is_verified=True,
    )

    assert review.rating == 5
    assert review.review_text is not None


def test_review_collection():
    collection = ReviewCollection(
        asin="B0FFGXYXQV",
        reviews=[
            Review(
                rating=5,
                review_text="Works well",
            ),
            Review(
                rating=2,
                review_text="The drive failed.",
            ),
        ],
    )
    assert len(collection.reviews) == 2
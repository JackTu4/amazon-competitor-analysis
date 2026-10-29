from app.models.review import Review
from app.analyzers.user_analyzer import analyze_user_reviews
def test_analyze_user_reviews():
    reviews = [
        Review(
            rating=5,
            review_header="Works well",
            review_text="Easy to install and works as expected.",
        ),
        Review(
            rating=2,
            review_header="Drive failed",
            review_text="The drive stopped working.",
        ),
        Review(
            rating=3,
            review_header="Slow performance",
            review_text="Performance is lower than expected.",
        ),
    ]
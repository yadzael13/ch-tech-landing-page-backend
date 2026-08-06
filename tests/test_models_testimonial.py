import pytest
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.testimonial import Testimonial


async def test_testimonial_accepts_a_null_rating(db_session: AsyncSession) -> None:
    testimonial = Testimonial(author_name="Ada Lovelace", content="Great work.")
    db_session.add(testimonial)
    await db_session.commit()

    assert testimonial.rating is None


@pytest.mark.parametrize("rating", [1, 5])
async def test_testimonial_accepts_boundary_ratings(
    db_session: AsyncSession, rating: int
) -> None:
    testimonial = Testimonial(
        author_name="Ada Lovelace", content="Great work.", rating=rating
    )
    db_session.add(testimonial)
    await db_session.commit()

    assert testimonial.rating == rating


@pytest.mark.parametrize("rating", [-5, 0, 6, 100])
async def test_testimonial_rejects_a_rating_outside_1_to_5(
    db_session: AsyncSession, rating: int
) -> None:
    db_session.add(
        Testimonial(author_name="Ada Lovelace", content="Great work.", rating=rating)
    )
    # MySQL raises CHECK constraint violations as OperationalError (error
    # 3819), not IntegrityError like Postgres.
    with pytest.raises(OperationalError):
        await db_session.commit()

import pytest

from app import create_app
from app.entity import (
    IDP,
    AuditLog,
    Category,
    CompanyInfo,
    Enquiry,
    EnquiryMessage,
    Favourite,
    IDPFlag,
    IDPPhoto,
    LoginAttempt,
    Review,
    ShortlistEvent,
    UserAccount,
    UserProfile,
    ViewEvent,
    db,
)
from app.seed import DEMO_USERNAMES, SEED_PASSWORD, seed_database
from tests.helpers import TEST_CONFIG

MAIN_ENTITIES = [
    UserProfile,
    UserAccount,
    LoginAttempt,
    CompanyInfo,
    Category,
    IDP,
    IDPPhoto,
    Favourite,
    Enquiry,
    EnquiryMessage,
    Review,
    IDPFlag,
    AuditLog,
]


@pytest.fixture(scope="module")
def seeded():
    app = create_app(TEST_CONFIG)
    with app.app_context():
        seed_database()
        yield
        db.session.remove()
        db.drop_all()


@pytest.mark.parametrize("entity", MAIN_ENTITIES, ids=lambda e: e.__name__)
def test_at_least_100_rows_per_main_entity(seeded, entity):
    assert db.session.query(entity).count() >= 100


def test_events_are_plentiful_and_span_the_last_90_days(seeded):
    assert db.session.query(ViewEvent).count() >= 5000
    assert db.session.query(ShortlistEvent).count() > db.session.query(Favourite).count()
    oldest = db.session.query(db.func.min(ViewEvent.viewed_at)).scalar()
    newest = db.session.query(db.func.max(ViewEvent.viewed_at)).scalar()
    assert (newest - oldest).days >= 80


def test_demo_accounts_log_in_with_seed_password(seeded):
    for role, username in DEMO_USERNAMES.items():
        account = UserAccount.find_by_username(username)
        assert account.role == role
        assert account.check_password(SEED_PASSWORD)
        assert account.can_log_in()


def test_every_review_follows_a_designer_reply(seeded):
    for review in db.session.query(Review):
        reply = (
            db.session.query(EnquiryMessage)
            .join(Enquiry)
            .filter(
                Enquiry.customer_id == review.customer_id,
                Enquiry.designer_id == review.designer_id,
                EnquiryMessage.sender_id == review.designer_id,
            )
            .first()
        )
        assert reply is not None

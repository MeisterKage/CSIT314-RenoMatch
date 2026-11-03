import re
from collections import Counter
from datetime import timedelta
from pathlib import Path

import pytest

import app as app_package
from app import create_app
from app.control.validation import email_problem, phone_problem, username_problem
from app.entity import (
    AuditLogEntity,
    CategoryEntity,
    CompanyInfoEntity,
    EnquiryEntity,
    EnquiryMessageEntity,
    FavouriteEntity,
    IDPEntity,
    IDPFlagEntity,
    LoginAttemptEntity,
    PlatformActivityEntity,
    ReviewEntity,
    UserAccountEntity,
    UserProfileEntity,
    db,
)
from app.entity.db import utcnow
from app.entity.idp import IDP_STAGES, IDP_STATUSES, PROPERTY_TYPES, STYLES
from app.entity.idp_flag import FLAG_STATUSES
from app.seed import DEMO_USERNAMES, SEED_PASSWORD, seed_database
from tests.helpers import TEST_CONFIG

MAIN_ENTITIES = [
    UserProfileEntity,
    UserAccountEntity,
    LoginAttemptEntity,
    CompanyInfoEntity,
    CategoryEntity,
    IDPEntity,
    FavouriteEntity,
    PlatformActivityEntity,
    EnquiryEntity,
    EnquiryMessageEntity,
    ReviewEntity,
    IDPFlagEntity,
    AuditLogEntity,
]
STATIC_DIR = Path(app_package.__file__).parent / "boundary" / "static"
PHOTO_URL = re.compile(r"/static/img/idp/idp-(0[1-9]|[12][0-9]|3[0-2])\.jpg")


def seeded_photo_urls() -> dict[int, list[str]]:
    return {idp.idpId: idp.photoUrls for idp in db.session.query(IDPEntity)}


@pytest.fixture(scope="module")
def seeded():
    app = create_app(TEST_CONFIG)
    with app.app_context():
        seed_database()
        yield
        db.session.remove()
        db.drop_all()
        db.engine.dispose()


def activities(activity_type):
    return db.session.query(PlatformActivityEntity).filter_by(activityType=activity_type)


def status_shares(entity) -> dict[str, float]:
    rows = [row[0] for row in db.session.query(entity.status)]
    return {status: count / len(rows) for status, count in Counter(rows).items()}


@pytest.mark.parametrize("entity", MAIN_ENTITIES, ids=lambda e: e.__name__)
def test_at_least_100_rows_per_main_entity(seeded, entity):
    assert db.session.query(entity).count() >= 100


def test_view_and_shortlist_activity_is_plentiful_and_spans_90_days(seeded):
    assert activities("view").count() >= 7500
    assert activities("shortlist").count() >= 1400
    assert activities("shortlist").count() > db.session.query(FavouriteEntity).count()
    timestamps = [a.timestamp for a in activities("view")]
    assert (max(timestamps) - min(timestamps)).days >= 80
    assert min(timestamps) >= utcnow() - timedelta(days=91)


def test_register_enquiry_review_and_idp_activity_match_their_records(seeded):
    assert activities("register").count() == db.session.query(UserAccountEntity).count()
    assert activities("enquiry").count() == db.session.query(EnquiryEntity).count()
    assert activities("review").count() == db.session.query(ReviewEntity).count()
    assert activities("idp_added").count() == db.session.query(IDPEntity).count()


def test_idp_counters_equal_their_activity_counts(seeded):
    for activity_type, counter in (("view", "viewCount"), ("shortlist", "shortlistCount")):
        counted = Counter(a.idpId for a in activities(activity_type))
        for idp in db.session.query(IDPEntity):
            assert getattr(idp, counter) == counted[idp.idpId], (idp.idpId, counter)


def test_every_idp_has_one_to_three_pool_photos(seeded):
    for idp in db.session.query(IDPEntity):
        assert 1 <= len(idp.photoUrls) <= 3
        assert len(set(idp.photoUrls)) == len(idp.photoUrls)
        for url in idp.photoUrls:
            assert PHOTO_URL.fullmatch(url), url
            assert (STATIC_DIR / url.removeprefix("/static/")).is_file(), url


def test_photo_urls_are_deterministic(seeded):
    first = seeded_photo_urls()
    other = create_app(TEST_CONFIG)
    with other.app_context():
        seed_database()
        second = seeded_photo_urls()
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
    assert first == second


def test_exactly_six_active_idps_are_featured_with_a_date(seeded):
    featured = db.session.query(IDPEntity).filter_by(isFeatured=True).all()
    assert len(featured) == 6
    assert all(idp.status == "Active" and idp.featuredDate is not None for idp in featured)
    unfeatured = db.session.query(IDPEntity).filter_by(isFeatured=False)
    assert all(idp.featuredDate is None for idp in unfeatured)


def test_about_ten_percent_of_designers_opt_out_of_the_weekly_summary(seeded):
    designers = [a for a in db.session.query(UserAccountEntity) if a.role == "designer"]
    opted_out = [a for a in designers if not a.weeklySummaryOptIn]
    assert 0.08 <= len(opted_out) / len(designers) <= 0.12
    assert UserAccountEntity.findByUsername(DEMO_USERNAMES["designer"]).weeklySummaryOptIn


def test_accounts_are_mostly_active_with_about_four_percent_suspended(seeded):
    shares = status_shares(UserAccountEntity)
    assert set(shares) == {"Active", "Suspended"}
    assert 0.02 <= shares["Suspended"] <= 0.06


def test_categories_are_95_percent_active(seeded):
    assert status_shares(CategoryEntity) == {"Active": 0.95, "Suspended": 0.05}


def test_idps_are_92_percent_active_4_suspended_4_removed(seeded):
    assert status_shares(IDPEntity) == {"Active": 0.92, "Suspended": 0.04, "Removed": 0.04}


def test_an_idp_is_removed_exactly_when_a_flag_on_it_is_upheld(seeded):
    upheld = {f.idpId for f in db.session.query(IDPFlagEntity).filter_by(status="Upheld")}
    removed = {i.idpId for i in db.session.query(IDPEntity).filter_by(status="Removed")}
    assert upheld == removed


def test_seeded_statuses_use_the_spec_strings(seeded):
    assert {p.status for p in db.session.query(UserProfileEntity)} == {"Active", "Suspended"}
    assert {f.status for f in db.session.query(IDPFlagEntity)} == set(FLAG_STATUSES)


def test_demo_accounts_log_in_with_seed_password(seeded):
    for role, username in DEMO_USERNAMES.items():
        account = UserAccountEntity.findByUsername(username)
        assert account.role == role
        assert account.checkPassword(SEED_PASSWORD)
        assert account.canLogIn()


def test_seeded_accounts_pass_validation(seeded):
    for account in db.session.query(UserAccountEntity):
        assert username_problem(account.username) is None
        assert email_problem(account.email) is None
        assert phone_problem(account.phone) is None


def test_seeded_idps_use_allowed_enum_values(seeded):
    for idp in db.session.query(IDPEntity):
        assert idp.style in STYLES
        assert idp.propertyType in PROPERTY_TYPES
        assert idp.stage in IDP_STAGES
        assert idp.status in IDP_STATUSES
        assert isinstance(idp.budget, float)


def test_every_review_follows_a_designer_reply(seeded):
    for review in db.session.query(ReviewEntity):
        reply = (
            db.session.query(EnquiryMessageEntity)
            .join(EnquiryEntity)
            .filter(
                EnquiryEntity.userId == review.userId,
                EnquiryEntity.designerId == review.designerId,
                EnquiryMessageEntity.senderId == review.designerId,
            )
            .first()
        )
        assert reply is not None

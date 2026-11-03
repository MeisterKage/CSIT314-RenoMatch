"""US-38 to US-42: portfolio controllers, including each branch of the US-38 sequence."""

from io import BytesIO

import pytest
from werkzeug.datastructures import FileStorage

from app.control.add_idp_controller import AddIDPController
from app.control.delete_idp_controller import DeleteIDPController
from app.control.search_my_idps_controller import SearchMyIDPsController
from app.control.update_idp_controller import UpdateIDPController
from app.control.view_my_idp_controller import ViewMyIDPController
from app.entity import IDPEntity, PlatformActivityEntity, db
from tests.helpers import GIF_BYTES, jpeg_bytes, png_bytes

MB = 1024 * 1024


def upload(name="room.png", data=None, content_type="image/png"):
    stream = BytesIO(data if data is not None else png_bytes())
    return FileStorage(stream=stream, filename=name, content_type=content_type)


@pytest.fixture
def details(make_account, make_category):
    designer, category = make_account(role="designer"), make_category()

    def _details(**fields):
        values = {
            "designerId": designer.userId,
            "title": "Bright kitchen",
            "description": "Open plan.",
            "categoryId": str(category.categoryId),
            "style": "Modern",
            "propertyType": "HDB",
            "budget": "30000",
            "location": "Bishan",
        }
        values.update(fields)
        return values

    _details.designer, _details.category = designer, category
    return _details


def test_controllers_hold_the_entity_class():
    for controller in (
        AddIDPController,
        SearchMyIDPsController,
        ViewMyIDPController,
        UpdateIDPController,
        DeleteIDPController,
    ):
        assert controller().entity is IDPEntity


def test_valid_details_validate_then_call_the_entity_in_order(details, monkeypatch):
    calls = []
    controller = AddIDPController()
    realValidate, realAdd = controller.validateIDP, IDPEntity.addIDP.__func__

    def validate(idp, photos):
        calls.append("validateIDP")
        return realValidate(idp, photos)

    def add(cls, idp, photos):
        calls.append("entity.addIDP")
        return realAdd(cls, idp, photos)

    monkeypatch.setattr(controller, "validateIDP", validate)
    monkeypatch.setattr(IDPEntity, "addIDP", classmethod(add))
    assert controller.addIDP(details(), [upload()]) is True
    assert calls == ["validateIDP", "entity.addIDP"]


def test_valid_details_create_the_idp_with_photo_urls_and_activity(details):
    assert AddIDPController().addIDP(details(), [upload(), upload("b.jpg", jpeg_bytes())]) is True
    idp = IDPEntity.query.one()
    assert (idp.title, idp.budget, idp.status) == ("Bright kitchen", 30000.0, "Active")
    assert idp.stage == "Current"
    assert idp.designerId == details.designer.userId
    assert len(idp.photoUrls) == 2
    assert all(url.startswith("/uploads/") for url in idp.photoUrls)
    assert idp.photoUrls[0].endswith(".png") and idp.photoUrls[1].endswith(".jpg")
    activity = PlatformActivityEntity.query.filter_by(activityType="idp_added").one()
    assert (activity.userId, activity.idpId) == (details.designer.userId, idp.idpId)


def test_6a_missing_fields_returns_the_field_names_and_skips_the_entity(details, monkeypatch):
    called = []
    monkeypatch.setattr(IDPEntity, "addIDP", classmethod(lambda cls, i, p: called.append(1)))
    result = AddIDPController().addIDP(details(title="", location=" "), [upload()])
    assert result == ["title", "location"]
    assert called == []
    assert IDPEntity.query.count() == 0


def test_validate_idp_returns_a_boolean_and_records_the_reason(details):
    controller = AddIDPController()
    assert controller.validateIDP(details(), [upload()]) is True
    assert controller.validateIDP(details(title=""), [upload()]) is False
    assert controller.missingFields == ["title"]


def test_6a_no_photo_counts_as_a_missing_field(details):
    assert AddIDPController().addIDP(details(), []) == ["photos"]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("budget", "abc"),
        ("budget", "-5"),
        ("style", "Gothic"),
        ("propertyType", "Igloo"),
        ("categoryId", "x"),
        ("stage", "Someday"),
    ],
)
def test_6a_invalid_detail_values_are_reported_as_fields(details, field, value):
    assert AddIDPController().addIDP(details(**{field: value}), [upload()]) == [field]


@pytest.mark.parametrize(
    "photo",
    [
        lambda: upload("a.gif", GIF_BYTES, "image/gif"),
        lambda: upload("a.png", b"not an image at all"),
        lambda: upload("a.txt", png_bytes(), "text/plain"),
        lambda: upload("a.png", png_bytes(5 * MB), "image/png"),
        lambda: upload("a.jpg", png_bytes(), "image/jpeg"),
    ],
)
def test_6b_invalid_photo_returns_a_message_and_saves_nothing(details, photo):
    result = AddIDPController().addIDP(details(), [upload(), photo()])
    assert isinstance(result, str)
    assert IDPEntity.query.count() == 0


def test_exactly_5_mb_is_accepted(details):
    exact = png_bytes(5 * MB - len(png_bytes()))
    assert len(exact) == 5 * MB
    assert AddIDPController().addIDP(details(), [upload(data=exact)]) is True


def test_6c_suspended_category_returns_false_and_saves_nothing(details):
    details.category.status = "Suspended"
    db.session.commit()
    assert AddIDPController().addIDP(details(), [upload()]) is False
    assert IDPEntity.query.count() == 0
    assert PlatformActivityEntity.query.filter_by(activityType="idp_added").count() == 0


def test_search_lists_own_non_removed_idps_by_keyword(make_idp, make_account):
    me, other = make_account(role="designer"), make_account(role="designer")
    make_idp(designer=me, title="Calm study")
    make_idp(designer=me, title="Loud kitchen", status="Suspended")
    make_idp(designer=me, title="Calm gone", status="Removed")
    make_idp(designer=other, title="Calm theirs")
    controller = SearchMyIDPsController()
    everything = {i.title for i in controller.searchMyIDPs(me.userId, "")}
    assert everything == {"Calm study", "Loud kitchen"}
    assert {i.title for i in controller.searchMyIDPs(me.userId, "  calm ")} == {"Calm study"}
    assert len(controller.searchMyIDPs(me.userId, None)) == 2
    assert controller.searchMyIDPs(me.userId, "zzz") == []


def test_get_my_idp_is_owner_only_and_hides_removed(make_idp, make_account):
    me, other = make_account(role="designer"), make_account(role="designer")
    idp, gone = make_idp(designer=me), make_idp(designer=me, status="Removed")
    controller = ViewMyIDPController()
    assert controller.getMyIDP(me.userId, idp.idpId).idpId == idp.idpId
    assert controller.getMyIDP(other.userId, idp.idpId) is None
    assert controller.getMyIDP(me.userId, gone.idpId) is None
    assert controller.getMyIDP(me.userId, 9999) is None


def test_update_changes_details_and_adds_and_removes_photos(details):
    AddIDPController().addIDP(details(), [upload(), upload("b.png")])
    idp = IDPEntity.query.one()
    first, second = idp.photoUrls
    changed = details(title="New title", budget="41000", removePhotos=[first])
    result = UpdateIDPController().updateIDP(
        details.designer.userId, idp.idpId, changed, [upload("c.png")]
    )
    assert result is True
    idp = db.session.get(IDPEntity, idp.idpId)
    assert (idp.title, idp.budget) == ("New title", 41000.0)
    assert len(idp.photoUrls) == 2
    assert second in idp.photoUrls
    assert first not in idp.photoUrls


def test_update_keeps_at_least_one_photo(details):
    AddIDPController().addIDP(details(), [upload()])
    idp = IDPEntity.query.one()
    result = UpdateIDPController().updateIDP(
        details.designer.userId, idp.idpId, details(removePhotos=list(idp.photoUrls)), []
    )
    assert result == ["photos"]
    assert len(db.session.get(IDPEntity, idp.idpId).photoUrls) == 1


def test_update_results_for_each_problem(details, make_account, make_category):
    AddIDPController().addIDP(details(), [upload()])
    idp = IDPEntity.query.one()
    designerId, update = details.designer.userId, UpdateIDPController().updateIDP
    assert update(designerId, idp.idpId, details(title=""), []) == ["title"]
    assert isinstance(update(designerId, idp.idpId, details(), [upload("a.gif", GIF_BYTES)]), str)
    suspended = make_category(status="Suspended")
    moved = details(categoryId=str(suspended.categoryId))
    assert update(designerId, idp.idpId, moved, []) is False
    assert update(make_account(role="designer").userId, idp.idpId, details(), []) is None
    assert update(designerId, 9999, details(), []) is None


def test_delete_marks_removed_clears_featured_and_checks_owner(make_idp, make_account):
    me, other = make_account(role="designer"), make_account(role="designer")
    idp = make_idp(designer=me, isFeatured=True)
    controller = DeleteIDPController()
    assert controller.deleteIDP(other.userId, idp.idpId) is False
    assert db.session.get(IDPEntity, idp.idpId).status == "Active"
    assert controller.deleteIDP(me.userId, idp.idpId) is True
    idp = db.session.get(IDPEntity, idp.idpId)
    assert (idp.status, idp.isFeatured) == ("Removed", False)
    assert controller.deleteIDP(me.userId, idp.idpId) is False

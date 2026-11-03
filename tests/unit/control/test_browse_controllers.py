"""US-01, US-09, US-10, US-11: controllers for browsing."""

from app.control.browse_idps_controller import BrowseIDPsController
from app.control.search_idps_controller import SearchIDPsController
from app.control.view_designer_profile_controller import ViewDesignerProfileController
from app.control.view_idp_details_controller import ViewIDPDetailsController
from app.entity import CompanyInfoEntity, IDPEntity, ReviewEntity, db


def test_browse_controller_lists_active_idps(make_idp):
    hit = make_idp()
    make_idp(status="Suspended")
    page = BrowseIDPsController().getActiveIDPs(1)
    assert [idp.idpId for idp in page.items] == [hit.idpId]


def test_search_controller_filters(make_idp):
    hit = make_idp(style="Luxury")
    make_idp(style="Modern")
    page = SearchIDPsController().searchIDPs(None, None, "Luxury", None, None, None)
    assert [idp.idpId for idp in page.items] == [hit.idpId]


def test_controllers_hold_the_entity_class():
    assert BrowseIDPsController().entity is IDPEntity
    assert SearchIDPsController().entity is IDPEntity
    assert ViewIDPDetailsController().entity is IDPEntity


def test_view_idp_details_records_the_view(make_idp, make_account):
    idp = make_idp()
    result = ViewIDPDetailsController().viewIDPDetails(idp.idpId, make_account().userId)
    assert result.viewCount == 1


def test_view_idp_details_skips_designer_and_hides_non_active(make_idp):
    idp = make_idp()
    assert ViewIDPDetailsController().viewIDPDetails(idp.idpId, idp.designerId).viewCount == 0
    hidden = make_idp(status="Removed")
    assert ViewIDPDetailsController().viewIDPDetails(hidden.idpId, None) is None


def test_view_designer_profile(make_account, make_idp):
    designer = make_account(role="designer")
    db.session.add(CompanyInfoEntity(designerId=designer.userId, name="Studio X"))
    db.session.add(ReviewEntity(designerId=designer.userId, userId=make_account().userId, rating=4))
    db.session.commit()
    idp = make_idp(designer=designer)
    make_idp(designer=designer, status="Removed")
    profile = ViewDesignerProfileController().viewDesignerProfile(designer.userId)
    assert profile.designer.userId == designer.userId
    assert profile.company.name == "Studio X"
    assert [i.idpId for i in profile.idps] == [idp.idpId]
    assert profile.averageRating == 4.0
    assert len(profile.reviews) == 1


def test_view_designer_profile_rejects_non_designers(make_account):
    customer = make_account()
    suspended = make_account(role="designer", status="Suspended")
    controller = ViewDesignerProfileController()
    assert controller.viewDesignerProfile(customer.userId) is None
    assert controller.viewDesignerProfile(suspended.userId) is None
    assert controller.viewDesignerProfile(9999) is None

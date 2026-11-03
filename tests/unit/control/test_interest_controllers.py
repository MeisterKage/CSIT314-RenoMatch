"""US-43 (diagrammed), US-44 and US-46 controllers."""

from app.control.view_idp_shortlist_count_controller import ViewIDPShortlistCountController
from app.control.view_idp_view_count_controller import ViewIDPViewCountController
from app.control.view_interest_dashboard_controller import ViewInterestDashboardController
from app.entity import IDPEntity


def test_view_count_controller_holds_the_entity_class():
    assert ViewIDPViewCountController().entity is IDPEntity


def test_getViewCount_returns_what_the_entity_returns(make_idp):
    idp = make_idp(viewCount=12)
    assert ViewIDPViewCountController().getViewCount(idp.idpId) == 12


def test_getViewCount_calls_the_entity_with_idpId():
    calls = []

    class FakeEntity:
        @classmethod
        def getViewCount(cls, idpId):
            calls.append(idpId)
            return 3

    controller = ViewIDPViewCountController()
    controller.entity = FakeEntity
    assert controller.getViewCount(41) == 3
    assert calls == [41]


def test_getShortlistCount(make_idp):
    idp = make_idp(shortlistCount=5)
    controller = ViewIDPShortlistCountController()
    assert controller.entity is IDPEntity
    assert controller.getShortlistCount(idp.idpId) == 5


def test_getInterestDashboard(make_account, make_idp):
    designer = make_account(role="designer")
    make_idp(designer, title="Only", viewCount=2, shortlistCount=1)
    controller = ViewInterestDashboardController()
    dashboard = controller.getInterestDashboard(designer.userId)
    assert dashboard["byStyle"] == [("Modern", 2, 1)]

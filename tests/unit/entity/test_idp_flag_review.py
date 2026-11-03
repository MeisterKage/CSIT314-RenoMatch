"""US-58 entity methods: getOpenReports and resolveReport."""

from app.entity import IDPEntity, IDPFlagEntity, db


def make_flag(reporter, idp, status="Open", reason="Not a real project"):
    flag = IDPFlagEntity(idpId=idp.idpId, reporterId=reporter.userId, reason=reason, status=status)
    db.session.add(flag)
    db.session.commit()
    return flag


def test_get_open_reports_lists_only_open_flags(make_account, make_idp):
    customer = make_account()
    open_flag = make_flag(customer, make_idp())
    make_flag(customer, make_idp(), status="Upheld")
    make_flag(customer, make_idp(), status="Dismissed")
    assert [flag.flagId for flag in IDPFlagEntity.getOpenReports()] == [open_flag.flagId]


def test_uphold_removes_the_idp_and_clears_featured(make_account, make_idp):
    customer, manager = make_account(), make_account(role="platform")
    idp = make_idp(isFeatured=True)
    flag = make_flag(customer, idp)
    assert IDPFlagEntity.resolveReport(flag.flagId, manager.userId, "uphold") is True
    db.session.refresh(flag)
    db.session.refresh(idp)
    assert (flag.status, flag.reviewedBy) == ("Upheld", manager.userId)
    assert flag.reviewedAt is not None
    assert idp.status == "Removed" and idp.isFeatured is False
    assert IDPEntity.getFeaturedIDPs() == []


def test_dismiss_leaves_the_idp_untouched(make_account, make_idp):
    customer, manager = make_account(), make_account(role="platform")
    idp = make_idp(isFeatured=True)
    flag = make_flag(customer, idp)
    assert IDPFlagEntity.resolveReport(flag.flagId, manager.userId, "dismiss") is True
    db.session.refresh(flag)
    db.session.refresh(idp)
    assert (flag.status, flag.reviewedBy) == ("Dismissed", manager.userId)
    assert flag.reviewedAt is not None
    assert idp.status == "Active" and idp.isFeatured is True


def test_resolve_refuses_missing_closed_or_unknown_decision(make_account, make_idp):
    customer, manager = make_account(), make_account(role="platform")
    closed = make_flag(customer, make_idp(), status="Dismissed")
    open_flag = make_flag(customer, make_idp())
    assert IDPFlagEntity.resolveReport(9999, manager.userId, "uphold") is False
    assert IDPFlagEntity.resolveReport(closed.flagId, manager.userId, "uphold") is False
    assert IDPFlagEntity.resolveReport(open_flag.flagId, manager.userId, "ban") is False
    db.session.refresh(open_flag)
    assert open_flag.status == "Open"

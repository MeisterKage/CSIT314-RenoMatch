import pytest
from sqlalchemy.exc import IntegrityError

from app.entity import CompanyInfoEntity, db


def test_designer_can_have_only_one_company(make_account):
    designer = make_account(role="designer")
    db.session.add(CompanyInfoEntity(designer=designer, name="Studio One"))
    db.session.commit()
    db.session.add(CompanyInfoEntity(designer=designer, name="Studio Two"))
    with pytest.raises(IntegrityError):
        db.session.commit()


def test_category_names_are_unique(make_category):
    make_category(name="Kitchen Remodel")
    with pytest.raises(IntegrityError):
        make_category(name="Kitchen Remodel")


def test_idp_links_designer_and_category(make_account, make_category, make_idp):
    designer = make_account(role="designer")
    category = make_category(name="Kitchen Carpentry")
    idp = make_idp(designer=designer, category=category)
    assert idp.designerId == designer.userId
    assert idp.categoryId == category.categoryId
    assert idp.category.name == "Kitchen Carpentry"
    assert idp.createdAt is not None

import pytest
from sqlalchemy.exc import IntegrityError

from app.entity import IDP, CompanyInfo, IDPPhoto, db


def test_designer_can_have_only_one_company(make_account):
    designer = make_account(role="designer")
    db.session.add(CompanyInfo(designer=designer, name="Studio One"))
    db.session.commit()
    db.session.add(CompanyInfo(designer=designer, name="Studio Two"))
    with pytest.raises(IntegrityError):
        db.session.commit()


def test_category_names_are_unique(make_category):
    make_category(name="Kitchen Remodel")
    with pytest.raises(IntegrityError):
        make_category(name="Kitchen Remodel")


def test_new_idp_defaults_to_current_and_visible(make_idp):
    idp = make_idp()
    assert idp.status == "current"
    assert (idp.is_archived, idp.is_featured, idp.is_removed) == (False, False, False)
    assert idp.created_at is not None


def test_idp_links_designer_and_category(make_account, make_category, make_idp):
    designer = make_account(role="designer")
    category = make_category(name="Kitchen Carpentry")
    idp = make_idp(designer=designer, category=category)
    assert idp.designer.id == designer.id
    assert idp.category.name == "Kitchen Carpentry"


def test_idp_photos_come_back_in_position_order(make_idp):
    idp = make_idp()
    idp.photos.append(IDPPhoto(content_type="image/png", data=b"second", position=2))
    idp.photos.append(IDPPhoto(content_type="image/png", data=b"first", position=1))
    db.session.commit()
    db.session.expire_all()
    assert [p.data for p in db.session.get(IDP, idp.id).photos] == [b"first", b"second"]

"""US-35, US-36, US-37: company info controllers."""

import pytest

from app.control.create_company_info_controller import CreateCompanyInfoController
from app.control.errors import ValidationError
from app.control.update_company_info_controller import UpdateCompanyInfoController
from app.control.view_company_info_controller import ViewCompanyInfoController
from app.entity import CompanyInfoEntity

VALID = {
    "name": "Studio Oak",
    "description": "Calm homes.",
    "address": "1 Orchard Road",
    "phone": "+65 6123 4567",
    "email": "hello@oak.sg",
    "website": "https://oak.sg",
}


def test_controllers_hold_the_entity_class():
    for controller in (
        CreateCompanyInfoController,
        ViewCompanyInfoController,
        UpdateCompanyInfoController,
    ):
        assert controller().entity is CompanyInfoEntity


def test_create_then_get(make_account):
    designer = make_account(role="designer")
    assert ViewCompanyInfoController().getCompanyInfo(designer.userId) is None
    created = CreateCompanyInfoController().createCompanyInfo(designer.userId, **VALID)
    assert created.name == "Studio Oak"
    assert ViewCompanyInfoController().getCompanyInfo(designer.userId).companyId == created.companyId


def test_only_one_record_per_designer(make_account):
    designer = make_account(role="designer")
    CreateCompanyInfoController().createCompanyInfo(designer.userId, **VALID)
    with pytest.raises(ValidationError):
        CreateCompanyInfoController().createCompanyInfo(designer.userId, **VALID)
    assert CompanyInfoEntity.query.count() == 1


def test_update_changes_fields(make_account):
    designer = make_account(role="designer")
    CreateCompanyInfoController().createCompanyInfo(designer.userId, **VALID)
    changed = {**VALID, "name": "Oak and Pine", "website": ""}
    updated = UpdateCompanyInfoController().updateCompanyInfo(designer.userId, **changed)
    assert updated.name == "Oak and Pine"
    assert updated.website == ""
    assert CompanyInfoEntity.query.count() == 1


def test_update_without_record_returns_none(make_account):
    designer = make_account(role="designer")
    assert UpdateCompanyInfoController().updateCompanyInfo(designer.userId, **VALID) is None


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("name", "  "),
        ("email", "nope"),
        ("phone", "12ab"),
        ("website", "oak.sg"),
        ("website", "ftp://oak.sg"),
    ],
)
def test_validation_errors(make_account, field, value):
    designer = make_account(role="designer")
    with pytest.raises(ValidationError) as caught:
        CreateCompanyInfoController().createCompanyInfo(designer.userId, **{**VALID, field: value})
    assert field in caught.value.errors
    assert CompanyInfoEntity.query.count() == 0


def test_optional_fields_may_be_blank(make_account):
    designer = make_account(role="designer")
    blank = {"name": "Studio Oak", "description": "", "address": "", "phone": "", "email": "",
             "website": ""}
    assert CreateCompanyInfoController().createCompanyInfo(designer.userId, **blank)

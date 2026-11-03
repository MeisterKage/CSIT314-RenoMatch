from app.control.errors import ValidationError
from app.control.validation import email_problem, phone_problem, website_problem


def cleanCompanyInfo(name, description, address, phone, email, website) -> dict:
    """Trim the company fields and raise ValidationError for a missing name or a bad
    email, phone or website. Email, phone and website may be blank."""
    values = {
        "name": name.strip(),
        "description": description.strip(),
        "address": address.strip(),
        "phone": phone.strip(),
        "email": email.strip().lower(),
        "website": website.strip(),
    }
    errors = {}
    if not values["name"]:
        errors["name"] = "Enter your company name."
    elif len(values["name"]) > 120:
        errors["name"] = "Company name must be 120 characters or fewer."
    if values["email"] and (problem := email_problem(values["email"])):
        errors["email"] = problem
    if problem := phone_problem(values["phone"]):
        errors["phone"] = problem
    if problem := website_problem(values["website"]):
        errors["website"] = problem
    elif len(values["website"]) > 200:
        errors["website"] = "Website must be 200 characters or fewer."
    if len(values["address"]) > 255:
        errors["address"] = "Address must be 255 characters or fewer."
    if errors:
        raise ValidationError(errors)
    return values

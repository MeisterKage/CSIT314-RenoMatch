def register_blueprints(app):
    from app.boundary import (
        account,
        admin,
        audit_log,
        auth,
        browse,
        company_info,
        compare,
        customer,
        designer,
        enquiries,
        favourites,
        interest,
        platform,
        portfolio,
        public,
        reset_password,
        uploads,
    )

    for module in (
        public, auth, reset_password, account, browse, compare, company_info, admin, audit_log,
        designer, customer, enquiries, favourites, interest, platform, portfolio, uploads
    ):
        app.register_blueprint(module.bp)

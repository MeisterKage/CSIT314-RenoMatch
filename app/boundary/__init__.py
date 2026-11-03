def register_blueprints(app):
    from app.boundary import (
        account,
        admin,
        audit_log,
        auth,
        browse,
        categories,
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
        reports,
        reset_password,
        uploads,
        weekly_summary_scheduler,
    )

    for module in (
        public, auth, reset_password, account, browse, compare, company_info, admin, audit_log,
        designer, customer, enquiries, favourites, interest, platform, categories, reports,
        portfolio, uploads,
        weekly_summary_scheduler
    ):
        app.register_blueprint(module.bp)

def register_blueprints(app):
    from app.boundary import (
        account,
        admin,
        auth,
        browse,
        compare,
        customer,
        designer,
        enquiries,
        favourites,
        platform,
        public,
        reset_password,
    )

    for module in (
        public, auth, reset_password, account, browse, compare, admin, designer, customer,
        enquiries, favourites, platform
    ):
        app.register_blueprint(module.bp)

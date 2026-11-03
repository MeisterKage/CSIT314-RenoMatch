def register_blueprints(app):
    from app.boundary import (
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
    )

    for module in (
        public, auth, browse, compare, admin, designer, customer, enquiries, favourites, platform
    ):
        app.register_blueprint(module.bp)

def register_blueprints(app):
    from app.boundary import admin, auth, browse, customer, designer, favourites, platform, public

    for module in (public, auth, browse, admin, designer, customer, favourites, platform):
        app.register_blueprint(module.bp)

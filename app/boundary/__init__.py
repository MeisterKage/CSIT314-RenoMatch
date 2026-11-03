def register_blueprints(app):
    from app.boundary import admin, auth, browse, customer, designer, platform, public

    for module in (public, auth, browse, admin, designer, customer, platform):
        app.register_blueprint(module.bp)

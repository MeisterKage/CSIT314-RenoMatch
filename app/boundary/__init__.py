def register_blueprints(app):
    from app.boundary import admin, auth, customer, designer, platform, public

    for module in (public, auth, admin, designer, customer, platform):
        app.register_blueprint(module.bp)

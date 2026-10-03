def register_blueprints(app):
    from app.boundary import public

    app.register_blueprint(public.bp)

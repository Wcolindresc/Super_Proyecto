# app/__init__.py
from flask import Flask, jsonify
from .config import Settings
from .supabase_client import init_supabase
from .blueprints.public import bp as public_bp
from .blueprints.admin import bp as admin_bp
from .blueprints.cart import bp as cart_bp
from .blueprints.orders import bp as orders_bp
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    CORS(app) 
    app.config.from_object(Settings())

    @app.get("/health")
    def health():
        return jsonify(ok=True)

    init_supabase(app)

    app.register_blueprint(public_bp, url_prefix="/api")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(cart_bp, url_prefix="/api")
    app.register_blueprint(orders_bp, url_prefix="/api")

    @app.errorhandler(Exception)
    def handle_unexpected_error(e):
        app.logger.exception("Unhandled error")
        return jsonify(error="internal_error", detail=str(e)), 500

    @app.errorhandler(404)
    def handle_404(e):
        return jsonify(error="not_found"), 404

    return app

app = create_app()

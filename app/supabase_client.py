from supabase import create_client, Client
from flask import current_app

def init_supabase(app):
    app.extensions["supabase_anon"] = create_client(
        app.config["SUPABASE_URL"],
        app.config["SUPABASE_ANON_KEY"]
    )
    app.extensions["supabase_service"] = create_client(
        app.config["SUPABASE_URL"],
        app.config["SUPABASE_SERVICE_ROLE_KEY"]
    )

def supa_public() -> Client:
    return current_app.extensions["supabase_anon"]

def supa_service() -> Client:
    return current_app.extensions["supabase_service"]

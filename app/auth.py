from functools import wraps
from flask import request, abort
from .supabase_client import supa_service

def get_user_from_jwt():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    jwt = auth.split(" ", 1)[1]
    user = supa_service().auth.get_user(jwt)
    return user.user if user and user.user else None

def require_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        user = get_user_from_jwt()
        if not user:
            abort(401)
        request.user = user
        return f(*args, **kwargs)
    return wrapper

def require_role(role_name: str):
    def deco(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user = get_user_from_jwt()
            if not user:
                abort(401)
            data = supa_service().rpc("is_user_in_role", {"p_auth_user_id": user.id, "p_role": role_name}).execute()
            ok = bool(data.data and data.data[0].get("ok"))
            if not ok:
                abort(403)
            request.user = user
            return f(*args, **kwargs)
        return wrapper
    return deco

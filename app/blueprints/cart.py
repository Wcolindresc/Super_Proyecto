from flask import Blueprint, request, jsonify
from ..auth import require_auth
from ..supabase_client import supa_service

bp = Blueprint("cart", __name__)

@bp.post("/cart")
@require_auth
def upsert_cart():
    user = getattr(request, "user")
    body = request.get_json(force=True)
    supa_service().postgres.execute("select ensure_cart(%s);", (user.id,))
    for it in body.get("items", []):
        supa_service().postgres.execute(
            "select upsert_cart_item(%s, %s, %s);", (user.id, it["product_id"], it["qty"])
        )
    rows = supa_service().postgres.execute("select get_cart(%s);", (user.id,)).data
    return jsonify(rows[0]["get_cart"])

from flask import Blueprint, request, jsonify
from ..auth import require_auth
from ..supabase_client import supa_service

bp = Blueprint("orders", __name__)

@bp.post("/orders/checkout")
@require_auth
def checkout():
    user = getattr(request, "user")
    body = request.get_json(force=True)
    coupon = body.get("coupon_code")
    client = supa_service()
    res = client.rpc("checkout_order", {
        "p_auth_user_id": user.id,
        "p_coupon": coupon
    }).execute()
    # rpc retorna el UUID; normalizamos
    order_id = res.data if isinstance(res.data, str) else (res.data[0] if res.data else None)
    return jsonify({"order_id": order_id}), 201

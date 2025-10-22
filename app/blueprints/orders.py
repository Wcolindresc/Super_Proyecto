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
    res = supa_service().postgres.execute("select checkout_order(%s, %s) as order_id;", (user.id, coupon))
    return jsonify({"order_id": res.data[0]["order_id"]}), 201

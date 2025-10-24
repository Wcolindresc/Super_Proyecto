from flask import Blueprint, request, jsonify
from ..auth import require_auth
from ..supabase_client import supa_service
from flask import request, jsonify
from ..auth import require_role
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


    from flask import request, jsonify
from ..auth import require_role
from ..supabase_client import supa_service

@bp.get("/admin/orders")
@require_role("Admin")
def admin_orders_list():
    client = supa_service()
    page = int(request.args.get("page", 1))
    size = min(int(request.args.get("size", 20)), 100)
    from_ = (page-1)*size
    to_ = from_ + size - 1

    cols = "id, user_id, status, total_amount, created_at"
    res = (client.table("orders")
           .select(cols, count="exact")
           .order("created_at", desc=True)
           .range(from_, to_)
           .execute())
    return jsonify({
        "items": res.data or [],
        "count": res.count or 0,
        "page": page, "size": size
    })

@bp.get("/admin/orders/<uuid:oid>")
@require_role("Admin")
def admin_orders_get(oid):
    client = supa_service()
    ord_res = (client.table("orders")
               .select("*")
               .eq("id", str(oid)).limit(1).execute())
    orders = ord_res.data or []
    if not orders:
        return jsonify({"error":"not_found"}), 404
    order = orders[0]
    items = (client.table("order_items")
             .select("*")
             .eq("order_id", str(oid))
             .order("id", desc=False).execute().data or []
    order["items"] = items
    return jsonify(order)

@bp.put("/admin/orders/<uuid:oid>")
@require_role("Admin")
def admin_orders_update(oid):
    client = supa_service()
    payload = request.get_json(silent=True) or {}
    allowed = {"status", "shipment_tracking"}
    update = {k:v for k,v in payload.items() if k in allowed}
    if not update:
        return jsonify({"error":"no_fields"}), 400
    res = (client.table("orders")
           .update(update)
           .eq("id", str(oid))
           .execute())
    return jsonify(res.data[0] if res.data else {"ok": True})

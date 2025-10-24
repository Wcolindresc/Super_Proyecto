# app/blueprints/orders.py
from __future__ import annotations

from flask import Blueprint, jsonify, request

from ..auth import require_role  # valida JWT de Supabase + rol Admin
from ..supabase_client import supa_service  # client con SERVICE_ROLE

bp = Blueprint("orders", __name__)

# -------------------------------------------------------
# Endpoints de ADMIN para gestionar pedidos
#   GET   /api/admin/orders          (lista paginada)
#   GET   /api/admin/orders/<uuid>   (detalle + items)
#   PUT   /api/admin/orders/<uuid>   (actualizar estado/guía)
# -------------------------------------------------------

@bp.get("/admin/orders")
@require_role("Admin")
def admin_orders_list():
    """
    Lista pedidos con paginación.
    Query params: ?page=1&size=20
    """
    client = supa_service()
    page = int(request.args.get("page", 1))
    size = min(int(request.args.get("size", 20)), 100)
    start = (page - 1) * size
    end = start + size - 1

    cols = "id, user_id, status, total_amount, created_at"
    res = (
        client.table("orders")
        .select(cols, count="exact")
        .order("created_at", desc=True)
        .range(start, end)
        .execute()
    )

    return jsonify({
        "items": res.data or [],
        "count": res.count or 0,
        "page": page,
        "size": size
    })


@bp.get("/admin/orders/<uuid:oid>")
@require_role("Admin")
def admin_orders_get(oid):
    """
    Devuelve el detalle de un pedido + sus items.
    """
    client = supa_service()

    o_res = (
        client.table("orders")
        .select("*")
        .eq("id", str(oid))
        .limit(1)
        .execute()
    )
    orders = o_res.data or []
    if not orders:
        return jsonify({"error": "not_found"}), 404

    order = orders[0]

    items = (
        client.table("order_items")
        .select("*")
        .eq("order_id", str(oid))
        .order("id", desc=False)
        .execute()
        .data
        or []
    )

    order["items"] = items
    return jsonify(order)


@bp.put("/admin/orders/<uuid:oid>")
@require_role("Admin")
def admin_orders_update(oid):
    """
    Actualiza campos permitidos del pedido (por ejemplo: status, shipment_tracking).
    Body JSON: { "status": "...", "shipment_tracking": "..." }
    """
    client = supa_service()
    payload = request.get_json(silent=True) or {}

    allowed = {"status", "shipment_tracking"}
    update = {k: v for k, v in payload.items() if k in allowed}
    if not update:
        return jsonify({"error": "no_fields"}), 400

    res = (
        client.table("orders")
        .update(update)
        .eq("id", str(oid))
        .select("*")
        .execute()
    )

    if not res.data:
        return jsonify({"error": "not_found"}), 404

    return jsonify(res.data[0])

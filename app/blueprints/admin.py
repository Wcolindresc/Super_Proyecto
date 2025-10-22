from flask import Blueprint, request, jsonify
from ..auth import require_role
from ..supabase_client import supa_service
from datetime import datetime, timezone

bp = Blueprint("admin", __name__)

@bp.post("/products")
@require_role("Admin")
def create_product():
    body = request.get_json(force=True)
    client = supa_service()
    data = {
        "name": body.get("name"),
        "sku": body.get("sku"),
        "price": body.get("price"),
        "old_price": body.get("old_price"),
        "short_description": body.get("short_description"),
        "description": body.get("description"),
        "category_id": body.get("category_id"),
        "brand_id": body.get("brand_id"),
        "status": body.get("status", "draft"),
        "free_shipping": body.get("free_shipping", False),
    }
    res = client.table("products").insert(data).select("id").execute()
    return jsonify(res.data[0]), 201

@bp.put("/products/<uuid:pid>")
@require_role("Admin")
def update_product(pid):
    body = request.get_json(force=True)
    client = supa_service()
    patch = {k: v for k, v in {
        "name": body.get("name"),
        "sku": body.get("sku"),
        "price": body.get("price"),
        "old_price": body.get("old_price"),
        "short_description": body.get("short_description"),
        "description": body.get("description"),
        "category_id": body.get("category_id"),
        "brand_id": body.get("brand_id"),
        "status": body.get("status"),
        "free_shipping": body.get("free_shipping"),
    }.items() if v is not None}

    # published_at simple client-side
    if patch.get("status") == "published":
        patch.setdefault("published_at", datetime.now(timezone.utc).isoformat())

    res = client.table("products").update(patch).eq("id", str(pid)).select("id").execute()
    return jsonify(res.data[0] if res.data else {}), 200

@bp.post("/products/<uuid:pid>/images")
@require_role("Admin")
def add_image(pid):
    body = request.get_json(force=True)
    client = supa_service()
    data = {
        "product_id": str(pid),
        "url": body.get("url"),
        "sort_order": body.get("sort_order", 0),
        "is_primary": bool(body.get("is_primary", False))
    }
    res = client.table("product_images").insert(data).select("id").execute()
    return jsonify(res.data[0]), 201

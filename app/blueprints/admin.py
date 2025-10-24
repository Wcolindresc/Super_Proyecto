# app/blueprints/admin.py
from __future__ import annotations

import os
import uuid
import time
from flask import Blueprint, jsonify, request

from ..auth import require_role  # Decorador que valida JWT de Supabase + rol
from ..supabase_client import supa_service  # Client con SERVICE_ROLE

bp = Blueprint("admin", __name__)


@bp.get("/me")
@require_role("Admin")
def whoami():
    """Usado por el front para verificar que el usuario es Admin."""
    return jsonify({"ok": True, "role": "Admin"})


# ----------------------------
# Productos
# ----------------------------
@bp.post("/products")
@require_role("Admin")
def create_product():
    """
    Crea un producto. Espera JSON con, al menos:
    name, sku, price, category_id, brand_id, status ('draft'|'published'|'hidden')
    """
    body = request.get_json(silent=True) or {}
    required = ["name", "sku", "price", "category_id", "brand_id", "status"]
    miss = [k for k in required if body.get(k) in (None, "")]
    if miss:
        return jsonify({"error": "missing_fields", "fields": miss}), 400

    # Normaliza tipos
    body["price"] = float(body.get("price", 0))
    if "old_price" in body and body["old_price"] not in (None, ""):
        body["old_price"] = float(body["old_price"])
    else:
        body["old_price"] = None

    # Si viene published, setea published_at
    if str(body.get("status")) == "published" and not body.get("published_at"):
        # Supabase convertirá a timestamptz
        body["published_at"] = "now()"

    client = supa_service()
    res = client.table("products").insert(body).select("*").execute()
    data = (res.data or [])
    if not data:
        return jsonify({"error": "insert_failed"}), 500
    return jsonify(data[0])


@bp.put("/products/<uuid:pid>")
@require_role("Admin")
def update_product(pid):
    """
    Actualiza campos permitidos del producto.
    Si status pasa a 'published', setea published_at = now().
    """
    body = request.get_json(silent=True) or {}
    allowed = {
        "name",
        "sku",
        "price",
        "old_price",
        "short_description",
        "description",
        "category_id",
        "brand_id",
        "status",
        "free_shipping",
    }
    update = {k: v for k, v in body.items() if k in allowed}

    if "price" in update and update["price"] not in (None, ""):
        update["price"] = float(update["price"])
    if "old_price" in update:
        if update["old_price"] in (None, ""):
            update["old_price"] = None
        else:
            update["old_price"] = float(update["old_price"])

    if update.get("status") == "published":
        update["published_at"] = "now()"

    client = supa_service()
    res = (
        client.table("products")
        .update(update)
        .eq("id", str(pid))
        .select("*")
        .execute()
    )
    if not res.data:
        return jsonify({"error": "not_found"}), 404
    return jsonify(res.data[0])


@bp.post("/products/<uuid:pid>/images")
@require_role("Admin")
def add_product_image(pid):
    """
    Inserta un registro en product_images.
    Espera JSON: {url, sort_order (int), is_primary (bool)}
    Si is_primary=True, desmarca las demás del producto.
    """
    payload = request.get_json(silent=True) or {}
    url = payload.get("url")
    if not url:
        return jsonify({"error": "missing_url"}), 400

    sort_order = int(payload.get("sort_order", 0))
    is_primary = bool(payload.get("is_primary", False))

    client = supa_service()

    if is_primary:
        # desmarca otras
        client.table("product_images").update({"is_primary": False}).eq(
            "product_id", str(pid)
        ).execute()

    ins = (
        client.table("product_images")
        .insert(
            {
                "product_id": str(pid),
                "url": url,
                "sort_order": sort_order,
                "is_primary": is_primary,
            }
        )
        .select("*")
        .execute()
    )
    return jsonify(ins.data[0] if ins.data else {"ok": True})


# ----------------------------
# Upload (Supabase Storage)
# ----------------------------
@bp.post("/upload")
@require_role("Admin")
def upload_file():
    """
    Subida de imagen a Supabase Storage usando SERVICE ROLE.
    Form-data:
      - file: archivo
      - prefix: carpeta opcional (ej. products/SKU-01)
    Devuelve: { public_url, path }
    """
    if "file" not in request.files:
        return jsonify({"error": "missing_file"}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "empty_filename"}), 400

    prefix = request.form.get("prefix", "products")
    # Nombre único: <prefix>/<ts>-<uuid>-<sanitized-name>
    base = file.filename.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    ts = int(time.time() * 1000)
    key = f"{prefix}/{ts}-{uuid.uuid4().hex}-{base}"

    client = supa_service()
    storage = client.storage.from_("products")

    # Carga binaria
    data = file.read()
    storage.upload(key, data, {"contentType": file.mimetype})

    # Public URL
    pub = storage.get_public_url(key)
    return jsonify({"public_url": pub, "path": key})


# ----------------------------
# Usuarios (Clientes)
# ----------------------------
@bp.get("/users")
@require_role("Admin")
def list_users():
    """
    Lista clientes (tabla app_users).
    Query params: ?page=1&size=20
    """
    page = int(request.args.get("page", 1))
    size = min(int(request.args.get("size", 20)), 100)
    from_ = (page - 1) * size
    to_ = from_ + size - 1

    client = supa_service()
    cols = "id, email, full_name, created_at, auth_user_id"
    res = (
        client.table("app_users")
        .select(cols, count="exact")
        .order("created_at", desc=True)
        .range(from_, to_)
        .execute()
    )

    return jsonify(
        {
            "items": res.data or [],
            "count": res.count or 0,
            "page": page,
            "size": size,
        }
    )

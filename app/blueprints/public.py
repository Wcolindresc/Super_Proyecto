# app/blueprints/public.py
from flask import Blueprint, jsonify, request
from .utils import to_int
from ..supabase_client import supa_public  # cliente público (anon) para RLS

bp = Blueprint("public", __name__)

@bp.get("/products")
def list_products():
    try:
        q = request.args.get("q")
        brand = request.args.get("brand")
        category = request.args.get("category")
        minp = to_int(request.args.get("min"))
        maxp = to_int(request.args.get("max"))
        order = request.args.get("order", "name.asc")
        limit = to_int(request.args.get("limit")) or 60

        client = supa_public()
        query = client.table("products").select(
            "id,name,sku,price,old_price,status,brand_id,category_id"
        ).eq("status", "published")

        if q:
            query = query.ilike("name", f"%{q}%")

        if brand:
            b = client.table("brands").select("id").eq("slug", brand).limit(1).execute()
            if b.data: query = query.eq("brand_id", b.data[0]["id"])
            else: return jsonify([])

        if category:
            c = client.table("categories").select("id").eq("slug", category).limit(1).execute()
            if c.data: query = query.eq("category_id", c.data[0]["id"])
            else: return jsonify([])

        if minp is not None: query = query.gte("price", minp)
        if maxp is not None: query = query.lte("price", maxp)

        if order == "price.asc": query = query.order("price", desc=False)
        elif order == "price.desc": query = query.order("price", desc=True)
        else: query = query.order("name", desc=False)

        prods = query.limit(limit).execute().data or []

        ids = [p["id"] for p in prods]
        primary = {}
        if ids:
            imgs = (client.table("product_images")
                .select("product_id,url,is_primary,sort_order")
                .in_("product_id", ids)
                .eq("is_primary", True)
                .order("sort_order", desc=False)
                .execute().data or [])
            for im in imgs:
                pid = im["product_id"]
                if pid not in primary: primary[pid] = im["url"]

        for p in prods: p["primary_image"] = primary.get(p["id"])
        return jsonify(prods)
    except Exception as e:
        return jsonify({"error": "internal_error", "detail": str(e)}), 500

@bp.get("/products/<uuid:pid>")
def get_product(pid):
    try:
        client = supa_public()
        r = (client.table("products").select("*")
            .eq("id", str(pid)).eq("status", "published").limit(1).execute())
        rows = r.data or []
        if not rows: return jsonify({"error": "not_found"}), 404
        prod = rows[0]
        imgs = (client.table("product_images")
            .select("id,url,sort_order,is_primary")
            .eq("product_id", str(pid)).order("sort_order", desc=False).execute().data or [])
        prod["images"] = imgs
        return jsonify(prod)
    except Exception as e:
        return jsonify({"error": "internal_error", "detail": str(e)}), 500

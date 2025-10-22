from flask import Blueprint, request, jsonify
from ..auth import require_role
from ..supabase_client import supa_service

bp = Blueprint("admin", __name__)

@bp.post("/products")
@require_role("Admin")
def create_product():
    body = request.get_json(force=True)
    sql = '''
    insert into products(name, sku, price, old_price, short_description, description, category_id, brand_id, status)
    values (%(name)s, %(sku)s, %(price)s, %(old_price)s, %(short)s, %(desc)s, %(category_id)s, %(brand_id)s, coalesce(%(status)s,'draft'))
    returning id;
    '''
    res = supa_service().postgres.execute(sql, {
        "name": body.get("name"),
        "sku": body.get("sku"),
        "price": body.get("price"),
        "old_price": body.get("old_price"),
        "short": body.get("short_description"),
        "desc": body.get("description"),
        "category_id": body.get("category_id"),
        "brand_id": body.get("brand_id"),
        "status": body.get("status", "draft"),
    })
    return jsonify(res.data[0]), 201

@bp.put("/products/<uuid:pid>")
@require_role("Admin")
def update_product(pid):
    body = request.get_json(force=True)
    sql = '''
    update products set
      name=coalesce(%(name)s, name),
      sku=coalesce(%(sku)s, sku),
      price=coalesce(%(price)s, price),
      old_price=%(old_price)s,
      short_description=coalesce(%(short)s, short_description),
      description=coalesce(%(desc)s, description),
      category_id=coalesce(%(category_id)s, category_id),
      brand_id=coalesce(%(brand_id)s, brand_id),
      status=coalesce(%(status)s, status),
      published_at = case when %(status)s='published' and published_at is null then now() else published_at end
    where id=%(pid)s
    returning id;
    '''
    res = supa_service().postgres.execute(sql, {**body, "pid": str(pid)})
    return jsonify(res.data[0] if res.data else {}), 200

@bp.post("/products/<uuid:pid>/images")
@require_role("Admin")
def add_image(pid):
    body = request.get_json(force=True)
    sql = '''
    insert into product_images(product_id, url, sort_order, is_primary)
    values (%(pid)s, %(url)s, coalesce(%(sort_order)s, 0), coalesce(%(is_primary)s,false))
    returning id;
    '''
    res = supa_service().postgres.execute(sql, {"pid": str(pid), **body})
    return jsonify(res.data[0]), 201

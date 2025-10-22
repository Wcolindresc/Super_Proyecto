from flask import Blueprint, jsonify, request
from .utils import to_int
from ..supabase_client import supa_service

bp = Blueprint("public", __name__)

@bp.get("/products")
def list_products():
    q = request.args.get("q")
    brand = request.args.get("brand")
    category = request.args.get("category")
    minp = to_int(request.args.get("min"))
    maxp = to_int(request.args.get("max"))
    order = request.args.get("order", "name.asc")

    sql = '''
    select p.id, p.name, p.sku, p.price, p.old_price, p.status,
           (select url from product_images pi where pi.product_id=p.id and pi.is_primary = true
            order by sort_order asc limit 1) as primary_image
    from products p
    where p.status='published'
      and (%(q)s is null or p.name ilike '%%' || %(q)s || '%%')
      and (%(brand)s is null or p.brand_id in (select id from brands where slug=%(brand)s))
      and (%(category)s is null or p.category_id in (select id from categories where slug=%(category)s))
      and (%(min)s is null or p.price >= %(min)s)
      and (%(max)s is null or p.price <= %(max)s)
    order by case when %(order)s='price.asc' then p.price end asc,
             case when %(order)s='price.desc' then p.price end desc,
             case when %(order)s='name.asc' then p.name end asc nulls last;
    '''
    data = supa_service().postgres.execute(sql, {
        "q": q, "brand": brand, "category": category, "min": minp, "max": maxp, "order": order
    })
    return jsonify(data.data or [])

@bp.get("/products/<uuid:pid>")
def get_product(pid):
    sql = '''
    select p.*, coalesce(json_agg(pi order by pi.sort_order) filter (where pi.id is not null), '[]') as images
    from products p
    left join product_images pi on pi.product_id=p.id
    where p.id=%(pid)s and p.status='published'
    group by p.id;
    '''
    data = supa_service().postgres.execute(sql, {"pid": str(pid)})
    rows = data.data or []
    return (jsonify(rows[0]), 200) if rows else (jsonify({"error":"not_found"}), 404)

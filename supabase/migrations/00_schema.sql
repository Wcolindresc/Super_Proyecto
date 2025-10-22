create extension if not exists "uuid-ossp";

do $$ begin
  if not exists (select 1 from pg_type where typname = 'product_status') then
    create type product_status as enum ('draft','pending','published','hidden');
  end if;
end $$;

create table if not exists app_users(
  id uuid primary key default uuid_generate_v4(),
  auth_user_id uuid unique,
  email text unique not null,
  full_name text,
  created_at timestamptz default now()
);

create table if not exists app_roles(
  id bigserial primary key,
  role_name text unique not null check (role_name in ('Admin','Gestor','Cliente'))
);

insert into app_roles(role_name) values ('Admin'),('Gestor'),('Cliente')
on conflict (role_name) do nothing;

create table if not exists user_roles(
  user_id uuid references app_users(id) on delete cascade,
  role_id bigint references app_roles(id) on delete cascade,
  primary key (user_id, role_id)
);

create table if not exists brands(
  id bigserial primary key,
  name text not null unique,
  slug text not null unique
);

create table if not exists categories(
  id bigserial primary key,
  name text not null,
  slug text not null unique,
  parent_id bigint references categories(id)
);

create table if not exists products(
  id uuid primary key default uuid_generate_v4(),
  sku text not null unique,
  name text not null,
  short_description text,
  description text,
  brand_id bigint references brands(id),
  category_id bigint references categories(id),
  price numeric(12,2) not null,
  old_price numeric(12,2),
  status product_status not null default 'draft',
  published_at timestamptz,
  free_shipping boolean default false,
  created_at timestamptz default now()
);

create index if not exists idx_products_status on products(status);
create index if not exists idx_products_sku on products(sku);
create index if not exists idx_products_name on products using gin (to_tsvector('spanish', coalesce(name,'')));

create table if not exists product_images(
  id bigserial primary key,
  product_id uuid references products(id) on delete cascade,
  url text not null,
  sort_order int default 0,
  is_primary boolean default false
);

create table if not exists product_variants(
  id bigserial primary key,
  product_id uuid references products(id) on delete cascade,
  name text not null,
  sku text unique,
  price numeric(12,2),
  stock int not null default 0
);

create table if not exists inventory_movements(
  id bigserial primary key,
  product_id uuid references products(id) on delete set null,
  variant_id bigint references product_variants(id) on delete set null,
  qty int not null,
  reason text,
  created_at timestamptz default now()
);

create table if not exists carts(
  id uuid primary key default uuid_generate_v4(),
  owner_auth_user_id uuid not null,
  created_at timestamptz default now()
);

create table if not exists cart_items(
  id bigserial primary key,
  cart_id uuid references carts(id) on delete cascade,
  product_id uuid references products(id),
  variant_id bigint references product_variants(id),
  qty int not null check (qty > 0)
);

create table if not exists orders(
  id uuid primary key default uuid_generate_v4(),
  owner_auth_user_id uuid not null,
  status text not null check (status in ('nuevo','pagado','enviado','entregado','cancelado')) default 'nuevo',
  total numeric(12,2) not null default 0,
  created_at timestamptz default now()
);

create table if not exists order_items(
  id bigserial primary key,
  order_id uuid references orders(id) on delete cascade,
  product_id uuid references products(id),
  variant_id bigint references product_variants(id),
  name text,
  sku text,
  price numeric(12,2),
  qty int not null
);

create table if not exists payments(
  id bigserial primary key,
  order_id uuid references orders(id) on delete cascade,
  method text,
  amount numeric(12,2),
  status text,
  created_at timestamptz default now()
);

create table if not exists shipments(
  id bigserial primary key,
  order_id uuid references orders(id) on delete cascade,
  address text,
  city text,
  status text,
  tracking_code text,
  created_at timestamptz default now()
);

create table if not exists coupons(
  id bigserial primary key,
  code text unique not null,
  description text,
  discount_percent int check (discount_percent between 1 and 90),
  valid_from date,
  valid_to date,
  active boolean default true
);

create table if not exists banners(
  id bigserial primary key,
  title text,
  image_url text,
  link_url text,
  sort_order int default 0,
  active boolean default true
);

create table if not exists audit_logs(
  id bigserial primary key,
  actor_auth_user_id uuid,
  action text,
  entity text,
  entity_id text,
  payload jsonb,
  created_at timestamptz default now()
);

create or replace function ensure_cart(p_auth_user_id uuid) returns uuid language plpgsql as $$
declare c_id uuid;
begin
  select id into c_id from carts where owner_auth_user_id = p_auth_user_id limit 1;
  if c_id is null then
    insert into carts(owner_auth_user_id) values (p_auth_user_id) returning id into c_id;
  end if;
  return c_id;
end $$;

create or replace function upsert_cart_item(p_auth_user_id uuid, p_product uuid, p_qty int)
returns void language plpgsql as $$
declare c_id uuid;
begin
  c_id := ensure_cart(p_auth_user_id);
  if exists(select 1 from cart_items where cart_id=c_id and product_id=p_product) then
    update cart_items set qty = p_qty where cart_id=c_id and product_id=p_product;
  else
    insert into cart_items(cart_id, product_id, qty) values (c_id, p_product, p_qty);
  end if;
end $$;

create or replace function get_cart(p_auth_user_id uuid) returns json language sql as $$
  with c as (select id from carts where owner_auth_user_id = p_auth_user_id limit 1)
  select json_build_object(
    'id', c.id,
    'items', coalesce((
      select json_agg(json_build_object(
        'product_id', ci.product_id,
        'qty', ci.qty,
        'name', p.name,
        'sku', p.sku,
        'price', p.price
      ))
      from cart_items ci
      join products p on p.id=ci.product_id
      where ci.cart_id=c.id
    ), '[]'::json),
    'total', coalesce((
      select sum(ci.qty * p.price) from cart_items ci join products p on p.id=ci.product_id where ci.cart_id=c.id
    ),0)
  )
  from c;
$$;

create or replace function checkout_order(p_auth_user_id uuid, p_coupon text)
returns uuid language plpgsql as $$
declare v_order uuid; v_total numeric(12,2); v_discount int := 0;
begin
  perform ensure_cart(p_auth_user_id);
  select (get_cart(p_auth_user_id)->>'total')::numeric into v_total;

  if p_coupon is not null then
    select discount_percent into v_discount
    from coupons c where c.code=p_coupon and c.active and current_date between c.valid_from and c.valid_to
    limit 1;
    if v_discount is null then v_discount := 0; end if;
  end if;

  v_total := v_total * (100 - v_discount) / 100.0;

  insert into orders(owner_auth_user_id, total) values (p_auth_user_id, coalesce(v_total,0)) returning id into v_order;

  insert into order_items(order_id, product_id, name, sku, price, qty)
  select v_order, ci.product_id, p.name, p.sku, p.price, ci.qty
  from carts c
  join cart_items ci on ci.cart_id=c.id
  join products p on p.id=ci.product_id
  where c.owner_auth_user_id=p_auth_user_id;

  insert into inventory_movements(product_id, qty, reason)
  select ci.product_id, -ci.qty, 'checkout'
  from carts c join cart_items ci on ci.cart_id=c.id
  where c.owner_auth_user_id=p_auth_user_id;

  delete from cart_items where cart_id in (select id from carts where owner_auth_user_id=p_auth_user_id);

  return v_order;
end $$;

create or replace function is_user_in_role(p_auth_user_id uuid, p_role text)
returns table(ok boolean) language sql as $$
  select exists(
    select 1
    from app_users u
    join user_roles ur on ur.user_id=u.id
    join app_roles r on r.id=ur.role_id
    where u.auth_user_id=p_auth_user_id and r.role_name=p_role
  ) as ok;
$$;

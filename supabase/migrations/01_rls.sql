-- 01_rls.sql — idempotente

-- Activar RLS (es idempotente)
alter table products enable row level security;
alter table carts enable row level security;
alter table cart_items enable row level security;
alter table orders enable row level security;
alter table order_items enable row level security;
alter table product_images enable row level security;

-- Products: lectura pública solo publicados
drop policy if exists "public_read_published" on products;
create policy "public_read_published" on products
  for select
  using (status = 'published');

-- Products: escritura solo Admin
drop policy if exists "admin_write_products" on products;
create policy "admin_write_products" on products
  for all
  using (exists (
    select 1 from app_users u
    join user_roles ur on ur.user_id=u.id
    join app_roles r on r.id=ur.role_id
    where u.auth_user_id = auth.uid() and r.role_name='Admin'
  ))
  with check (exists (
    select 1 from app_users u
    join user_roles ur on ur.user_id=u.id
    join app_roles r on r.id=ur.role_id
    where u.auth_user_id = auth.uid() and r.role_name='Admin'
  ));

-- Imágenes: visibles si el producto está publicado
drop policy if exists "read_images_published_product" on product_images;
create policy "read_images_published_product" on product_images
  for select
  using (exists (
    select 1 from products p
    where p.id=product_images.product_id and p.status='published'
  ));

-- CARRITOS: propietario
drop policy if exists "cart_owner" on carts;
create policy "cart_owner" on carts
  for all
  using (owner_auth_user_id = auth.uid())
  with check (owner_auth_user_id = auth.uid());

drop policy if exists "cart_items_owner" on cart_items;
create policy "cart_items_owner" on cart_items
  for all
  using (exists (
    select 1 from carts c
    where c.id=cart_items.cart_id and c.owner_auth_user_id=auth.uid()
  ))
  with check (exists (
    select 1 from carts c
    where c.id=cart_items.cart_id and c.owner_auth_user_id=auth.uid()
  ));

-- ÓRDENES: propietario
drop policy if exists "orders_owner" on orders;
create policy "orders_owner" on orders
  for all
  using (owner_auth_user_id = auth.uid())
  with check (owner_auth_user_id = auth.uid());

drop policy if exists "order_items_owner" on order_items;
create policy "order_items_owner" on order_items
  for select
  using (exists (
    select 1 from orders o
    where o.id=order_items.order_id and o.owner_auth_user_id=auth.uid()
  ));

-- Admin puede ver TODO en carts y orders
drop policy if exists "admin_all_carts" on carts;
create policy "admin_all_carts" on carts
  for select
  using (exists(
    select 1 from app_users u
    join user_roles ur on ur.user_id=u.id
    join app_roles r on r.id=ur.role_id
    where u.auth_user_id=auth.uid() and r.role_name='Admin'
  ));

drop policy if exists "admin_all_orders" on orders;
create policy "admin_all_orders" on orders
  for select
  using (exists(
    select 1 from app_users u
    join user_roles ur on ur.user_id=u.id
    join app_roles r on r.id=ur.role_id
    where u.auth_user_id=auth.uid() and r.role_name='Admin'
  ));

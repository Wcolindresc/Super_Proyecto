-- 02_seed.sql (FIX ENUM CAST)

insert into app_users(auth_user_id, email, full_name) values
  ('00000000-0000-0000-0000-000000000001','admin@labodegonea.gt','Admin Demo')
on conflict (auth_user_id) do nothing;

insert into app_users(auth_user_id, email, full_name) values
  ('00000000-0000-0000-0000-000000000002','cliente@labodegonea.gt','Cliente Demo')
on conflict (auth_user_id) do nothing;

insert into user_roles(user_id, role_id)
select u.id, r.id from app_users u, app_roles r
where u.auth_user_id='00000000-0000-0000-0000-000000000001' and r.role_name='Admin'
on conflict do nothing;

insert into user_roles(user_id, role_id)
select u.id, r.id from app_users u, app_roles r
where u.auth_user_id='00000000-0000-0000-0000-000000000002' and r.role_name='Cliente'
on conflict do nothing;

insert into brands(name, slug) values
('KetzalTech','ketzaltech'),('QuetzalGear','quetzalgear'),('Pacaya','pacaya'),
('Atitlán','atitlan'),('Ixchel','ixchel'),('Tecún','tecun')
on conflict do nothing;

insert into categories(name, slug) values
('Laptops','laptops'),('Smartphones','smartphones'),('Accesorios','accesorios'),
('Audio','audio'),('Hogar','hogar'),('Gaming','gaming')
on conflict do nothing;

do $$
declare i int := 1;
begin
  while i <= 32 loop
    insert into products(
      sku, name, price, old_price, short_description, description,
      category_id, brand_id, status, free_shipping
    )
    values (
      'SKU-'||to_char(i,'FM00'),
      'Producto Demo '||i,
      (3000 + i*10),
      (3000 + i*10 + 200),
      'Resumen breve del producto '||i,
      'Descripción larga del producto de demostración #'||i||'. Ideal para pruebas.',
      (select id from categories order by id limit 1),
      (select id from brands order by id limit 1),
      /* CAST CORRECTO AL ENUM product_status */
      case when i%3=0 then 'published'::product_status else 'draft'::product_status end,
      (i%2=0)
    );
    i := i + 1;
  end loop;
end $$;

insert into banners(title, image_url, link_url, sort_order, active) values
('Ofertas de la semana','/assets/img/banner1.jpg','/productos.html',1,true),
('Nuevas llegadas','/assets/img/banner2.jpg','/productos.html',2,true)
on conflict do nothing;

insert into coupons(code, description, discount_percent, valid_from, valid_to, active) values
('BIENVENIDA','Descuento de bienvenida',10,current_date - 1, current_date + 30, true),
('OCTUBRE','Mes de octubre',15,current_date - 1, current_date + 10, true),
('VIP','Clientes VIP',20,current_date - 1, current_date + 60, true)
on conflict do nothing;

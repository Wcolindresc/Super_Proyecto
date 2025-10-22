-- 03_storage.sql — sin storage.create_bucket, idempotente

-- Crear/actualizar bucket 'products' directamente
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
  'products',
  'products',
  true,
  5242880,                                  -- 5 MB
  array['image/jpeg','image/png','image/webp']
)
on conflict (id) do update
  set public = excluded.public,
      file_size_limit = excluded.file_size_limit,
      allowed_mime_types = excluded.allowed_mime_types;

-- Políticas: dropear si existen y recrear
drop policy if exists "Public read products bucket" on storage.objects;
create policy "Public read products bucket"
on storage.objects for select
using ( bucket_id = 'products' );

drop policy if exists "Admin write products bucket" on storage.objects;
create policy "Admin write products bucket"
on storage.objects for all
using (
  bucket_id = 'products' and
  exists(
    select 1
    from app_users u
    join user_roles ur on ur.user_id = u.id
    join app_roles r on r.id = ur.role_id
    where u.auth_user_id = auth.uid() and r.role_name = 'Admin'
  )
)
with check (
  bucket_id = 'products' and
  exists(
    select 1
    from app_users u
    join user_roles ur on ur.user_id = u.id
    join app_roles r on r.id = ur.role_id
    where u.auth_user_id = auth.uid() and r.role_name = 'Admin'
  )
);

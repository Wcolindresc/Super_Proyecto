select storage.create_bucket(
  'products',
  public := true,
  file_size_limit := 5242880::bigint,
  allowed_mime_types := array['image/jpeg','image/png','image/webp']
);

create policy if not exists "Public read products bucket"
on storage.objects for select
using ( bucket_id = 'products' );

create policy if not exists "Admin write products bucket"
on storage.objects for all
using (
  bucket_id='products' and
  exists(
    select 1 from app_users u
    join user_roles ur on ur.user_id=u.id
    join app_roles r on r.id=ur.role_id
    where u.auth_user_id=auth.uid() and r.role_name='Admin'
  )
)
with check (
  bucket_id='products' and
  exists(
    select 1 from app_users u
    join user_roles ur on ur.user_id=u.id
    join app_roles r on r.id=ur.role_id
    where u.auth_user_id=auth.uid() and r.role_name='Admin'
  )
);

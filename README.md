# La Bodegonea – Flask + Supabase + Front estático

## Paso a paso
1. Crea un proyecto **Supabase** y copia:
   - `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY` (API → Keys)
   - `DATABASE_URL` del **Connection Pooler** (puerto 6543) con `?sslmode=require` (Project Settings → Database → Connection pooling).
2. En tu repo GitHub agrega en **Settings → Secrets → Actions**:
   - `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `DATABASE_URL`, `FLASK_SECRET_KEY`.
   - Si usas **Render**: `RENDER_API_KEY`, `RENDER_SERVICE_ID`.
3. Corre el workflow **Provision Database** para aplicar migraciones `00→03`.
4. Crea un servicio web en **Render** (Python):
   - Build: `pip install -r requirements.txt`
   - Start: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2`
   - Variables de entorno: las mismas claves de arriba.
5. Pon la URL pública del backend en `dist/index.html` (reemplaza `REEMPLAZA_CON_URL_API`).
6. Publica GitHub Pages apuntando a la carpeta `/dist`.
7. En Supabase → Auth: invita `admin@labodegonea.gt` y `cliente@labodegonea.gt`. Actualiza `app_users.auth_user_id` con sus UUID y asigna rol Admin al primero.

## Endpoints
- `GET /api/products`
- `GET /api/products/:id`
- `POST /api/admin/products` (Admin)
- `POST /api/cart` (auth)
- `POST /api/orders/checkout` (auth)

## Notas
- RLS activo: públicos ven solo `published`.
- Storage bucket `products` con lectura pública y escritura solo Admin.
- Checkout descuenta stock via `inventory_movements`.

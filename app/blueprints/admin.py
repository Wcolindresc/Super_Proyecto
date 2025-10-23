# app/blueprints/admin.py  (fragmento nuevo al final)
from flask import request, jsonify
from ..auth import require_role
from ..supabase_client import supa_service

@bp.get("/me")
@require_role("Admin")
def who_am_i():
    return jsonify({"role": "Admin"}), 200

@bp.post("/upload")
@require_role("Admin")
def upload_image():
    from werkzeug.utils import secure_filename
    import time, mimetypes

    client = supa_service()

    if "file" not in request.files:
        return jsonify({"error": "no_file"}), 400

    f = request.files["file"]
    filename = secure_filename(f.filename or "upload.bin")
    mime = f.mimetype or mimetypes.guess_type(filename)[0] or "application/octet-stream"

    if mime not in ["image/jpeg", "image/png", "image/webp"]:
        return jsonify({"error": "unsupported_type"}), 400

    f.seek(0, 2); size = f.tell(); f.seek(0)
    if size > 5 * 1024 * 1024:
        return jsonify({"error": "too_large"}), 400

    prefix = request.form.get("prefix", "").strip().rstrip("/")
    ts = int(time.time())
    path = f"{prefix}/{ts}_{filename}" if prefix else f"{ts}_{filename}"

    data = f.read()
    res = client.storage.from_("products").upload(
        path=path, file=data, file_options={"content-type": mime, "upsert": True}
    )
    if getattr(res, "error", None):
        return jsonify({"error": "upload_failed", "detail": str(res.error)}), 500

    public_url = client.storage.from_("products").get_public_url(path)
    return jsonify({"path": path, "public_url": public_url}), 201

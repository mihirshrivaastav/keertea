import uuid
from pathlib import Path

from flask import Blueprint, current_app, jsonify, redirect, render_template, request, send_from_directory, url_for
from werkzeug.utils import secure_filename

from tapri.services.auth import (
    admin_login_required,
    authenticate_admin,
    is_admin_authenticated,
    login_admin,
    logout_admin,
)
from tapri.services.catalog import (
    allowed_image_file,
    create_product,
    delete_product,
    list_admin_products,
    update_product,
)
from tapri.services.orders import list_orders


admin_bp = Blueprint("admin", __name__)


@admin_bp.get("/admin/login")
def login_page():
    if is_admin_authenticated():
        return redirect(url_for("admin.admin_page"))
    return render_template("admin_login.html", error=None)


@admin_bp.post("/admin/login")
def login_submit():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    next_url = request.args.get("next") or request.form.get("next") or url_for("admin.admin_page")

    if authenticate_admin(username, password):
        login_admin(username)
        return redirect(next_url)

    return render_template(
        "admin_login.html",
        error="Invalid username or password.",
    ), 401


@admin_bp.post("/admin/logout")
@admin_login_required
def logout_submit():
    logout_admin()
    return redirect(url_for("admin.login_page"))


@admin_bp.get("/admin")
@admin_login_required
def admin_page():
    return render_template("admin.html")


@admin_bp.get("/uploads/<path:filename>")
@admin_login_required
def uploaded_file(filename):
    return send_from_directory(current_app.config["UPLOAD_DIR"], filename)


@admin_bp.get("/api/admin/products")
@admin_login_required
def admin_products():
    return jsonify(list_admin_products())


@admin_bp.post("/api/admin/uploads")
@admin_login_required
def upload_image():
    image = request.files.get("image")
    if image is None or not image.filename:
        return jsonify({"error": "Please choose an image to upload."}), 400
    if not allowed_image_file(image.filename):
        return jsonify({"error": "Unsupported image format. Use PNG, JPG, JPEG, WEBP, or GIF."}), 400

    safe_name = secure_filename(image.filename)
    suffix = Path(safe_name).suffix.lower()
    saved_name = f"{uuid.uuid4().hex}{suffix}"
    upload_path = current_app.config["UPLOAD_DIR"] / saved_name
    image.save(upload_path)
    return jsonify({"url": f"/uploads/{saved_name}", "filename": safe_name}), 201


@admin_bp.post("/api/admin/products")
@admin_login_required
def create_product_route():
    product = create_product(request.get_json(force=True))
    return jsonify(product), 201


@admin_bp.put("/api/admin/products/<int:product_id>")
@admin_login_required
def update_product_route(product_id):
    product = update_product(product_id, request.get_json(force=True))
    if product is None:
        return jsonify({"error": "Product not found."}), 404
    return jsonify(product)


@admin_bp.delete("/api/admin/products/<int:product_id>")
@admin_login_required
def delete_product_route(product_id):
    delete_product(product_id)
    return jsonify({"ok": True})


@admin_bp.get("/api/admin/orders")
@admin_login_required
def orders_route():
    return jsonify(list_orders())

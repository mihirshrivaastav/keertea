from pathlib import Path

from flask import current_app

from tapri.db import fetch_all, fetch_one, get_db


def serialize_product(row):
    return {
        "id": row["id"],
        "name": row["name"],
        "category": row["category"],
        "pricePerUnit": row["price_per_unit"],
        "unit": row["unit"],
        "minWeight": row["min_weight"],
        "maxWeight": row["max_weight"],
        "badge": row["badge"],
        "rating": row["rating"],
        "desc": row["description"],
        "img": row["image_url"],
        "imageVersion": row["updated_at"],
        "inventoryGrams": row["inventory_grams"],
        "isActive": bool(row["is_active"]),
    }


def list_public_products():
    rows = fetch_all("SELECT * FROM products WHERE is_active = 1 ORDER BY id")
    return [serialize_product(row) for row in rows]


def list_admin_products():
    rows = fetch_all("SELECT * FROM products ORDER BY id DESC")
    return [serialize_product(row) for row in rows]


def allowed_image_file(filename):
    return Path(filename).suffix.lower() in current_app.config["ALLOWED_IMAGE_EXTENSIONS"]


def create_product(data):
    db = get_db()
    payload = (
        data["name"],
        data["category"],
        float(data["pricePerUnit"]),
        data["unit"],
        int(data["minWeight"]),
        int(data["maxWeight"]),
        data.get("badge", "New"),
        data.get("rating", "★★★★★"),
        data["desc"],
        data["img"],
        int(data.get("inventoryGrams", 0)),
        1 if data.get("isActive", True) else 0,
    )
    cursor = db.execute(
        """
        INSERT INTO products
        (name, category, price_per_unit, unit, min_weight, max_weight, badge, rating,
         description, image_url, inventory_grams, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        payload,
    )
    db.commit()
    return serialize_product(fetch_one("SELECT * FROM products WHERE id = ?", (cursor.lastrowid,)))


def update_product(product_id, data):
    db = get_db()
    db.execute(
        """
        UPDATE products
        SET name = ?, category = ?, price_per_unit = ?, unit = ?, min_weight = ?, max_weight = ?,
            badge = ?, rating = ?, description = ?, image_url = ?, inventory_grams = ?, is_active = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            data["name"],
            data["category"],
            float(data["pricePerUnit"]),
            data["unit"],
            int(data["minWeight"]),
            int(data["maxWeight"]),
            data.get("badge", "New"),
            data.get("rating", "★★★★★"),
            data["desc"],
            data["img"],
            int(data.get("inventoryGrams", 0)),
            1 if data.get("isActive", True) else 0,
            product_id,
        ),
    )
    db.commit()
    row = fetch_one("SELECT * FROM products WHERE id = ?", (product_id,))
    return serialize_product(row) if row else None


def delete_product(product_id):
    db = get_db()
    db.execute("DELETE FROM products WHERE id = ?", (product_id,))
    db.commit()

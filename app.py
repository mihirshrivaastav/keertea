import json
import os
import sqlite3
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from base64 import b64encode
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(tempfile.gettempdir()) / "Tapri"
DB_PATH = DATA_DIR / "tapri.db"

app = Flask(__name__, static_folder=".", static_url_path="")


DEFAULT_PRODUCTS = [
    {
        "name": "Prakriti Chai",
        "category": "Tea Leaves",
        "price_per_unit": 400,
        "unit": "kg",
        "min_weight": 100,
        "max_weight": 5000,
        "badge": "Natural",
        "rating": "★★★★★",
        "description": "Natural and fresh - the purest chai experience with authentic flavors.",
        "image_url": "https://images.unsplash.com/photo-1563822249366-3efb23b8e0c9?w=500&q=80",
        "inventory_grams": 30000,
        "is_active": 1,
    },
    {
        "name": "Vanam Chai",
        "category": "Tea Leaves",
        "price_per_unit": 500,
        "unit": "kg",
        "min_weight": 100,
        "max_weight": 5000,
        "badge": "Forest-Grown",
        "rating": "★★★★★",
        "description": "Forest-grown richness - deep, aromatic chai with natural complexity.",
        "image_url": "https://images.unsplash.com/photo-1571934811356-5cc061b6821f?w=500&q=80",
        "inventory_grams": 22000,
        "is_active": 1,
    },
    {
        "name": "Amrit Chai",
        "category": "Tea Leaves",
        "price_per_unit": 600,
        "unit": "kg",
        "min_weight": 100,
        "max_weight": 5000,
        "badge": "Premium",
        "rating": "★★★★★",
        "description": "Finest, nectar-like quality - the ultimate treasured chai blend.",
        "image_url": "https://images.unsplash.com/photo-1597318130435-95e3e4589e98?w=500&q=80",
        "inventory_grams": 18000,
        "is_active": 1,
    },
    {
        "name": "Kaju",
        "category": "Cashew Nuts",
        "price_per_unit": 1200,
        "unit": "kg",
        "min_weight": 100,
        "max_weight": 5000,
        "badge": "Handpicked",
        "rating": "★★★★★",
        "description": "Handpicked cashew nuts with premium quality and natural richness.",
        "image_url": "https://images.unsplash.com/photo-1590779033100-9f60a05a013d?w=500&q=80",
        "inventory_grams": 12000,
        "is_active": 1,
    },
    {
        "name": "Elaichi",
        "category": "Elaichi",
        "price_per_unit": 500,
        "unit": "100g",
        "min_weight": 10,
        "max_weight": 1000,
        "badge": "Handpicked",
        "rating": "★★★★★",
        "description": "Handpicked and fresh - aromatic green cardamom pods for chai and cooking.",
        "image_url": "https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=500&q=80",
        "inventory_grams": 4000,
        "is_active": 1,
    },
]


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = get_db()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price_per_unit REAL NOT NULL,
            unit TEXT NOT NULL,
            min_weight INTEGER NOT NULL,
            max_weight INTEGER NOT NULL,
            badge TEXT NOT NULL,
            rating TEXT NOT NULL,
            description TEXT NOT NULL,
            image_url TEXT NOT NULL,
            inventory_grams INTEGER NOT NULL DEFAULT 0,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            address TEXT NOT NULL,
            payment_method TEXT NOT NULL,
            payment_provider TEXT NOT NULL DEFAULT 'manual',
            payment_status TEXT NOT NULL DEFAULT 'pending',
            payment_reference TEXT,
            subtotal REAL NOT NULL,
            total REAL NOT NULL,
            order_status TEXT NOT NULL DEFAULT 'placed',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            unit TEXT NOT NULL,
            selected_weight INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            line_total REAL NOT NULL,
            FOREIGN KEY(order_id) REFERENCES orders(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        );
        """
    )

    existing = conn.execute("SELECT COUNT(*) AS count FROM products").fetchone()["count"]
    if existing == 0:
        conn.executemany(
            """
            INSERT INTO products
            (name, category, price_per_unit, unit, min_weight, max_weight, badge, rating,
             description, image_url, inventory_grams, is_active)
            VALUES
            (:name, :category, :price_per_unit, :unit, :min_weight, :max_weight, :badge, :rating,
             :description, :image_url, :inventory_grams, :is_active)
            """,
            DEFAULT_PRODUCTS,
        )
    conn.commit()
    conn.close()


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
        "inventoryGrams": row["inventory_grams"],
        "isActive": bool(row["is_active"]),
    }


def compute_item_price(product, weight):
    if product["unit"] == "kg":
        return product["price_per_unit"] * weight / 1000
    return product["price_per_unit"] * weight / 100


def normalize_payment_method(value):
    payment_method = (value or "").strip().lower()
    allowed = {
        "cash on delivery": ("manual", "pending"),
        "upi / gpay / phonepe": ("razorpay", "pending"),
        "credit / debit card": ("stripe", "pending"),
        "net banking": ("razorpay", "pending"),
    }
    return allowed.get(payment_method, ("manual", "pending"))


def call_payment_provider(provider, amount_rupees, order_id, customer_name):
    if provider == "manual":
        return {"status": "pending", "reference": f"COD-{order_id}", "message": "Cash on delivery selected."}

    amount_paise = int(round(amount_rupees * 100))
    if provider == "stripe":
        secret = os.getenv("STRIPE_SECRET_KEY")
        if not secret:
            raise ValueError("Stripe is not configured. Set STRIPE_SECRET_KEY to enable card payments.")
        payload = urllib.parse.urlencode(
            {
                "amount": amount_paise,
                "currency": "inr",
                "description": f"Tapri order #{order_id} for {customer_name}",
                "metadata[order_id]": order_id,
            }
        ).encode()
        req = urllib.request.Request(
            "https://api.stripe.com/v1/payment_intents",
            data=payload,
            method="POST",
            headers={
                "Authorization": f"Bearer {secret}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        with urllib.request.urlopen(req, timeout=20) as response:
            body = json.loads(response.read().decode())
        return {
            "status": body.get("status", "requires_payment_method"),
            "reference": body["id"],
            "clientSecret": body.get("client_secret"),
            "message": "Stripe payment intent created.",
        }

    if provider == "razorpay":
        key_id = os.getenv("RAZORPAY_KEY_ID")
        key_secret = os.getenv("RAZORPAY_KEY_SECRET")
        if not key_id or not key_secret:
            raise ValueError("Razorpay is not configured. Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET.")
        payload = json.dumps(
            {
                "amount": amount_paise,
                "currency": "INR",
                "receipt": f"tapri-{order_id}",
                "notes": {"customer_name": customer_name},
            }
        ).encode()
        auth = b64encode(f"{key_id}:{key_secret}".encode()).decode()
        req = urllib.request.Request(
            "https://api.razorpay.com/v1/orders",
            data=payload,
            method="POST",
            headers={
                "Authorization": f"Basic {auth}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=20) as response:
            body = json.loads(response.read().decode())
        return {
            "status": body.get("status", "created"),
            "reference": body["id"],
            "keyId": key_id,
            "amount": body.get("amount"),
            "message": "Razorpay order created.",
        }

    raise ValueError("Unsupported payment provider.")


def build_order_payload(order_row, items):
    return {
        "id": order_row["id"],
        "customerName": order_row["customer_name"],
        "phone": order_row["phone"],
        "address": order_row["address"],
        "paymentMethod": order_row["payment_method"],
        "paymentProvider": order_row["payment_provider"],
        "paymentStatus": order_row["payment_status"],
        "paymentReference": order_row["payment_reference"],
        "subtotal": order_row["subtotal"],
        "total": order_row["total"],
        "orderStatus": order_row["order_status"],
        "createdAt": order_row["created_at"],
        "items": items,
    }


@app.get("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")


@app.get("/admin")
def admin():
    return send_from_directory(BASE_DIR, "admin.html")


@app.get("/api/products")
def list_products():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM products WHERE is_active = 1 ORDER BY id"
    ).fetchall()
    conn.close()
    return jsonify([serialize_product(row) for row in rows])


@app.get("/api/admin/products")
def admin_products():
    conn = get_db()
    rows = conn.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
    conn.close()
    return jsonify([serialize_product(row) for row in rows])


@app.post("/api/admin/products")
def create_product():
    data = request.get_json(force=True)
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
    conn = get_db()
    cur = conn.execute(
        """
        INSERT INTO products
        (name, category, price_per_unit, unit, min_weight, max_weight, badge, rating,
         description, image_url, inventory_grams, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        payload,
    )
    conn.commit()
    row = conn.execute("SELECT * FROM products WHERE id = ?", (cur.lastrowid,)).fetchone()
    conn.close()
    return jsonify(serialize_product(row)), 201


@app.put("/api/admin/products/<int:product_id>")
def update_product(product_id):
    data = request.get_json(force=True)
    conn = get_db()
    conn.execute(
        """
        UPDATE products
        SET name = ?, category = ?, price_per_unit = ?, unit = ?, min_weight = ?, max_weight = ?,
            badge = ?, rating = ?, description = ?, image_url = ?, inventory_grams = ?, is_active = ?
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
    conn.commit()
    row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    conn.close()
    return jsonify(serialize_product(row))


@app.delete("/api/admin/products/<int:product_id>")
def delete_product(product_id):
    conn = get_db()
    conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.get("/api/admin/orders")
def list_orders():
    conn = get_db()
    order_rows = conn.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
    result = []
    for order_row in order_rows:
        item_rows = conn.execute(
            """
            SELECT product_id, product_name, unit, selected_weight, quantity, unit_price, line_total
            FROM order_items
            WHERE order_id = ?
            ORDER BY id
            """,
            (order_row["id"],),
        ).fetchall()
        result.append(
            build_order_payload(
                order_row,
                [
                    {
                        "productId": item["product_id"],
                        "productName": item["product_name"],
                        "unit": item["unit"],
                        "selectedWeight": item["selected_weight"],
                        "quantity": item["quantity"],
                        "unitPrice": item["unit_price"],
                        "lineTotal": item["line_total"],
                    }
                    for item in item_rows
                ],
            )
        )
    conn.close()
    return jsonify(result)


@app.post("/api/orders")
def create_order():
    data = request.get_json(force=True)
    items = data.get("items", [])
    if not items:
        return jsonify({"error": "Cart is empty."}), 400

    customer_name = data.get("customerName", "").strip()
    phone = data.get("phone", "").strip()
    address = data.get("address", "").strip()
    payment_method = data.get("paymentMethod", "").strip()
    if not customer_name or not phone or not address or not payment_method:
        return jsonify({"error": "Customer name, phone, address, and payment method are required."}), 400

    conn = get_db()
    normalized_items = []
    subtotal = 0.0

    for item in items:
        product = conn.execute("SELECT * FROM products WHERE id = ? AND is_active = 1", (item["id"],)).fetchone()
        if not product:
            conn.close()
            return jsonify({"error": f"Product {item.get('id')} is unavailable."}), 404

        weight = int(item.get("weight", 0))
        qty = int(item.get("qty", 0))
        if weight < product["min_weight"] or weight > product["max_weight"]:
            conn.close()
            return jsonify({"error": f"Invalid weight selected for {product['name']}."}), 400
        if qty < 1:
            conn.close()
            return jsonify({"error": f"Invalid quantity selected for {product['name']}."}), 400

        required_grams = weight * qty
        if required_grams > product["inventory_grams"]:
            conn.close()
            return jsonify({"error": f"Only {product['inventory_grams']}g of {product['name']} is left in stock."}), 400

        unit_price = compute_item_price(product, weight)
        line_total = unit_price * qty
        subtotal += line_total
        normalized_items.append(
            {
                "product": product,
                "weight": weight,
                "qty": qty,
                "unit_price": unit_price,
                "line_total": line_total,
            }
        )

    provider, payment_status = normalize_payment_method(payment_method)
    cur = conn.execute(
        """
        INSERT INTO orders
        (customer_name, phone, address, payment_method, payment_provider, payment_status, subtotal, total)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (customer_name, phone, address, payment_method, provider, payment_status, subtotal, subtotal),
    )
    order_id = cur.lastrowid

    for item in normalized_items:
        conn.execute(
            """
            INSERT INTO order_items
            (order_id, product_id, product_name, unit, selected_weight, quantity, unit_price, line_total)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                order_id,
                item["product"]["id"],
                item["product"]["name"],
                item["product"]["unit"],
                item["weight"],
                item["qty"],
                item["unit_price"],
                item["line_total"],
            ),
        )
        conn.execute(
            "UPDATE products SET inventory_grams = inventory_grams - ? WHERE id = ?",
            (item["weight"] * item["qty"], item["product"]["id"]),
        )

    try:
        payment = call_payment_provider(provider, subtotal, order_id, customer_name)
    except ValueError as exc:
        conn.execute(
            "UPDATE orders SET payment_status = ?, payment_reference = ? WHERE id = ?",
            ("configuration_required", "", order_id),
        )
        conn.commit()
        conn.close()
        return jsonify({"error": str(exc), "orderId": order_id}), 400
    except urllib.error.HTTPError as exc:
        body = exc.read().decode()
        conn.execute(
            "UPDATE orders SET payment_status = ?, payment_reference = ? WHERE id = ?",
            ("failed", "", order_id),
        )
        conn.commit()
        conn.close()
        return jsonify({"error": f"Payment provider rejected the request: {body}", "orderId": order_id}), 502

    conn.execute(
        "UPDATE orders SET payment_status = ?, payment_reference = ? WHERE id = ?",
        (payment["status"], payment.get("reference", ""), order_id),
    )
    conn.commit()

    order_row = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    item_rows = conn.execute(
        """
        SELECT product_id, product_name, unit, selected_weight, quantity, unit_price, line_total
        FROM order_items
        WHERE order_id = ?
        ORDER BY id
        """,
        (order_id,),
    ).fetchall()
    conn.close()

    return jsonify(
        {
            "message": "Order placed successfully.",
            "order": build_order_payload(
                order_row,
                [
                    {
                        "productId": item["product_id"],
                        "productName": item["product_name"],
                        "unit": item["unit"],
                        "selectedWeight": item["selected_weight"],
                        "quantity": item["quantity"],
                        "unitPrice": item["unit_price"],
                        "lineTotal": item["line_total"],
                    }
                    for item in item_rows
                ],
            ),
            "payment": payment,
        }
    ), 201


@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "timestamp": datetime.utcnow().isoformat() + "Z"})


if __name__ == "__main__":
    init_db()
    app.run(debug=False, use_reloader=False, port=5000)

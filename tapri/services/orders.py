import urllib.error

from tapri.db import fetch_all, fetch_one, get_db
from tapri.services.payments import call_payment_provider, normalize_payment_method


def compute_item_price(product, weight):
    if product["unit"] == "kg":
        return product["price_per_unit"] * weight / 1000
    return product["price_per_unit"] * weight / 100


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


def fetch_order_items(order_id):
    rows = fetch_all(
        """
        SELECT product_id, product_name, unit, selected_weight, quantity, unit_price, line_total
        FROM order_items
        WHERE order_id = ?
        ORDER BY id
        """,
        (order_id,),
    )
    return [
        {
            "productId": item["product_id"],
            "productName": item["product_name"],
            "unit": item["unit"],
            "selectedWeight": item["selected_weight"],
            "quantity": item["quantity"],
            "unitPrice": item["unit_price"],
            "lineTotal": item["line_total"],
        }
        for item in rows
    ]


def list_orders():
    orders = []
    for row in fetch_all("SELECT * FROM orders ORDER BY id DESC"):
        orders.append(build_order_payload(row, fetch_order_items(row["id"])))
    return orders


def create_order(data):
    items = data.get("items", [])
    if not items:
        return {"error": "Cart is empty."}, 400

    customer_name = data.get("customerName", "").strip()
    phone = data.get("phone", "").strip()
    address = data.get("address", "").strip()
    payment_method = data.get("paymentMethod", "").strip()
    if not customer_name or not phone or not address or not payment_method:
        return {"error": "Customer name, phone, address, and payment method are required."}, 400

    db = get_db()
    normalized_items = []
    subtotal = 0.0

    # We normalize every line item up front so validation failures happen before any writes.
    for item in items:
        product = fetch_one("SELECT * FROM products WHERE id = ? AND is_active = 1", (item["id"],))
        if not product:
            return {"error": f"Product {item.get('id')} is unavailable."}, 404

        weight = int(item.get("weight", 0))
        quantity = int(item.get("qty", 0))
        if weight < product["min_weight"] or weight > product["max_weight"]:
            return {"error": f"Invalid weight selected for {product['name']}."}, 400
        if quantity < 1:
            return {"error": f"Invalid quantity selected for {product['name']}."}, 400

        required_grams = weight * quantity
        if required_grams > product["inventory_grams"]:
            return {"error": f"Only {product['inventory_grams']}g of {product['name']} is left in stock."}, 400

        unit_price = compute_item_price(product, weight)
        line_total = unit_price * quantity
        subtotal += line_total
        normalized_items.append(
            {
                "product": product,
                "weight": weight,
                "quantity": quantity,
                "unit_price": unit_price,
                "line_total": line_total,
            }
        )

    provider, payment_status = normalize_payment_method(payment_method)
    cursor = db.execute(
        """
        INSERT INTO orders
        (customer_name, phone, address, payment_method, payment_provider, payment_status, subtotal, total)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (customer_name, phone, address, payment_method, provider, payment_status, subtotal, subtotal),
    )
    order_id = cursor.lastrowid

    for item in normalized_items:
        db.execute(
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
                item["quantity"],
                item["unit_price"],
                item["line_total"],
            ),
        )
        db.execute(
            "UPDATE products SET inventory_grams = inventory_grams - ? WHERE id = ?",
            (item["weight"] * item["quantity"], item["product"]["id"]),
        )

    try:
        payment = call_payment_provider(provider, subtotal, order_id, customer_name)
    except ValueError as exc:
        db.execute(
            "UPDATE orders SET payment_status = ?, payment_reference = ? WHERE id = ?",
            ("configuration_required", "", order_id),
        )
        db.commit()
        return {"error": str(exc), "orderId": order_id}, 400
    except urllib.error.HTTPError as exc:
        body = exc.read().decode()
        db.execute(
            "UPDATE orders SET payment_status = ?, payment_reference = ? WHERE id = ?",
            ("failed", "", order_id),
        )
        db.commit()
        return {"error": f"Payment provider rejected the request: {body}", "orderId": order_id}, 502

    db.execute(
        "UPDATE orders SET payment_status = ?, payment_reference = ? WHERE id = ?",
        (payment["status"], payment.get("reference", ""), order_id),
    )
    db.commit()

    order_row = fetch_one("SELECT * FROM orders WHERE id = ?", (order_id,))
    return {
        "message": "Order placed successfully.",
        "order": build_order_payload(order_row, fetch_order_items(order_id)),
        "payment": payment,
    }, 201

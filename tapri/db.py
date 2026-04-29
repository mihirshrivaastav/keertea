import sqlite3
from contextlib import closing
from datetime import datetime

from flask import current_app, g

from tapri.seed import DEFAULT_PRODUCTS


SCHEMA = """
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
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
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


def ensure_storage_dirs():
    current_app.config["DATA_DIR"].mkdir(parents=True, exist_ok=True)
    current_app.config["UPLOAD_DIR"].mkdir(parents=True, exist_ok=True)


def get_db():
    if "db" not in g:
        ensure_storage_dirs()
        db_path = current_app.config["DB_PATH"]
        # check_same_thread=False keeps the connection usable inside Flask request handling.
        g.db = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES, check_same_thread=False)
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def initialize_database():
    with current_app.app_context():
        db = get_db()
        try:
            db.executescript(SCHEMA)
        except sqlite3.OperationalError as exc:
            if "disk I/O error" not in str(exc):
                raise

            broken_path = current_app.config["DB_PATH"].with_suffix(
                f".broken-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.db"
            )
            close_db()
            current_app.config["DB_PATH"].replace(broken_path)
            db = get_db()
            db.executescript(SCHEMA)

        product_columns = {row["name"] for row in db.execute("PRAGMA table_info(products)").fetchall()}
        if "updated_at" not in product_columns:
            db.execute("ALTER TABLE products ADD COLUMN updated_at TEXT")
            db.execute("UPDATE products SET updated_at = COALESCE(updated_at, created_at, CURRENT_TIMESTAMP)")

        existing = db.execute("SELECT COUNT(*) AS count FROM products").fetchone()["count"]
        if existing == 0:
            db.executemany(
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

        db.commit()


def fetch_all(query, params=()):
    with closing(get_db().execute(query, params)) as cursor:
        return cursor.fetchall()


def fetch_one(query, params=()):
    with closing(get_db().execute(query, params)) as cursor:
        return cursor.fetchone()

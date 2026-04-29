# KeerTea Naturals

KeerTea Naturals is a small full-stack storefront and admin system for selling chai and related products. The current version is a Flask application with a customer-facing storefront, an authenticated admin panel, SQLite storage, order handling, inventory tracking, local image uploads, and payment-provider integration hooks.

The storefront content is tailored to the business details currently used in the site:

- Established in `1995`
- Based in `Varanasi`
- Products sourced directly from `Darjiling`, `Assam`, and `Tamil Nadu`
- Serves both `B2B` and `B2C` customers

## What This Project Does

- Shows products on a storefront page
- Lets customers add items to cart and place orders
- Stores order and customer details
- Tracks inventory in grams
- Provides an admin login page
- Restricts admin product and order actions to authenticated admins
- Lets admins add, edit, delete, activate, and deactivate products
- Lets admins upload product images
- Lets admins view incoming orders
- Prepares backend integration points for Razorpay and Stripe

## Tech Stack

- Frontend: `HTML`, `CSS`, `JavaScript`
- Backend: `Python`, `Flask`
- Database: `SQLite`
- Authentication: Flask session-based admin login
- Storage: local `uploads/` for images
- Payments: Razorpay / Stripe integration hooks

## Current Project Structure

```text
Tapri/
|-- app.py
|-- requirements.txt
|-- uploads/
|-- tapri/
|   |-- __init__.py
|   |-- config.py
|   |-- db.py
|   |-- seed.py
|   |-- routes/
|   |   |-- admin.py
|   |   |-- orders.py
|   |   `-- storefront.py
|   |-- services/
|   |   |-- auth.py
|   |   |-- catalog.py
|   |   |-- orders.py
|   |   `-- payments.py
|   |-- static/
|   |   |-- css/
|   |   |   |-- admin-auth.css
|   |   |   |-- admin.css
|   |   |   `-- styles.css
|   |   `-- js/
|   |       |-- admin.js
|   |       `-- storefront.js
|   `-- templates/
|       |-- admin.html
|       |-- admin_login.html
|       `-- index.html
`-- README.md
```

## File Guide

### Entry Point

- [app.py](C:/Users/mihir/OneDrive/Desktop/DAILY/Tapri/app.py)
  Minimal runtime entrypoint that creates the Flask app and starts the server.

### App Setup

- [tapri/__init__.py](C:/Users/mihir/OneDrive/Desktop/DAILY/Tapri/tapri/__init__.py)
  App factory, blueprint registration, error handling, and database initialization.

- [tapri/config.py](C:/Users/mihir/OneDrive/Desktop/DAILY/Tapri/tapri/config.py)
  Central configuration for DB path, uploads path, admin credentials, secret key, and payment env values.

- [tapri/db.py](C:/Users/mihir/OneDrive/Desktop/DAILY/Tapri/tapri/db.py)
  SQLite connection helpers, schema setup, and seed bootstrap.

- [tapri/seed.py](C:/Users/mihir/OneDrive/Desktop/DAILY/Tapri/tapri/seed.py)
  Default products inserted on first startup.

### Routes

- [tapri/routes/storefront.py](C:/Users/mihir/OneDrive/Desktop/DAILY/Tapri/tapri/routes/storefront.py)
  Storefront page route and public API endpoints.

- [tapri/routes/admin.py](C:/Users/mihir/OneDrive/Desktop/DAILY/Tapri/tapri/routes/admin.py)
  Admin login, logout, admin page, admin APIs, and upload route.

- [tapri/routes/orders.py](C:/Users/mihir/OneDrive/Desktop/DAILY/Tapri/tapri/routes/orders.py)
  Customer order creation API.

### Services

- [tapri/services/auth.py](C:/Users/mihir/OneDrive/Desktop/DAILY/Tapri/tapri/services/auth.py)
  Admin authentication helpers and route protection decorator.

- [tapri/services/catalog.py](C:/Users/mihir/OneDrive/Desktop/DAILY/Tapri/tapri/services/catalog.py)
  Product serialization and product CRUD logic.

- [tapri/services/orders.py](C:/Users/mihir/OneDrive/Desktop/DAILY/Tapri/tapri/services/orders.py)
  Order validation, stock deduction, and order payload shaping.

- [tapri/services/payments.py](C:/Users/mihir/OneDrive/Desktop/DAILY/Tapri/tapri/services/payments.py)
  Razorpay and Stripe request builders.

### Templates

- [tapri/templates/index.html](C:/Users/mihir/OneDrive/Desktop/DAILY/Tapri/tapri/templates/index.html)
  Storefront page with shop story, sourcing details, product grid, checkout, and contact section.

- [tapri/templates/admin_login.html](C:/Users/mihir/OneDrive/Desktop/DAILY/Tapri/tapri/templates/admin_login.html)
  Admin sign-in page.

- [tapri/templates/admin.html](C:/Users/mihir/OneDrive/Desktop/DAILY/Tapri/tapri/templates/admin.html)
  Authenticated admin dashboard.

### Frontend Assets

- [tapri/static/js/storefront.js](C:/Users/mihir/OneDrive/Desktop/DAILY/Tapri/tapri/static/js/storefront.js)
  Customer storefront behavior such as product rendering, cart state, background sync, and checkout.

- [tapri/static/js/admin.js](C:/Users/mihir/OneDrive/Desktop/DAILY/Tapri/tapri/static/js/admin.js)
  Admin product editor behavior, order listing, upload flow, and fetch helpers.

- [tapri/static/css/styles.css](C:/Users/mihir/OneDrive/Desktop/DAILY/Tapri/tapri/static/css/styles.css)
  Storefront styles.

- [tapri/static/css/admin.css](C:/Users/mihir/OneDrive/Desktop/DAILY/Tapri/tapri/static/css/admin.css)
  Admin dashboard styles.

- [tapri/static/css/admin-auth.css](C:/Users/mihir/OneDrive/Desktop/DAILY/Tapri/tapri/static/css/admin-auth.css)
  Admin login page styles.

## Database

The app uses SQLite with these main tables:

- `products`
- `orders`
- `order_items`

### Database Location

Because this workspace is inside a synced OneDrive folder, SQLite writes in the repo folder can fail with `disk I/O error`. The running app uses a temp-backed writable location instead:

`C:\Users\mihir\AppData\Local\Temp\TapriData\tapri.db`

This path is created automatically by the app config and database setup logic.

## Authentication

The admin panel is now protected by login.

### Admin URLs

- Login: [http://127.0.0.1:5000/admin/login](http://127.0.0.1:5000/admin/login)
- Dashboard: [http://127.0.0.1:5000/admin](http://127.0.0.1:5000/admin)

### Default Admin Credentials

- Username: `admin`
- Password: `admin123`

These should be changed for any real deployment through environment variables.

### Admin Environment Variables

- `SECRET_KEY`
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`

## API Endpoints

### Public

- `GET /`
  Serves the storefront page.

- `GET /api/products`
  Returns active products for the storefront.

- `POST /api/orders`
  Creates an order, validates stock, saves order items, and returns payment/order data.

- `GET /api/health`
  Simple health-check endpoint.

### Admin Auth

- `GET /admin/login`
  Serves the admin login page.

- `POST /admin/login`
  Authenticates an admin and creates a session.

- `POST /admin/logout`
  Clears the admin session.

### Protected Admin

- `GET /admin`
  Serves the admin dashboard.

- `GET /api/admin/products`
  Returns all products.

- `POST /api/admin/products`
  Creates a new product.

- `PUT /api/admin/products/<id>`
  Updates a product.

- `DELETE /api/admin/products/<id>`
  Deletes a product.

- `POST /api/admin/uploads`
  Uploads a product image and returns its local URL.

- `GET /api/admin/orders`
  Returns all saved orders.

## Payment Integration

The backend is prepared for two payment providers:

- `Razorpay`
- `Stripe`

### Current Status

- `Cash on Delivery` works end-to-end
- Razorpay and Stripe are structurally wired, but production credentials and payment confirmation handling are still needed

### Payment Environment Variables

- `STRIPE_SECRET_KEY`
- `RAZORPAY_KEY_ID`
- `RAZORPAY_KEY_SECRET`

If these are missing, the API returns a configuration error for those payment methods.

## How To Run The Project

### Install Dependencies

```powershell
python -m pip install -r requirements.txt
```

### Start The Server

```powershell
python -B app.py
```

### Open In Browser

- Storefront: [http://127.0.0.1:5000](http://127.0.0.1:5000)
- Admin login: [http://127.0.0.1:5000/admin/login](http://127.0.0.1:5000/admin/login)

## Why `python -B` Is Used

This workspace has shown flaky behavior when Python tries to write bytecode files (`__pycache__`) inside the synced folder. Running with `-B` disables bytecode generation and avoids those issues.

## What The Storefront Shows

The storefront now presents:

- Shop history since `1995`
- Varanasi-based business identity
- Direct sourcing from `Darjiling`, `Assam`, and `Tamil Nadu`
- B2B and B2C service positioning
- Contact details:
  - Address: `Golghar Kachari, Near Vissu Katra, Katra, Varanasi-221001, Uttar Pradesh`
  - Email: `mihir.srivastava001@gamil.com`

## Inventory Tracking

Each product stores stock in grams through `inventory_grams`. When an order is placed:

- product availability is validated
- order items are saved
- inventory is reduced

## Admin Panel Features

- Admin login/logout
- Add product
- Edit product
- Delete product
- Mark product active/inactive
- Set inventory amount
- Upload product image
- View orders

## Suggested Next Improvements

- Replace plain env-based admin credentials with hashed passwords in a user table
- Add `.env` loading support
- Add CSRF protection to admin login/logout and admin forms
- Move from SQLite to PostgreSQL for production
- Add schema migrations with Alembic
- Add payment webhooks and status reconciliation
- Add order status updates from admin
- Add product search/filtering in admin
- Add customer notifications
- Move uploads to cloud storage for production

## Summary

This project is now a refactored Flask application with:

- a storefront for customers
- a login-protected admin panel
- separated routes, services, templates, and static assets
- SQLite-backed catalog and order storage
- inventory tracking
- product image uploads
- payment integration hooks

That structure makes the project much easier to extend, debug, and maintain than the earlier single-file version.

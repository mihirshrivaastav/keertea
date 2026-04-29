from functools import wraps

from flask import current_app, jsonify, redirect, request, session, url_for


def is_admin_authenticated():
    return bool(session.get("is_admin_authenticated"))


def authenticate_admin(username, password):
    expected_username = current_app.config["ADMIN_USERNAME"]
    expected_password = current_app.config["ADMIN_PASSWORD"]
    return username == expected_username and password == expected_password


def login_admin(username):
    # Keeping only the small bits of session state we need makes debugging auth simpler.
    session.clear()
    session["is_admin_authenticated"] = True
    session["admin_username"] = username


def logout_admin():
    session.clear()


def admin_login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if is_admin_authenticated():
            return view(*args, **kwargs)

        if request.path.startswith("/api/"):
            return jsonify({"error": "Admin authentication required."}), 401

        next_url = request.path
        return redirect(url_for("admin.login_page", next=next_url))

    return wrapped_view

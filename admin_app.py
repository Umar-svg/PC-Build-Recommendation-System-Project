# admin_app.py — Standalone Admin Panel for PC Build Recommendation System
# Runs as a separate Flask application on port 5001
# Connects to the same MySQL database as app.py

import os

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash
)
from functools import wraps
from datetime import date, timedelta
import mysql.connector
import bcrypt
from config import Config

# ====================================================================
# ADMIN CREDENTIALS — CHANGE THESE TO WHATEVER YOU WANT
# ====================================================================
ADMIN_EMAIL    = "umar@gmail.com"
ADMIN_PASSWORD = "admin123"
ADMIN_NAME     = "Administrator"
# ====================================================================

# Component types — used in dropdowns and validation
COMPONENT_TYPES = ["CPU", "GPU", "RAM", "Motherboard", "Storage",
                   "PSU", "Case", "Cooler"]

# Conversion rate for the PKR display in logs/analytics
USD_TO_PKR = 280.0

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY + "_admin"


# ---------- Database helper ----------
def get_db():
    return mysql.connector.connect(
        host=app.config["MYSQL_HOST"],
        user=app.config["MYSQL_USER"],
        password=app.config["MYSQL_PASSWORD"],
        database=app.config["MYSQL_DB"],
        port=app.config["MYSQL_PORT"],
    )


# ---------- Auto-sync built-in admin into the User table on startup ----------
def ensure_builtin_admin():
    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT user_id FROM User WHERE email = %s",
                    (ADMIN_EMAIL.lower(),))
        existing = cur.fetchone()

        hashed = bcrypt.hashpw(ADMIN_PASSWORD.encode("utf-8"),
                               bcrypt.gensalt()).decode("utf-8")

        if existing:
            cur.execute(
                "UPDATE User SET role = 'admin', password = %s, full_name = %s "
                "WHERE email = %s",
                (hashed, ADMIN_NAME, ADMIN_EMAIL.lower()),
            )
            print(f"[admin] Built-in admin synced: {ADMIN_EMAIL}")
        else:
            cur.execute(
                "INSERT INTO User (full_name, email, password, role) "
                "VALUES (%s, %s, %s, 'admin')",
                (ADMIN_NAME, ADMIN_EMAIL.lower(), hashed),
            )
            print(f"[admin] Built-in admin created: {ADMIN_EMAIL}")

        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"[admin] WARNING: could not sync built-in admin: {e}")


# ---------- Auth decorator ----------
def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("admin_id"):
            flash("Please log in as an administrator.", "error")
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return wrapper


# Helper: check if Build_Request has currency/build_preference columns
# (depends on whether you've run the schema migration).
def get_request_columns():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SHOW COLUMNS FROM Build_Request")
        cols = {row[0] for row in cur.fetchall()}
        cur.close()
        conn.close()
        return cols
    except Exception:
        return {"request_id", "budget", "purpose", "request_date", "user_id"}


# ====================================================================
# AUTH ROUTES
# ====================================================================

@app.route("/")
def home():
    if session.get("admin_id"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("admin_login"))


@app.route("/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        # 1) Built-in admin
        if email == ADMIN_EMAIL.lower() and password == ADMIN_PASSWORD:
            conn = get_db()
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT user_id, full_name FROM User WHERE email = %s",
                        (ADMIN_EMAIL.lower(),))
            row = cur.fetchone()
            cur.close()
            conn.close()

            session["admin_id"]    = row["user_id"] if row else 0
            session["admin_name"]  = (row["full_name"] if row else None) or ADMIN_NAME
            session["admin_email"] = ADMIN_EMAIL
            flash(f"Welcome, {session['admin_name']}!", "success")
            return redirect(url_for("dashboard"))

        # 2) Database-stored admins
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT * FROM User WHERE email = %s AND role = 'admin'", (email,))
        admin = cur.fetchone()
        cur.close()
        conn.close()

        if admin:
            stored = admin["password"].encode("utf-8")
            if stored.startswith(b"$2") and bcrypt.checkpw(
                password.encode("utf-8"), stored
            ):
                session["admin_id"]    = admin["user_id"]
                session["admin_name"]  = admin["full_name"]
                session["admin_email"] = admin["email"]
                flash(f"Welcome, {admin['full_name']}!", "success")
                return redirect(url_for("dashboard"))

        flash("Invalid credentials or not an administrator.", "error")

    return render_template("admin/login.html")


@app.route("/logout")
def admin_logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("admin_login"))


# ====================================================================
# DASHBOARD
# ====================================================================

@app.route("/dashboard")
@admin_required
def dashboard():
    conn = get_db()
    cur = conn.cursor(dictionary=True)

    stats = {}
    cur.execute("SELECT COUNT(*) AS c FROM User WHERE role = 'user'")
    stats["total_users"] = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) AS c FROM User WHERE role = 'admin'")
    stats["total_admins"] = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) AS c FROM Component WHERE is_active = 1")
    stats["total_components"] = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) AS c FROM Build_Request")
    stats["total_requests"] = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) AS c FROM Recommended_Build")
    stats["total_builds"] = cur.fetchone()["c"]
    cur.execute("SELECT AVG(budget) AS a FROM Build_Request")
    avg = cur.fetchone()["a"]
    stats["avg_budget"] = round(float(avg), 2) if avg else 0.0
    cur.execute("""
        SELECT COUNT(*) AS c FROM Build_Request
        WHERE MONTH(request_date) = MONTH(CURDATE())
          AND YEAR(request_date)  = YEAR(CURDATE())
    """)
    stats["requests_this_month"] = cur.fetchone()["c"]
    cur.execute("SELECT COALESCE(SUM(total_cost), 0) AS s FROM Recommended_Build")
    stats["total_value"] = round(float(cur.fetchone()["s"]), 2)

    cur.execute("""
        SELECT br.request_id, u.full_name, br.purpose, br.budget, br.request_date,
               (SELECT COUNT(*) FROM Recommended_Build rb
                WHERE rb.request_id = br.request_id) AS build_count
        FROM Build_Request br
        JOIN User u ON br.user_id = u.user_id
        ORDER BY br.request_date DESC, br.request_id DESC
        LIMIT 8
    """)
    recent = cur.fetchall()
    for r in recent:
        r["budget"] = float(r["budget"])

    cur.execute("""
        SELECT c.component_name, c.component_type, c.brand,
               COUNT(bc.build_component_id) AS times_used
        FROM Build_Component bc
        JOIN Component c ON bc.component_id = c.component_id
        GROUP BY c.component_id
        ORDER BY times_used DESC
        LIMIT 5
    """)
    top_components = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "admin/dashboard.html",
        stats=stats, recent=recent, top_components=top_components,
        active_section="dashboard",
    )


# ====================================================================
# MANAGE COMPONENTS — full CRUD
# (UNCHANGED — keep your original component routes here)
# ====================================================================

@app.route("/components")
@admin_required
def components():
    q          = request.args.get("q", "").strip()
    type_filter = request.args.get("type", "").strip()
    status     = request.args.get("status", "active")

    sql = """
        SELECT c.component_id, c.component_name, c.component_type,
               c.brand, c.price, c.is_active,
               (SELECT COUNT(*) FROM Build_Component bc
                WHERE bc.component_id = c.component_id) AS times_used
        FROM Component c
        WHERE 1=1
    """
    params = []
    if q:
        sql += " AND (c.component_name LIKE %s OR c.brand LIKE %s)"
        params.extend([f"%{q}%", f"%{q}%"])
    if type_filter:
        sql += " AND c.component_type = %s"
        params.append(type_filter)
    if status == "active":
        sql += " AND c.is_active = 1"
    elif status == "inactive":
        sql += " AND c.is_active = 0"

    sql += " ORDER BY c.component_type, c.brand, c.component_name"

    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute(sql, params)
    rows = cur.fetchall()
    for r in rows:
        r["price"] = float(r["price"])
    cur.close()
    conn.close()

    return render_template(
        "admin/components/list.html",
        components=rows,
        q=q, type_filter=type_filter, status=status,
        component_types=COMPONENT_TYPES,
        active_section="components",
    )


@app.route("/components/new", methods=["GET", "POST"])
@admin_required
def component_new():
    if request.method == "POST":
        try:
            data = (
                request.form["component_name"].strip(),
                request.form["component_type"].strip(),
                request.form["brand"].strip(),
                float(request.form["price"]),
                request.form.get("specifications", "").strip() or None,
                request.form.get("compatibility_info", "").strip() or None,
            )
            if not data[0] or not data[2]:
                flash("Name and brand are required.", "error")
                return redirect(url_for("component_new"))
            if data[1] not in COMPONENT_TYPES:
                flash("Invalid component type.", "error")
                return redirect(url_for("component_new"))
            if data[3] < 0:
                flash("Price cannot be negative.", "error")
                return redirect(url_for("component_new"))

            conn = get_db()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO Component
                  (component_name, component_type, brand, price,
                   specifications, compatibility_info, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, 1)
            """, data)
            conn.commit()
            cur.close()
            conn.close()

            flash(f"Component '{data[0]}' added successfully.", "success")
            return redirect(url_for("components"))
        except ValueError:
            flash("Price must be a valid number.", "error")
        except mysql.connector.Error as err:
            flash(f"Database error: {err}", "error")

    return render_template(
        "admin/components/form.html",
        comp=None, component_types=COMPONENT_TYPES,
        active_section="components", form_title="Add New Component",
    )


@app.route("/components/<int:cid>/edit", methods=["GET", "POST"])
@admin_required
def component_edit(cid):
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    if request.method == "POST":
        try:
            data = (
                request.form["component_name"].strip(),
                request.form["component_type"].strip(),
                request.form["brand"].strip(),
                float(request.form["price"]),
                request.form.get("specifications", "").strip() or None,
                request.form.get("compatibility_info", "").strip() or None,
                cid,
            )
            if not data[0] or not data[2]:
                flash("Name and brand are required.", "error")
                return redirect(url_for("component_edit", cid=cid))
            if data[1] not in COMPONENT_TYPES:
                flash("Invalid component type.", "error")
                return redirect(url_for("component_edit", cid=cid))
            if data[3] < 0:
                flash("Price cannot be negative.", "error")
                return redirect(url_for("component_edit", cid=cid))

            cur.execute("""
                UPDATE Component
                SET component_name = %s, component_type = %s, brand = %s,
                    price = %s, specifications = %s, compatibility_info = %s
                WHERE component_id = %s
            """, data)
            conn.commit()
            cur.close()
            conn.close()
            flash(f"Component '{data[0]}' updated successfully.", "success")
            return redirect(url_for("components"))
        except ValueError:
            flash("Price must be a valid number.", "error")
        except mysql.connector.Error as err:
            flash(f"Database error: {err}", "error")

    cur.execute("SELECT * FROM Component WHERE component_id = %s", (cid,))
    comp = cur.fetchone()
    cur.close()
    conn.close()
    if not comp:
        flash("Component not found.", "error")
        return redirect(url_for("components"))
    comp["price"] = float(comp["price"])
    return render_template(
        "admin/components/form.html",
        comp=comp, component_types=COMPONENT_TYPES,
        active_section="components", form_title=f"Edit: {comp['component_name']}",
    )


@app.route("/components/<int:cid>/toggle", methods=["POST"])
@admin_required
def component_toggle(cid):
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT component_name, is_active FROM Component WHERE component_id = %s", (cid,))
    comp = cur.fetchone()
    if not comp:
        flash("Component not found.", "error")
    else:
        new_state = 0 if comp["is_active"] else 1
        cur.execute("UPDATE Component SET is_active = %s WHERE component_id = %s",
                    (new_state, cid))
        conn.commit()
        action = "restored" if new_state else "deactivated"
        flash(f"Component '{comp['component_name']}' {action}.", "success")
    cur.close()
    conn.close()
    return redirect(url_for("components"))


@app.route("/components/<int:cid>/delete", methods=["POST"])
@admin_required
def component_delete(cid):
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT component_name FROM Component WHERE component_id = %s", (cid,))
    comp = cur.fetchone()
    if not comp:
        flash("Component not found.", "error")
        cur.close()
        conn.close()
        return redirect(url_for("components"))
    cur.execute("SELECT COUNT(*) AS c FROM Build_Component WHERE component_id = %s", (cid,))
    used = cur.fetchone()["c"]
    if used > 0:
        flash(
            f"Cannot permanently delete '{comp['component_name']}' — it appears "
            f"in {used} build(s). Deactivate it instead.", "error")
    else:
        try:
            cur.execute("DELETE FROM Component WHERE component_id = %s", (cid,))
            conn.commit()
            flash(f"Component '{comp['component_name']}' permanently deleted.",
                  "success")
        except mysql.connector.Error as err:
            flash(f"Could not delete: {err}", "error")
    cur.close()
    conn.close()
    return redirect(url_for("components"))


# ====================================================================
# MANAGE PRICES — bulk price editor
# ====================================================================

@app.route("/prices", methods=["GET", "POST"])
@admin_required
def prices():
    if request.method == "POST":
        updated_count = 0
        conn = get_db()
        cur = conn.cursor()
        try:
            for key, value in request.form.items():
                if not key.startswith("price_"):
                    continue
                try:
                    cid = int(key.split("_")[1])
                    new_price = float(value)
                    if new_price < 0:
                        continue
                except (ValueError, IndexError):
                    continue
                cur.execute("SELECT price FROM Component WHERE component_id = %s", (cid,))
                row = cur.fetchone()
                if row and abs(float(row[0]) - new_price) > 0.001:
                    cur.execute("UPDATE Component SET price = %s WHERE component_id = %s",
                                (new_price, cid))
                    updated_count += 1
            conn.commit()
            flash(f"{updated_count} price(s) updated.", "success")
        except mysql.connector.Error as err:
            flash(f"Database error: {err}", "error")
        finally:
            cur.close()
            conn.close()
        return redirect(url_for("prices", type=request.args.get("type", "")))

    type_filter = request.args.get("type", "").strip()
    sql = """SELECT component_id, component_name, component_type, brand, price
             FROM Component WHERE is_active = 1"""
    params = []
    if type_filter:
        sql += " AND component_type = %s"
        params.append(type_filter)
    sql += " ORDER BY component_type, brand, component_name"

    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute(sql, params)
    rows = cur.fetchall()
    for r in rows:
        r["price"] = float(r["price"])
    cur.close()
    conn.close()

    return render_template(
        "admin/components/prices.html",
        components=rows, type_filter=type_filter,
        component_types=COMPONENT_TYPES, active_section="prices",
    )


# ====================================================================
# VIEW USERS — user management
# ====================================================================

@app.route("/users")
@admin_required
def users():
    q          = request.args.get("q", "").strip()
    role_filter = request.args.get("role", "").strip()

    sql = """
        SELECT u.user_id, u.full_name, u.email, u.role,
               (SELECT COUNT(*) FROM Build_Request br
                WHERE br.user_id = u.user_id) AS request_count,
               (SELECT MAX(br.request_date) FROM Build_Request br
                WHERE br.user_id = u.user_id) AS last_activity
        FROM User u WHERE 1=1
    """
    params = []
    if q:
        sql += " AND (u.full_name LIKE %s OR u.email LIKE %s)"
        params.extend([f"%{q}%", f"%{q}%"])
    if role_filter in ("user", "admin"):
        sql += " AND u.role = %s"
        params.append(role_filter)
    sql += " ORDER BY u.user_id DESC"

    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute(sql, params)
    user_rows = cur.fetchall()
    cur.close()
    conn.close()

    return render_template(
        "admin/users/list.html",
        users=user_rows, q=q, role_filter=role_filter,
        current_admin_id=session.get("admin_id"),
        active_section="users",
    )


@app.route("/users/<int:uid>/promote", methods=["POST"])
@admin_required
def user_promote(uid):
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT full_name, role FROM User WHERE user_id = %s", (uid,))
    u = cur.fetchone()
    if not u:
        flash("User not found.", "error")
    else:
        new_role = "user" if u["role"] == "admin" else "admin"
        if u["role"] == "admin" and uid == session.get("admin_id"):
            flash("You cannot demote yourself.", "error")
        else:
            cur.execute("UPDATE User SET role = %s WHERE user_id = %s",
                        (new_role, uid))
            conn.commit()
            verb = "promoted to admin" if new_role == "admin" else "demoted to user"
            flash(f"{u['full_name']} {verb}.", "success")
    cur.close()
    conn.close()
    return redirect(url_for("users"))


@app.route("/users/<int:uid>/delete", methods=["POST"])
@admin_required
def user_delete(uid):
    if uid == session.get("admin_id"):
        flash("You cannot delete your own account.", "error")
        return redirect(url_for("users"))
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT full_name, email FROM User WHERE user_id = %s", (uid,))
    u = cur.fetchone()
    if not u:
        flash("User not found.", "error")
    else:
        try:
            cur.execute("DELETE FROM User WHERE user_id = %s", (uid,))
            conn.commit()
            flash(
                f"{u['full_name']} ({u['email']}) and all their build "
                f"requests have been deleted.", "success")
        except mysql.connector.Error as err:
            flash(f"Could not delete user: {err}", "error")
    cur.close()
    conn.close()
    return redirect(url_for("users"))


# ====================================================================
# RECOMMENDATION LOGS — full build history with filters
# ====================================================================

@app.route("/logs")
@admin_required
def logs():
    """List every build request + its generated builds, with filters."""
    # Filters
    q          = request.args.get("q", "").strip()
    purpose    = request.args.get("purpose", "").strip()
    preference = request.args.get("preference", "").strip()
    date_from  = request.args.get("from", "").strip()
    date_to    = request.args.get("to", "").strip()

    # Pagination
    try:
        page = max(1, int(request.args.get("page", 1)))
    except ValueError:
        page = 1
    per_page = 25
    offset = (page - 1) * per_page

    cols = get_request_columns()
    has_currency   = "currency" in cols
    has_preference = "build_preference" in cols

    # Build SELECT — gracefully handle missing optional columns
    select_extra = ""
    if has_currency:
        select_extra += ", br.currency"
    else:
        select_extra += ", 'USD' AS currency"
    if has_preference:
        select_extra += ", br.build_preference"
    else:
        select_extra += ", 'Balanced' AS build_preference"

    sql = f"""
        SELECT br.request_id, br.budget, br.purpose, br.request_date,
               br.user_id, u.full_name, u.email
               {select_extra},
               (SELECT COUNT(*) FROM Recommended_Build rb
                WHERE rb.request_id = br.request_id) AS build_count,
               (SELECT COALESCE(SUM(rb.total_cost), 0) FROM Recommended_Build rb
                WHERE rb.request_id = br.request_id) AS total_value
        FROM Build_Request br
        JOIN User u ON u.user_id = br.user_id
        WHERE 1=1
    """
    params = []

    if q:
        sql += " AND (u.full_name LIKE %s OR u.email LIKE %s)"
        params.extend([f"%{q}%", f"%{q}%"])
    if purpose:
        sql += " AND br.purpose = %s"
        params.append(purpose)
    if preference and has_preference:
        sql += " AND br.build_preference = %s"
        params.append(preference)
    if date_from:
        sql += " AND br.request_date >= %s"
        params.append(date_from)
    if date_to:
        sql += " AND br.request_date <= %s"
        params.append(date_to)

    # Count for pagination
    count_sql = "SELECT COUNT(*) AS c FROM (" + sql + ") AS t"

    sql += " ORDER BY br.request_date DESC, br.request_id DESC LIMIT %s OFFSET %s"
    params.extend([per_page, offset])

    conn = get_db()
    cur = conn.cursor(dictionary=True)

    # Get total count
    count_params = params[:-2]  # without LIMIT/OFFSET
    cur.execute(count_sql, count_params)
    total_count = cur.fetchone()["c"]
    total_pages = max(1, (total_count + per_page - 1) // per_page)

    cur.execute(sql, params)
    rows = cur.fetchall()
    for r in rows:
        r["budget"]      = float(r["budget"])
        r["total_value"] = float(r["total_value"])

    # Distinct purposes / preferences for dropdowns
    cur.execute("SELECT DISTINCT purpose FROM Build_Request ORDER BY purpose")
    distinct_purposes = [r["purpose"] for r in cur.fetchall()]
    if has_preference:
        cur.execute("SELECT DISTINCT build_preference FROM Build_Request "
                    "WHERE build_preference IS NOT NULL ORDER BY build_preference")
        distinct_preferences = [r["build_preference"] for r in cur.fetchall()]
    else:
        distinct_preferences = []

    cur.close()
    conn.close()

    return render_template(
        "admin/logs/list.html",
        logs=rows,
        q=q, purpose=purpose, preference=preference,
        date_from=date_from, date_to=date_to,
        page=page, total_pages=total_pages, total_count=total_count,
        distinct_purposes=distinct_purposes,
        distinct_preferences=distinct_preferences,
        usd_to_pkr=USD_TO_PKR,
        active_section="logs",
    )


@app.route("/logs/<int:request_id>")
@admin_required
def log_detail(request_id):
    """Show full detail of a single build request: all parts in each build."""
    cols = get_request_columns()
    has_currency   = "currency" in cols
    has_preference = "build_preference" in cols

    select_extra = ""
    if has_currency:
        select_extra += ", br.currency"
    else:
        select_extra += ", 'USD' AS currency"
    if has_preference:
        select_extra += ", br.build_preference"
    else:
        select_extra += ", 'Balanced' AS build_preference"

    conn = get_db()
    cur = conn.cursor(dictionary=True)

    cur.execute(f"""
        SELECT br.request_id, br.budget, br.purpose, br.request_date,
               u.user_id, u.full_name, u.email
               {select_extra}
        FROM Build_Request br
        JOIN User u ON u.user_id = br.user_id
        WHERE br.request_id = %s
    """, (request_id,))
    req = cur.fetchone()

    if not req:
        flash("Request not found.", "error")
        cur.close()
        conn.close()
        return redirect(url_for("logs"))

    req["budget"] = float(req["budget"])

    # All builds for this request, with their parts
    cur.execute("""
        SELECT build_id, total_cost, recommendation_date
        FROM Recommended_Build
        WHERE request_id = %s
        ORDER BY build_id
    """, (request_id,))
    builds = cur.fetchall()

    for b in builds:
        b["total_cost"] = float(b["total_cost"])
        cur.execute("""
            SELECT c.component_name, c.component_type, c.brand,
                   c.price, c.specifications, bc.quantity
            FROM Build_Component bc
            JOIN Component c ON bc.component_id = c.component_id
            WHERE bc.build_id = %s
            ORDER BY FIELD(c.component_type,
                'CPU','GPU','Motherboard','RAM','Storage','PSU','Case','Cooler')
        """, (b["build_id"],))
        b["parts"] = cur.fetchall()
        for p in b["parts"]:
            p["price"] = float(p["price"])

    cur.close()
    conn.close()

    return render_template(
        "admin/logs/detail.html",
        req=req, builds=builds,
        usd_to_pkr=USD_TO_PKR,
        active_section="logs",
    )


# ====================================================================
# ANALYTICS — system-wide statistics & charts
# ====================================================================

@app.route("/analytics")
@admin_required
def analytics():
    """Aggregate analytics: usage trends, popular components, budget distribution."""
    cols = get_request_columns()
    has_preference = "build_preference" in cols

    conn = get_db()
    cur = conn.cursor(dictionary=True)

    # ---- Headline numbers ----
    cur.execute("SELECT COUNT(*) AS c FROM Build_Request")
    total_requests = cur.fetchone()["c"]

    cur.execute("SELECT COUNT(*) AS c FROM Recommended_Build")
    total_builds = cur.fetchone()["c"]

    cur.execute("""
        SELECT COALESCE(AVG(total_cost), 0) AS avg_cost,
               COALESCE(MIN(total_cost), 0) AS min_cost,
               COALESCE(MAX(total_cost), 0) AS max_cost,
               COALESCE(SUM(total_cost), 0) AS sum_cost
        FROM Recommended_Build
    """)
    cost_stats = cur.fetchone()
    for k in cost_stats:
        cost_stats[k] = float(cost_stats[k])

    avg_builds_per_request = (total_builds / total_requests) if total_requests else 0.0

    # ---- Requests by purpose ----
    cur.execute("""
        SELECT purpose, COUNT(*) AS cnt,
               COALESCE(AVG(budget), 0) AS avg_budget
        FROM Build_Request
        GROUP BY purpose
        ORDER BY cnt DESC
    """)
    by_purpose = cur.fetchall()
    for r in by_purpose:
        r["avg_budget"] = float(r["avg_budget"])

    # ---- Requests by build_preference (if column exists) ----
    by_preference = []
    if has_preference:
        cur.execute("""
            SELECT build_preference AS pref, COUNT(*) AS cnt
            FROM Build_Request
            WHERE build_preference IS NOT NULL
            GROUP BY build_preference
            ORDER BY cnt DESC
        """)
        by_preference = cur.fetchall()

    # ---- Requests over time (last 12 months) ----
    cur.execute("""
        SELECT DATE_FORMAT(request_date, '%Y-%m') AS ym, COUNT(*) AS cnt
        FROM Build_Request
        WHERE request_date >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
        GROUP BY ym
        ORDER BY ym
    """)
    monthly_raw = cur.fetchall()
    monthly_map = {r["ym"]: r["cnt"] for r in monthly_raw}

    # Fill in missing months
    months_series = []
    today = date.today()
    for i in range(11, -1, -1):
        y = today.year
        m = today.month - i
        while m <= 0:
            m += 12
            y -= 1
        ym = f"{y:04d}-{m:02d}"
        months_series.append({"ym": ym, "cnt": int(monthly_map.get(ym, 0))})

    # ---- Top recommended components ----
    cur.execute("""
        SELECT c.component_id, c.component_name, c.component_type, c.brand,
               c.price, COUNT(bc.build_component_id) AS times_used
        FROM Build_Component bc
        JOIN Component c ON c.component_id = bc.component_id
        GROUP BY c.component_id
        ORDER BY times_used DESC
        LIMIT 10
    """)
    top_components = cur.fetchall()
    for r in top_components:
        r["price"] = float(r["price"])

    # ---- Top by category (most-picked in each type) ----
    cur.execute("""
        SELECT t.component_type, t.component_name, t.brand, t.cnt
        FROM (
            SELECT c.component_type, c.component_name, c.brand,
                   COUNT(bc.build_component_id) AS cnt,
                   ROW_NUMBER() OVER (PARTITION BY c.component_type
                                      ORDER BY COUNT(bc.build_component_id) DESC) AS rn
            FROM Build_Component bc
            JOIN Component c ON c.component_id = bc.component_id
            GROUP BY c.component_id
        ) AS t
        WHERE t.rn = 1
        ORDER BY t.cnt DESC
    """)
    top_by_category = cur.fetchall()

    # ---- Top brands (by appearances in builds) ----
    cur.execute("""
        SELECT c.brand, COUNT(bc.build_component_id) AS cnt
        FROM Build_Component bc
        JOIN Component c ON c.component_id = bc.component_id
        GROUP BY c.brand
        ORDER BY cnt DESC
        LIMIT 8
    """)
    by_brand = cur.fetchall()

    # ---- Budget distribution buckets ----
    cur.execute("""
        SELECT
          SUM(CASE WHEN budget <  500              THEN 1 ELSE 0 END) AS b1,
          SUM(CASE WHEN budget >= 500  AND budget < 1000  THEN 1 ELSE 0 END) AS b2,
          SUM(CASE WHEN budget >= 1000 AND budget < 2000  THEN 1 ELSE 0 END) AS b3,
          SUM(CASE WHEN budget >= 2000 AND budget < 3500  THEN 1 ELSE 0 END) AS b4,
          SUM(CASE WHEN budget >= 3500 AND budget < 6000  THEN 1 ELSE 0 END) AS b5,
          SUM(CASE WHEN budget >= 6000                     THEN 1 ELSE 0 END) AS b6
        FROM Build_Request
    """)
    bucket_row = cur.fetchone() or {}
    budget_buckets = [
        {"label": "< $500",     "count": int(bucket_row.get("b1") or 0)},
        {"label": "$500–1k",    "count": int(bucket_row.get("b2") or 0)},
        {"label": "$1k–2k",     "count": int(bucket_row.get("b3") or 0)},
        {"label": "$2k–3.5k",   "count": int(bucket_row.get("b4") or 0)},
        {"label": "$3.5k–6k",   "count": int(bucket_row.get("b5") or 0)},
        {"label": "$6k+",       "count": int(bucket_row.get("b6") or 0)},
    ]

    # ---- Most active users ----
    cur.execute("""
        SELECT u.user_id, u.full_name, u.email, COUNT(br.request_id) AS cnt
        FROM Build_Request br
        JOIN User u ON u.user_id = br.user_id
        GROUP BY u.user_id
        ORDER BY cnt DESC
        LIMIT 10
    """)
    top_users = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "admin/analytics/index.html",
        total_requests=total_requests, total_builds=total_builds,
        cost_stats=cost_stats,
        avg_builds_per_request=avg_builds_per_request,
        by_purpose=by_purpose, by_preference=by_preference,
        months_series=months_series,
        top_components=top_components, top_by_category=top_by_category,
        by_brand=by_brand, budget_buckets=budget_buckets,
        top_users=top_users,
        usd_to_pkr=USD_TO_PKR,
        has_preference=has_preference,
        active_section="analytics",
    )


# ====================================================================
# SETTINGS — admin account, system info, danger zone
# ====================================================================

@app.route("/settings", methods=["GET", "POST"])
@admin_required
def settings():
    """Admin password change, profile, and read-only system info."""
    conn = get_db()
    cur = conn.cursor(dictionary=True)

    # Handle POST: password change
    if request.method == "POST":
        action = request.form.get("action", "")

        if action == "change_password":
            current_pw = request.form.get("current_password", "")
            new_pw     = request.form.get("new_password", "")
            confirm_pw = request.form.get("confirm_password", "")

            if not current_pw or not new_pw or not confirm_pw:
                flash("All password fields are required.", "error")
            elif new_pw != confirm_pw:
                flash("New password and confirmation do not match.", "error")
            elif len(new_pw) < 6:
                flash("Password must be at least 6 characters.", "error")
            else:
                # Verify current password
                admin_id = session.get("admin_id")
                cur.execute("SELECT password, email FROM User WHERE user_id = %s",
                            (admin_id,))
                row = cur.fetchone()
                if not row:
                    flash("Admin account not found in database.", "error")
                else:
                    stored = (row["password"] or "").encode("utf-8")
                    # Allow either the bcrypt hash OR the built-in plaintext
                    # ADMIN_PASSWORD as the "current" password.
                    valid = False
                    if stored.startswith(b"$2") and bcrypt.checkpw(
                        current_pw.encode("utf-8"), stored
                    ):
                        valid = True
                    elif (row["email"] == ADMIN_EMAIL.lower()
                          and current_pw == ADMIN_PASSWORD):
                        valid = True

                    if not valid:
                        flash("Current password is incorrect.", "error")
                    else:
                        new_hash = bcrypt.hashpw(new_pw.encode("utf-8"),
                                                 bcrypt.gensalt()).decode("utf-8")
                        cur.execute(
                            "UPDATE User SET password = %s WHERE user_id = %s",
                            (new_hash, admin_id))
                        conn.commit()
                        flash("Password updated successfully.", "success")

        elif action == "update_profile":
            new_name = request.form.get("full_name", "").strip()
            if not new_name:
                flash("Name cannot be empty.", "error")
            else:
                admin_id = session.get("admin_id")
                cur.execute("UPDATE User SET full_name = %s WHERE user_id = %s",
                            (new_name, admin_id))
                conn.commit()
                session["admin_name"] = new_name
                flash("Profile updated.", "success")

        cur.close()
        conn.close()
        return redirect(url_for("settings"))

    # GET: gather info to display
    admin_id = session.get("admin_id")
    cur.execute("SELECT user_id, full_name, email, role FROM User WHERE user_id = %s",
                (admin_id,))
    admin_row = cur.fetchone() or {
        "user_id": 0, "full_name": session.get("admin_name", ADMIN_NAME),
        "email": session.get("admin_email", ADMIN_EMAIL), "role": "admin"
    }

    # ---- System info ----
    cur.execute("SELECT VERSION() AS v")
    mysql_version = cur.fetchone()["v"]

    db_name = app.config.get("MYSQL_DB", "?")
    db_host = app.config.get("MYSQL_HOST", "?")
    db_port = app.config.get("MYSQL_PORT", "?")

    cur.execute("""
        SELECT COUNT(*) AS c FROM information_schema.tables
        WHERE table_schema = %s
    """, (db_name,))
    table_count = cur.fetchone()["c"]

    cur.execute("SELECT COUNT(*) AS c FROM Component")
    total_components_all = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) AS c FROM Component WHERE is_active = 1")
    active_components = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) AS c FROM User")
    total_users_all = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) AS c FROM Build_Request")
    total_requests = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) AS c FROM Recommended_Build")
    total_builds = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) AS c FROM Build_Component")
    total_build_components = cur.fetchone()["c"]

    cur.close()
    conn.close()

    system_info = {
        "mysql_version": mysql_version,
        "db_name": db_name,
        "db_host": db_host,
        "db_port": db_port,
        "table_count": table_count,
        "total_components_all": total_components_all,
        "active_components": active_components,
        "total_users_all": total_users_all,
        "total_requests": total_requests,
        "total_builds": total_builds,
        "total_build_components": total_build_components,
        "usd_to_pkr": USD_TO_PKR,
        "builtin_admin_email": ADMIN_EMAIL,
    }

    return render_template(
        "admin/settings/index.html",
        admin=admin_row,
        system_info=system_info,
        active_section="settings",
    )


# ====================================================================
# START
# ====================================================================

if __name__ == "__main__":
    ensure_builtin_admin()
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=Config.DEBUG)
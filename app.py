# app.py — Streamlined PC Build Recommendation System

import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
from datetime import date
import mysql.connector
import bcrypt
from config import Config
from recommender import generate_recommendations

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY

# ---------- Database Helper ----------
def get_db():
    return mysql.connector.connect(
        host=app.config["MYSQL_HOST"],
        user=app.config["MYSQL_USER"],
        password=app.config["MYSQL_PASSWORD"],
        database=app.config["MYSQL_DB"],
        port=app.config["MYSQL_PORT"],
    )

# ---------- Decorators ----------
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in first.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

# ---------- Constants ----------
# Conversion rate: 1 USD = 280 PKR (approximate)
USD_TO_PKR = 280.0

# ==========================================================================
# CORE ROUTES
# ==========================================================================

@app.route("/")
def home():
    # If the user is already logged in, send them to the dashboard
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    # Otherwise, prompt them to log in
    return redirect(url_for("login"))

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        full_name = request.form["full_name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        try:
            conn = get_db()
            cur = conn.cursor()
            # Hardcoding the role to "user" since we removed the admin setup
            cur.execute(
                "INSERT INTO User (full_name, email, password, role) VALUES (%s, %s, %s, %s)",
                (full_name, email, hashed.decode("utf-8"), "user"),
            )
            conn.commit()
            cur.close()
            conn.close()
            flash("Account created! Please log in.", "success")
            return redirect(url_for("login"))
        except mysql.connector.IntegrityError:
            flash("That email is already registered.", "error")
        except mysql.connector.Error as err:
            flash(f"Database error: {err}", "error")

    # Assuming you have a signup.html template!
    return render_template("signup.html") 

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        conn = get_db()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM User WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user:
            stored = user["password"].encode("utf-8")
            if stored.startswith(b"$2") and bcrypt.checkpw(password.encode("utf-8"), stored):
                session["user_id"]   = user["user_id"]
                session["full_name"] = user["full_name"]
                session["role"]      = user["role"]
                flash(f"Welcome back, {user['full_name']}!", "success")
                return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "error")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))

@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_db()
    cur = conn.cursor(dictionary=True)

    user_id = session["user_id"]

    # 1. User's Total Requests
    cur.execute("SELECT COUNT(*) AS total_requests FROM Build_Request WHERE user_id = %s", (user_id,))
    total_requests = cur.fetchone()["total_requests"]

    # 2. User's Total Generated Builds
    # We join Build_Request to Recommended_Build to only count builds belonging to this user
    cur.execute("""
        SELECT COUNT(rb.build_id) AS total_builds 
        FROM Recommended_Build rb
        JOIN Build_Request br ON rb.request_id = br.request_id
        WHERE br.user_id = %s
    """, (user_id,))
    total_builds = cur.fetchone()["total_builds"]

    # 3. User's Most Requested Purpose
    cur.execute("""
        SELECT purpose 
        FROM Build_Request 
        WHERE user_id = %s 
        GROUP BY purpose 
        ORDER BY COUNT(*) DESC 
        LIMIT 1
    """, (user_id,))
    top_purpose_row = cur.fetchone()
    top_purpose = top_purpose_row["purpose"] if top_purpose_row else "None Yet"

    cur.close()
    conn.close()

    # Package the personal stats to pass to the template
    stats = {
        "total_requests": total_requests,
        "total_builds": total_builds,
        "top_purpose": top_purpose
    }

    return render_template("dashboard.html", stats=stats)
# ==========================================================================
# BUILD REQUEST & RESULTS LOGIC
# ==========================================================================

# Drop-in replacement for the build_request route in app.py.
# Replace the existing @app.route("/build/request", ...) function with this one.

@app.route("/build/request", methods=["GET", "POST"])
@login_required
def build_request():
    if request.method == "POST":
        try:
            budget_input = float(request.form["budget"])
            currency = request.form.get("currency", "USD").strip().upper()
            purpose = request.form["purpose"].strip()
            build_preference = request.form.get("build_preference", "Balanced").strip()

            if budget_input <= 0:
                flash("Budget must be greater than 0.", "error")
                return redirect(url_for("build_request"))

            if currency == "PKR":
                budget_usd = budget_input / USD_TO_PKR
            else:
                budget_usd = budget_input

            min_budget_usd = 1500 if purpose == "AI & Model Training" else 200
            if budget_usd < min_budget_usd:
                if currency == "PKR":
                    flash(f"Budget is too low. Minimum is ~{int(min_budget_usd * USD_TO_PKR):,} PKR.", "error")
                else:
                    flash(f"Budget is too low. Minimum is ${min_budget_usd} USD.", "error")
                return redirect(url_for("build_request"))

            conn = get_db()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO Build_Request
                    (budget, currency, purpose, build_preference, request_date, user_id)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (round(budget_usd, 2), currency, purpose, build_preference,
                  date.today(), session["user_id"]))
            request_id = cur.lastrowid
            conn.commit()
            cur.close()

            # ----- KEY CHANGE: print the actual error so we can see it -----
            try:
                build_ids = generate_recommendations(
                    conn, request_id, budget_usd, purpose, build_preference
                )
            except Exception as e:
                import traceback
                print("=" * 60)
                print("RECOMMENDATION ENGINE CRASHED")
                print("=" * 60)
                traceback.print_exc()
                print("=" * 60)
                conn.close()
                flash(f"Recommendation engine error: {type(e).__name__}: {e}", "error")
                return redirect(url_for("build_request"))

            conn.close()

            if not build_ids:
                flash("Could not generate a build with that budget. Try increasing it.", "error")
                return redirect(url_for("build_request"))

            flash(f"Generated {len(build_ids)} build recommendation(s)!", "success")
            return redirect(url_for("build_result", request_id=request_id))

        except ValueError:
            flash("Please enter a valid number for budget.", "error")
            return redirect(url_for("build_request"))
        except mysql.connector.Error as err:
            flash(f"Database error: {err}", "error")
            return redirect(url_for("build_request"))

    return render_template("build_request.html")


@app.route("/build/result/<int:request_id>")
@login_required
def build_result(request_id):
    conn = get_db()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT request_id, budget, currency, purpose,
               build_preference, request_date
        FROM Build_Request
        WHERE request_id = %s AND user_id = %s
    """, (request_id, session["user_id"]))
    req = cur.fetchone()

    if not req:
        cur.close()
        conn.close()
        flash("Build request not found.", "error")
        return redirect(url_for("dashboard"))

    req["budget"] = float(req["budget"])

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
                   c.price, c.specifications, c.image_url, bc.quantity
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

    return render_template("build_result.html",
                           req=req, builds=builds,
                           usd_to_pkr=USD_TO_PKR)

# ==========================================================================
# HISTORY LOGIC
# ==========================================================================

@app.route("/history")
@login_required
def history():
    conn = get_db()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT request_id, budget, currency, purpose,
               build_preference, request_date
        FROM Build_Request
        WHERE user_id = %s
        ORDER BY request_date DESC, request_id DESC
    """, (session["user_id"],))
    requests = cur.fetchall()

    for r in requests:
        r["budget"] = float(r["budget"])

        cur.execute("""
            SELECT build_id, total_cost, recommendation_date
            FROM Recommended_Build
            WHERE request_id = %s
            ORDER BY build_id
        """, (r["request_id"],))
        r["builds"] = cur.fetchall()

        for b in r["builds"]:
            b["total_cost"] = float(b["total_cost"])

            cur.execute("""
                SELECT c.component_name, c.component_type, c.brand,
                       c.price, c.image_url, bc.quantity
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

    return render_template("history.html",
                           requests=requests,
                           usd_to_pkr=USD_TO_PKR)


# ==========================================================================
# ADMIN STUB
# ==========================================================================
# I am leaving this simple route here because your `base.html` template
# still has a line checking `{% if session.get('role') == 'admin' %}` and linking 
# to `admin_components`. If we remove the route entirely, Jinja will crash.

@app.route("/admin/components")
@login_required
def admin_components():
    flash("The admin panel has been disabled to keep things simple.", "info")
    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    # Use the PORT env var that Railway injects at runtime;
    # fall back to 5000 when running locally.
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=Config.DEBUG)
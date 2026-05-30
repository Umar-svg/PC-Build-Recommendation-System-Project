# PC Build Recommendation System

A full-stack web application that recommends custom PC builds based on user budget, intended purpose, and preference. Users get two distinct build options (e.g. NVIDIA vs AMD GPU, or with/without extra storage) per request, with a separate admin panel for managing components, users, and analytics.

Built as a Database Lab project — deployed live on Railway with MySQL.

---

## Features

### For Users
- **Sign up / log in** with bcrypt-hashed passwords
- **Request builds** by specifying budget, purpose, and build preference
- **Multi-currency support** — enter budget in USD or PKR
- **Two distinct recommendations** per request:
  - Build #1 — engine's default pick (typically NVIDIA + SSD only)
  - Build #2 — deliberately different (AMD GPU and/or SSD + HDD)
- **Eight purpose presets** — Gaming, Streaming, Gaming + Streaming, Video Editing, 3D Rendering, Programming, AI & Model Training, General Use
- **Three build preferences** — Maximum Performance, Balanced, Budget Saver
- **Build history** with full part breakdown for every past request

### For Admins (separate panel)
- **Dashboard** — system-wide stats and recent activity
- **Component management** — full CRUD on the parts catalog
- **Bulk price editor** — update component prices in one place
- **User management** — promote/demote/delete users
- **Recommendation logs** — every build request with filters and detail views
- **Analytics** — top components, popular purposes, budget distribution, brand trends
- **Settings** — change admin password, view system info

---

## Recommendation Engine Highlights

The engine isn't just a price-based filter — it applies real PC-building knowledge:

- **Tier-based scoring** — each CPU/GPU has a score per purpose (an RTX 4090 scores high for Gaming, low for General Use)
- **CPU/GPU balance rules** — prevents pairings like *Ryzen 9 + GTX 1650*; the GPU/CPU price ratio must fall in a purpose-appropriate range
- **Socket compatibility** — AM5 CPU → AM5 motherboard; matches DDR4/DDR5 across CPU/MB/RAM
- **Brand preferences** — CUDA-dependent purposes (Video Editing, AI & Model Training, 3D Rendering) require NVIDIA; AI builds prefer Intel CPUs
- **Workstation parts filtered out** for consumer purposes — no Threadripper or RTX A6000 in a gaming build
- **Newer-chipset preference** — picks X870E over X670E for AM5, even if the older board is pricier
- **Multi-pass upgrade sweeper** (Maximum Performance mode) — iteratively upgrades parts within budget while respecting balance rules
- **Trade-swap pass** — downgrades minor parts to fund major upgrades (e.g. cheaper case to afford a better GPU)
- **Splurge passes at high budget** — once core parts are maxed, soak remaining budget into RAM, cooling, premium PSU, secondary storage

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, Flask 3.0 |
| Database | MySQL 8 |
| Auth | bcrypt (password hashing), Flask sessions |
| Frontend | Jinja2 templates, custom CSS, Bootstrap 5 (admin) |
| Production server | Gunicorn |
| Hosting | Railway (Flask services + managed MySQL) |
| Version control | Git + GitHub |

---

## Project Structure

```
pc_build_system/
├── app.py                    # User-facing Flask app
├── admin_app.py              # Admin-facing Flask app (separate service)
├── recommender.py            # Build recommendation engine
├── config.py                 # Reads DB credentials from env vars
├── auth.py                   # login_required / admin_required decorators
├── schema.sql                # Database schema (DDL)
├── load_csv.py               # Loads CSV seed data into MySQL
├── setup_railway_db.py       # One-shot script to set up Railway's DB
├── create_admin.py           # One-shot script to seed the built-in admin
├── requirements.txt          # Python dependencies
├── Procfile                  # Tells Railway how to start the user app
├── runtime.txt               # Pins Python version (3.12.7)
├── mise.toml                 # Skips Python attestation check on Railway
├── csv_data/                 # CSV seed data (5 files, not committed)
├── static/                   # CSS, images
└── templates/
    ├── base.html             # User app shell
    ├── login.html, signup.html, dashboard.html, ...
    └── admin/                # Admin panel templates
        ├── base.html, login.html, dashboard.html, ...
        ├── components/       # List, form, prices
        ├── users/            # List
        ├── logs/             # List, detail
        ├── analytics/        # Index
        └── settings/         # Index
```

---

## Database Schema

Five normalized tables:

```
User                  Build_Request              Recommended_Build
├ user_id (PK)        ├ request_id (PK)          ├ build_id (PK)
├ full_name           ├ budget                   ├ total_cost
├ email (UQ)          ├ currency                 ├ recommendation_date
├ password (bcrypt)   ├ purpose                  └ request_id (FK)
└ role                ├ build_preference
                      ├ request_date
                      └ user_id (FK)

Component                                Build_Component (junction)
├ component_id (PK)                      ├ build_component_id (PK)
├ component_name                         ├ quantity
├ component_type (CPU/GPU/...)           ├ build_id (FK)
├ brand                                  └ component_id (FK)
├ price
├ specifications
├ compatibility_info
├ image_url
└ is_active
```

Foreign keys cascade on delete (deleting a user removes their requests; deleting a request removes its builds), with `Build_Component → Component` set to RESTRICT so components used in builds can't be hard-deleted.

---

## Local Setup

### Requirements
- Python 3.12
- MySQL 8 running locally

### Install

```bash
git clone https://github.com/Umar-svg/PC-Build-Recommendation-System-Project.git
cd PC-Build-Recommendation-System-Project
pip install -r requirements.txt
```

### Configure
Edit the defaults in `config.py` to match your local MySQL setup, or set environment variables: `MYSQLHOST`, `MYSQLUSER`, `MYSQLPASSWORD`, `MYSQLDATABASE`, `MYSQLPORT`.

### Initialize the database

```bash
mysql -u root -p < schema.sql
python load_csv.py
```

### Run

```bash
# User app (http://localhost:5000)
python app.py

# Admin panel (http://localhost:5001) — separate terminal
python admin_app.py
```

### Default admin credentials
```
Email:    umar@gmail.com
Password: admin123
```
Change these in `admin_app.py` (or via env vars `ADMIN_EMAIL` / `ADMIN_PASSWORD`) before deploying anywhere public.

---

## Deployment (Railway)

The app is built to deploy cleanly on Railway:

1. **Two web services** from the same GitHub repo:
   - User app — uses the default `Procfile`
   - Admin app — uses a Custom Start Command:
     ```
     gunicorn admin_app:app --bind 0.0.0.0:8081 --workers 2 --timeout 60
     ```
2. **One MySQL plugin** in the same project — both services reference its variables (`MYSQLHOST`, `MYSQLPORT`, `MYSQLUSER`, `MYSQLPASSWORD`, `MYSQLDATABASE`)
3. **Use `mysql.railway.internal` as `MYSQLHOST`** for service-to-service connections within Railway; use the public proxy host only when connecting from outside (e.g. for `setup_railway_db.py`)
4. **Generate public domains** in each service's Networking section, pointing to the correct internal port

To initialize Railway's empty MySQL after first deploy:
```bash
# Edit setup_railway_db.py with your MYSQL_PUBLIC_URL credentials
python setup_railway_db.py
python create_admin.py
```

---

## Screenshots

_Add your screenshots here:_

- `screenshots/dashboard.png` — user dashboard
- `screenshots/build_request.png` — build request form
- `screenshots/build_result.png` — recommended builds with parts table
- `screenshots/admin_dashboard.png` — admin overview
- `screenshots/admin_analytics.png` — analytics charts

---

## Future Improvements

- Live pricing via PCPartPicker / retailer APIs instead of static CSV
- Wishlist / save-for-later for users
- Email notifications on price drops
- More granular component compatibility (RAM speed limits, PSU wattage check against GPU TDP)
- Switch to PostgreSQL for better full-text search on components
- Caching of the component catalog with Redis
- API endpoints (JSON) for a future mobile client

---

## Author

**Umar** — Database Lab Project, 2026
GitHub: [@Umar-svg](https://github.com/Umar-svg)

---

## License

This project is for educational/academic purposes.

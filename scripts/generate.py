"""
Milestone 3 — Synthetic Data Generator
PC Build Recommendation System
Generates 5 CSV files (User, Build_Request, Component, Recommended_Build, Build_Component)
with realistic, internally consistent data respecting all FK relationships.
"""

import csv
import os
import random
from datetime import date, timedelta
from faker import Faker

fake = Faker()
Faker.seed(42)
random.seed(42)

OUT = "/home/claude/m3_data"
os.makedirs(OUT, exist_ok=True)

# ----------------------------------------------------------------------
# 1) USER  — 60 rows (5 admins + 55 regular users)
# ----------------------------------------------------------------------
users = []
admins = 5
total_users = 60
used_emails = set()

for i in range(1, total_users + 1):
    full_name = fake.name()
    # build a deterministic-ish email from name
    base = full_name.lower().replace(" ", ".").replace("'", "").replace(",", "")
    email = f"{base}@example.com"
    n = 1
    while email in used_emails:
        n += 1
        email = f"{base}{n}@example.com"
    used_emails.add(email)
    role = "admin" if i <= admins else "user"
    # passwords stored as fake bcrypt-ish hash strings (NOT real hashes — synthetic placeholder)
    password = "$2b$12$" + fake.lexify(text="?" * 53, letters="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789./")
    users.append({
        "user_id": i,
        "full_name": full_name,
        "email": email,
        "password": password,
        "role": role,
    })

with open(f"{OUT}/User.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["user_id", "full_name", "email", "password", "role"])
    w.writeheader()
    w.writerows(users)

# ----------------------------------------------------------------------
# 2) COMPONENT — ~80 rows of realistic PC parts
# ----------------------------------------------------------------------
# Each entry: (type, name, brand, price_range, sample_spec, sample_compat)
component_catalog = [
    # CPUs
    ("CPU", "Ryzen 5 5600",          "AMD",    120, 160, "6 cores / 12 threads, 3.5–4.4 GHz, AM4", "Socket AM4; DDR4 supported"),
    ("CPU", "Ryzen 5 7600",          "AMD",    200, 240, "6 cores / 12 threads, 3.8–5.1 GHz, AM5", "Socket AM5; DDR5 only"),
    ("CPU", "Ryzen 7 5800X",         "AMD",    230, 280, "8 cores / 16 threads, 3.8–4.7 GHz, AM4", "Socket AM4; DDR4 supported"),
    ("CPU", "Ryzen 7 7700X",         "AMD",    300, 360, "8 cores / 16 threads, 4.5–5.4 GHz, AM5", "Socket AM5; DDR5 only"),
    ("CPU", "Ryzen 9 7900X",         "AMD",    420, 500, "12 cores / 24 threads, 4.7–5.6 GHz, AM5", "Socket AM5; DDR5 only"),
    ("CPU", "Ryzen 9 7950X",         "AMD",    560, 650, "16 cores / 32 threads, 4.5–5.7 GHz, AM5", "Socket AM5; DDR5 only"),
    ("CPU", "Core i3-12100F",        "Intel",  95,  130, "4 cores / 8 threads, 3.3–4.3 GHz, LGA1700", "Socket LGA1700; DDR4/DDR5"),
    ("CPU", "Core i5-12400F",        "Intel",  150, 190, "6 cores / 12 threads, 2.5–4.4 GHz, LGA1700", "Socket LGA1700; DDR4/DDR5"),
    ("CPU", "Core i5-13600K",        "Intel",  280, 330, "14 cores / 20 threads, 3.5–5.1 GHz, LGA1700", "Socket LGA1700; DDR4/DDR5"),
    ("CPU", "Core i7-13700K",        "Intel",  380, 440, "16 cores / 24 threads, 3.4–5.4 GHz, LGA1700", "Socket LGA1700; DDR4/DDR5"),
    ("CPU", "Core i7-14700K",        "Intel",  400, 460, "20 cores / 28 threads, 3.4–5.6 GHz, LGA1700", "Socket LGA1700; DDR4/DDR5"),
    ("CPU", "Core i9-13900K",        "Intel",  550, 640, "24 cores / 32 threads, 3.0–5.8 GHz, LGA1700", "Socket LGA1700; DDR4/DDR5"),
    # GPUs
    ("GPU", "GeForce RTX 3060 12GB", "NVIDIA", 280, 340, "12GB GDDR6, 3584 CUDA cores",     "PCIe 4.0 x16; 1x 8-pin power"),
    ("GPU", "GeForce RTX 4060 8GB",  "NVIDIA", 290, 350, "8GB GDDR6, 3072 CUDA cores",      "PCIe 4.0 x8; 1x 8-pin power"),
    ("GPU", "GeForce RTX 4060 Ti 8GB","NVIDIA",380, 450, "8GB GDDR6, 4352 CUDA cores",      "PCIe 4.0 x8; 1x 16-pin power"),
    ("GPU", "GeForce RTX 4070",      "NVIDIA", 540, 620, "12GB GDDR6X, 5888 CUDA cores",    "PCIe 4.0 x16; 1x 16-pin power"),
    ("GPU", "GeForce RTX 4070 Super","NVIDIA", 600, 680, "12GB GDDR6X, 7168 CUDA cores",    "PCIe 4.0 x16; 1x 16-pin power"),
    ("GPU", "GeForce RTX 4080",      "NVIDIA", 950, 1100,"16GB GDDR6X, 9728 CUDA cores",    "PCIe 4.0 x16; 1x 16-pin power"),
    ("GPU", "GeForce RTX 4090",      "NVIDIA", 1600,1900,"24GB GDDR6X, 16384 CUDA cores",   "PCIe 4.0 x16; 1x 16-pin power"),
    ("GPU", "Radeon RX 6600",        "AMD",    200, 250, "8GB GDDR6, 1792 stream processors","PCIe 4.0 x8; 1x 8-pin power"),
    ("GPU", "Radeon RX 6700 XT",     "AMD",    330, 400, "12GB GDDR6, 2560 stream processors","PCIe 4.0 x16; 2x 8-pin power"),
    ("GPU", "Radeon RX 7600",        "AMD",    260, 300, "8GB GDDR6, 2048 stream processors","PCIe 4.0 x8; 1x 8-pin power"),
    ("GPU", "Radeon RX 7800 XT",     "AMD",    490, 570, "16GB GDDR6, 3840 stream processors","PCIe 4.0 x16; 2x 8-pin power"),
    ("GPU", "Radeon RX 7900 XTX",    "AMD",    900, 1050,"24GB GDDR6, 6144 stream processors","PCIe 4.0 x16; 2x 8-pin power"),
    # RAM
    ("RAM", "Vengeance LPX 16GB DDR4 3200",  "Corsair",  35, 55,  "2x8GB DDR4-3200 CL16",       "DDR4; AM4/LGA1200/LGA1700 boards"),
    ("RAM", "Vengeance 32GB DDR4 3600",      "Corsair",  70, 95,  "2x16GB DDR4-3600 CL18",      "DDR4; AM4/LGA1200/LGA1700 boards"),
    ("RAM", "Vengeance 32GB DDR5 6000",      "Corsair",  100,140, "2x16GB DDR5-6000 CL30",      "DDR5; AM5/LGA1700 (DDR5) boards"),
    ("RAM", "Ripjaws V 16GB DDR4 3200",      "G.Skill",  32, 50,  "2x8GB DDR4-3200 CL16",       "DDR4 boards"),
    ("RAM", "Trident Z5 32GB DDR5 6400",     "G.Skill",  115,155, "2x16GB DDR5-6400 CL32",      "DDR5; AM5/LGA1700 (DDR5) boards"),
    ("RAM", "Fury Beast 32GB DDR5 5600",     "Kingston", 90, 120, "2x16GB DDR5-5600 CL36",      "DDR5; AM5/LGA1700 (DDR5) boards"),
    ("RAM", "Fury 16GB DDR4 3600",           "Kingston", 38, 58,  "2x8GB DDR4-3600 CL18",       "DDR4 boards"),
    ("RAM", "Crucial Pro 32GB DDR5 5600",    "Crucial",  85, 110, "2x16GB DDR5-5600 CL46",      "DDR5; AM5/LGA1700 (DDR5) boards"),
    # Motherboards
    ("Motherboard", "B550 Tomahawk",        "MSI",      130, 170, "ATX, AM4, DDR4, PCIe 4.0",   "Socket AM4; DDR4 only"),
    ("Motherboard", "B650 Tomahawk WiFi",   "MSI",      210, 260, "ATX, AM5, DDR5, PCIe 4.0",   "Socket AM5; DDR5 only"),
    ("Motherboard", "X670E Tomahawk",       "MSI",      330, 400, "ATX, AM5, DDR5, PCIe 5.0",   "Socket AM5; DDR5 only"),
    ("Motherboard", "TUF Gaming B550-Plus", "ASUS",     145, 180, "ATX, AM4, DDR4, PCIe 4.0",   "Socket AM4; DDR4 only"),
    ("Motherboard", "ROG Strix B650-A",     "ASUS",     250, 310, "ATX, AM5, DDR5, PCIe 5.0",   "Socket AM5; DDR5 only"),
    ("Motherboard", "Z690 Aorus Elite AX",  "Gigabyte", 220, 280, "ATX, LGA1700, DDR5, PCIe 5.0","Socket LGA1700; DDR5"),
    ("Motherboard", "Z790 Aorus Elite",     "Gigabyte", 270, 330, "ATX, LGA1700, DDR5, PCIe 5.0","Socket LGA1700; DDR5"),
    ("Motherboard", "B760M Pro RS",         "ASRock",   130, 170, "mATX, LGA1700, DDR4, PCIe 4.0","Socket LGA1700; DDR4"),
    # Storage
    ("Storage", "Kingston A400 480GB SATA SSD",  "Kingston", 30, 45,  "480GB, SATA III, 500MB/s read", "Any 2.5\" SATA bay"),
    ("Storage", "Crucial MX500 1TB SATA SSD",    "Crucial",  60, 85,  "1TB, SATA III, 560MB/s read",   "Any 2.5\" SATA bay"),
    ("Storage", "Samsung 870 EVO 1TB SATA SSD",  "Samsung",  75, 100, "1TB, SATA III, 560MB/s read",   "Any 2.5\" SATA bay"),
    ("Storage", "WD Blue SN570 1TB NVMe",        "WD",       60, 85,  "1TB, PCIe 3.0 x4, 3500MB/s read","M.2 2280 PCIe 3.0 slot"),
    ("Storage", "Samsung 980 1TB NVMe",          "Samsung",  70, 95,  "1TB, PCIe 3.0 x4, 3500MB/s read","M.2 2280 PCIe 3.0 slot"),
    ("Storage", "Samsung 980 Pro 2TB NVMe",      "Samsung",  140,180, "2TB, PCIe 4.0 x4, 7000MB/s read","M.2 2280 PCIe 4.0 slot"),
    ("Storage", "WD Black SN850X 2TB NVMe",      "WD",       150,190, "2TB, PCIe 4.0 x4, 7300MB/s read","M.2 2280 PCIe 4.0 slot"),
    ("Storage", "Seagate Barracuda 2TB HDD",     "Seagate",  50, 75,  "2TB, 7200RPM, SATA III",        "Any 3.5\" SATA bay"),
    ("Storage", "WD Blue 4TB HDD",               "WD",       80, 110, "4TB, 5400RPM, SATA III",        "Any 3.5\" SATA bay"),
    # PSU
    ("PSU", "CX550M 550W 80+ Bronze",       "Corsair",      60, 80,  "550W, 80+ Bronze, semi-modular", "Standard ATX"),
    ("PSU", "RM750e 750W 80+ Gold",         "Corsair",      100,135, "750W, 80+ Gold, fully modular",  "Standard ATX"),
    ("PSU", "RM850x 850W 80+ Gold",         "Corsair",      135,170, "850W, 80+ Gold, fully modular",  "Standard ATX"),
    ("PSU", "MWE Gold 650W V2",             "Cooler Master",70, 95,  "650W, 80+ Gold, fully modular",  "Standard ATX"),
    ("PSU", "Focus GX-750",                 "Seasonic",     115,150, "750W, 80+ Gold, fully modular",  "Standard ATX"),
    ("PSU", "ToughPower GF1 850W",          "Thermaltake",  120,160, "850W, 80+ Gold, fully modular",  "Standard ATX"),
    # Case
    ("Case", "4000D Airflow",               "Corsair",      85, 110, "ATX mid-tower, 2x140mm included","Fits ATX/mATX/ITX; 360mm GPU clearance"),
    ("Case", "Lancool 216",                 "Lian Li",      95, 125, "ATX mid-tower, 2x160mm included","Fits ATX/mATX/ITX; 392mm GPU clearance"),
    ("Case", "NR200P",                      "Cooler Master",90, 120, "Mini-ITX, compact",              "Fits ITX only; 330mm GPU clearance"),
    ("Case", "Meshify 2 Compact",           "Fractal",      130,170, "ATX mid-tower mesh",             "Fits ATX/mATX/ITX; 360mm GPU clearance"),
    ("Case", "H7 Flow",                     "NZXT",         105,140, "ATX mid-tower mesh",             "Fits ATX/mATX/ITX; 400mm GPU clearance"),
    # Cooler
    ("Cooler", "Hyper 212 Black",           "Cooler Master",35, 55,  "Air cooler, 158mm height",       "AM4/AM5/LGA1700/LGA1200"),
    ("Cooler", "Peerless Assassin 120 SE",  "Thermalright", 35, 50,  "Dual-tower air cooler, 157mm",   "AM4/AM5/LGA1700/LGA1200"),
    ("Cooler", "Noctua NH-D15",             "Noctua",       100,130, "Dual-tower air cooler, 165mm",   "AM4/AM5/LGA1700/LGA1200"),
    ("Cooler", "iCUE H100i RGB Elite",      "Corsair",      120,160, "240mm AIO liquid cooler",        "AM4/AM5/LGA1700/LGA1200"),
    ("Cooler", "Liquid Freezer II 280",     "Arctic",       110,150, "280mm AIO liquid cooler",        "AM4/AM5/LGA1700/LGA1200"),
    ("Cooler", "Kraken X63 RGB",            "NZXT",         150,200, "280mm AIO liquid cooler",        "AM4/AM5/LGA1700/LGA1200"),
]

components = []
for cid, (ctype, cname, brand, lo, hi, spec, compat) in enumerate(component_catalog, start=1):
    price = round(random.uniform(lo, hi), 2)
    components.append({
        "component_id": cid,
        "component_name": cname,
        "component_type": ctype,
        "brand": brand,
        "price": price,
        "specifications": spec,
        "compatibility_info": compat,
    })

with open(f"{OUT}/Component.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=[
        "component_id", "component_name", "component_type",
        "brand", "price", "specifications", "compatibility_info"
    ])
    w.writeheader()
    w.writerows(components)

# index by type for build assembly
by_type = {}
for c in components:
    by_type.setdefault(c["component_type"], []).append(c)

# ----------------------------------------------------------------------
# 3) BUILD_REQUEST  — 80 rows (only regular users submit requests)
# ----------------------------------------------------------------------
purposes = ["Gaming", "Programming", "Video Editing", "General Use", "3D Rendering", "Streaming"]
regular_user_ids = [u["user_id"] for u in users if u["role"] == "user"]

build_requests = []
start_date = date(2025, 1, 1)
end_date   = date(2026, 5, 10)
span_days  = (end_date - start_date).days

for req_id in range(1, 81):
    user_id = random.choice(regular_user_ids)
    purpose = random.choice(purposes)
    # budget tied loosely to purpose
    if purpose == "General Use":
        budget = round(random.uniform(500, 900), 2)
    elif purpose == "Programming":
        budget = round(random.uniform(700, 1300), 2)
    elif purpose == "Streaming":
        budget = round(random.uniform(1000, 1800), 2)
    elif purpose == "Gaming":
        budget = round(random.uniform(900, 2500), 2)
    elif purpose == "Video Editing":
        budget = round(random.uniform(1400, 3200), 2)
    else:  # 3D Rendering
        budget = round(random.uniform(2000, 4000), 2)
    rdate = start_date + timedelta(days=random.randint(0, span_days))
    build_requests.append({
        "request_id": req_id,
        "budget": budget,
        "purpose": purpose,
        "request_date": rdate.isoformat(),
        "user_id": user_id,
    })

with open(f"{OUT}/Build_Request.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["request_id", "budget", "purpose", "request_date", "user_id"])
    w.writeheader()
    w.writerows(build_requests)

# ----------------------------------------------------------------------
# 4) RECOMMENDED_BUILD  — ~100 rows
#    Some requests get 1 build, some get 2 (alternative recommendations).
# ----------------------------------------------------------------------
recommended_builds = []
build_components_rows = []
build_id = 0
build_component_id = 0

def pick_component(ctype, budget_share):
    """Pick a component of given type whose price fits roughly within budget_share."""
    candidates = by_type[ctype]
    affordable = [c for c in candidates if c["price"] <= budget_share]
    if not affordable:
        # fall back to cheapest of this type
        return min(candidates, key=lambda c: c["price"])
    # bias toward the more expensive of the affordable ones to spend the budget
    affordable_sorted = sorted(affordable, key=lambda c: c["price"])
    # pick from upper half
    upper = affordable_sorted[len(affordable_sorted) // 2:]
    return random.choice(upper)

# Budget allocation percentages by component type (typical PC build heuristics)
ALLOC = {
    "CPU":         0.22,
    "GPU":         0.32,
    "RAM":         0.08,
    "Motherboard": 0.12,
    "Storage":     0.08,
    "PSU":         0.08,
    "Case":        0.05,
    "Cooler":      0.05,
}

for req in build_requests:
    n_builds = 1 if random.random() < 0.7 else 2
    for _ in range(n_builds):
        build_id += 1
        # rec date: same day or up to 3 days after request
        rec_date = date.fromisoformat(req["request_date"]) + timedelta(days=random.randint(0, 3))

        chosen = {}
        for ctype, frac in ALLOC.items():
            chosen[ctype] = pick_component(ctype, req["budget"] * frac * 1.4)  # 1.4x headroom

        # Storage sometimes gets 2 drives (SSD + HDD) on larger builds
        extra_storage = None
        if req["budget"] > 1500 and random.random() < 0.4:
            hdds = [c for c in by_type["Storage"] if "HDD" in c["specifications"]]
            if hdds:
                extra_storage = random.choice(hdds)

        # RAM sometimes gets quantity 2 (two kits) for high-budget rendering builds
        ram_qty = 2 if (req["purpose"] in ("3D Rendering", "Video Editing") and req["budget"] > 2500 and random.random() < 0.5) else 1

        # Compute total cost
        total = sum(c["price"] for c in chosen.values())
        if ram_qty == 2:
            total += chosen["RAM"]["price"]  # add one more kit
        if extra_storage:
            total += extra_storage["price"]
        total = round(total, 2)

        recommended_builds.append({
            "build_id": build_id,
            "total_cost": total,
            "recommendation_date": rec_date.isoformat(),
            "request_id": req["request_id"],
        })

        # Build_Component rows
        for ctype, comp in chosen.items():
            build_component_id += 1
            qty = ram_qty if ctype == "RAM" else 1
            build_components_rows.append({
                "build_component_id": build_component_id,
                "quantity": qty,
                "build_id": build_id,
                "component_id": comp["component_id"],
            })
        if extra_storage:
            build_component_id += 1
            build_components_rows.append({
                "build_component_id": build_component_id,
                "quantity": 1,
                "build_id": build_id,
                "component_id": extra_storage["component_id"],
            })

with open(f"{OUT}/Recommended_Build.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["build_id", "total_cost", "recommendation_date", "request_id"])
    w.writeheader()
    w.writerows(recommended_builds)

with open(f"{OUT}/Build_Component.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["build_component_id", "quantity", "build_id", "component_id"])
    w.writeheader()
    w.writerows(build_components_rows)

# ----------------------------------------------------------------------
# Summary
# ----------------------------------------------------------------------
print(f"User.csv:              {len(users)} rows")
print(f"Component.csv:         {len(components)} rows")
print(f"Build_Request.csv:     {len(build_requests)} rows")
print(f"Recommended_Build.csv: {len(recommended_builds)} rows")
print(f"Build_Component.csv:   {len(build_components_rows)} rows")

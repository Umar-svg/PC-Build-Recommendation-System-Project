# recommender.py — PC Build Recommendation Engine v6
# Fixes:
#   - "Gaming and Streaming" purpose fully supported
#   - CPU/GPU price-ratio balance rules (no more Ryzen 7 + GT 1030)
#   - Multi-pass upgrade sweeper for Max Performance
#   - Hard budget cap with ~4,000 PKR tolerance
#   - Tier scores added for all entry-level / new parts

import random
import re
from datetime import date

print(">>> RECOMMENDER v6 LOADED — BALANCE RULES ACTIVE <<<", flush=True)


# ---------- Budget allocation per purpose ----------
PURPOSE_ALLOC = {
    "Gaming": {
        "CPU": 0.16, "GPU": 0.50, "RAM": 0.07, "Motherboard": 0.08,
        "Storage": 0.06, "PSU": 0.05, "Case": 0.04, "Cooler": 0.04,
    },
    "Streaming": {
        "CPU": 0.20, "GPU": 0.42, "RAM": 0.08, "Motherboard": 0.09,
        "Storage": 0.07, "PSU": 0.05, "Case": 0.05, "Cooler": 0.04,
    },
    "Gaming and Streaming": {
        "CPU": 0.18, "GPU": 0.48, "RAM": 0.07, "Motherboard": 0.08,
        "Storage": 0.06, "PSU": 0.05, "Case": 0.04, "Cooler": 0.04,
    },
    "Video Editing": {
        "CPU": 0.28, "GPU": 0.22, "RAM": 0.14, "Motherboard": 0.10,
        "Storage": 0.12, "PSU": 0.06, "Case": 0.04, "Cooler": 0.04,
    },
    "3D Rendering": {
        "CPU": 0.32, "GPU": 0.23, "RAM": 0.15, "Motherboard": 0.10,
        "Storage": 0.08, "PSU": 0.05, "Case": 0.03, "Cooler": 0.04,
    },
    "Programming": {
        "CPU": 0.28, "GPU": 0.13, "RAM": 0.18, "Motherboard": 0.13,
        "Storage": 0.13, "PSU": 0.06, "Case": 0.05, "Cooler": 0.04,
    },
    "AI & Model Training": {
        "CPU": 0.18, "GPU": 0.42, "RAM": 0.13, "Motherboard": 0.08,
        "Storage": 0.10, "PSU": 0.05, "Case": 0.02, "Cooler": 0.02,
    },
    "General Use": {
        "CPU": 0.22, "GPU": 0.13, "RAM": 0.10, "Motherboard": 0.15,
        "Storage": 0.17, "PSU": 0.10, "Case": 0.08, "Cooler": 0.05,
    },
}


# ---------- Hardware tier rankings ----------
CPU_TIERS = {
    "Gaming": {
        "Ryzen 7 7700X":    100, "Ryzen 9 7900X":     95, "Ryzen 9 7950X":     92,
        "Ryzen 7 5800X":     88, "Ryzen 5 7600":      85, "Ryzen 5 5600":      78,
        "Ryzen 5 5500":      70, "Ryzen 5 2600":      60, "Core i5-14600K":    58,
        "Core i7-14700K":    55, "Core i7-13700K":    52, "Core i9-13900K":    50,
        "Core i5-13600K":    45, "Core i5-13400F":    42, "Core i5-12400F":    40,
    },
    "Streaming": {
        "Core i7-14700K":  100, "Ryzen 9 7900X":    98, "Ryzen 7 7700X":    95,
        "Core i7-13700K":   93, "Core i5-14600K":   90, "Core i9-13900K":   88,
        "Ryzen 9 7950X":    85, "Core i5-13600K":   80, "Ryzen 7 5800X":    75,
        "Core i5-13400F":   68, "Ryzen 5 7600":     65, "Core i5-12400F":   55,
        "Ryzen 5 5600":     50, "Ryzen 5 5500":     42, "Ryzen 5 2600":     30,
    },
    "Gaming and Streaming": {
        "Core i7-14700K":  100, "Ryzen 9 7900X":    98, "Ryzen 7 7700X":    95,
        "Core i7-13700K":   93, "Core i5-14600K":   90, "Core i9-13900K":   88,
        "Ryzen 9 7950X":    85, "Core i5-13600K":   80, "Ryzen 7 5800X":    75,
        "Core i5-13400F":   68, "Ryzen 5 7600":     65, "Core i5-12400F":   55,
        "Ryzen 5 5600":     50, "Ryzen 5 5500":     42, "Ryzen 5 2600":     30,
    },
    "Video Editing": {
        "Core i9-13900K":   100, "Core i7-14700K":    97, "Core i7-13700K":    93,
        "Core i5-14600K":    90, "Core i5-13600K":    88, "Core i5-13400F":    80,
        "Core i5-12400F":    75, "Ryzen 9 7950X":     55, "Ryzen 9 7900X":     52,
        "Ryzen 7 7700X":     48, "Ryzen 7 5800X":     42, "Ryzen 5 7600":      35,
        "Ryzen 5 5600":      25, "Ryzen 5 5500":      18, "Ryzen 5 2600":      10,
    },
    "3D Rendering": {
        "Ryzen 9 7950X":   100, "Core i9-13900K":   98, "Ryzen 9 7900X":    95,
        "Core i7-14700K":   92, "Core i7-13700K":   85, "Ryzen 7 7700X":    75,
        "Core i5-14600K":   70, "Core i5-13600K":   65, "Ryzen 7 5800X":    60,
        "Core i5-13400F":   45, "Ryzen 5 7600":     40, "Core i5-12400F":   35,
        "Ryzen 5 5600":     25, "Ryzen 5 5500":     18, "Ryzen 5 2600":     10,
    },
    "Programming": {
        "Ryzen 9 7900X":   100, "Core i7-14700K":   98, "Ryzen 7 7700X":    95,
        "Core i7-13700K":   93, "Core i5-14600K":   90, "Ryzen 9 7950X":    88,
        "Core i9-13900K":   85, "Core i5-13600K":   80, "Ryzen 7 5800X":    75,
        "Ryzen 5 7600":     70, "Core i5-13400F":   65, "Core i5-12400F":   60,
        "Ryzen 5 5600":     55, "Ryzen 5 5500":     45, "Ryzen 5 2600":     35,
    },
    "AI & Model Training": {
        "Ryzen 9 7950X":    100, "Ryzen 9 7900X":     97, "Core i9-13900K":    95,
        "Core i7-14700K":    92, "Core i7-13700K":    85, "Ryzen 7 7700X":     78,
        "Core i5-14600K":    72, "Core i5-13600K":    65, "Ryzen 7 5800X":     60,
        "Core i5-13400F":    45, "Ryzen 5 7600":      35, "Core i5-12400F":    30,
        "Ryzen 5 5600":      20, "Ryzen 5 5500":      12, "Ryzen 5 2600":       8,
    },
    "General Use": {
        "Ryzen 5 5600":     100, "Ryzen 5 7600":      98, "Core i5-12400F":    96,
        "Core i5-13400F":    93, "Ryzen 5 5500":      90, "Ryzen 5 2600":      85,
        "Core i5-13600K":    70, "Core i5-14600K":    65, "Ryzen 7 7700X":     55,
        "Ryzen 7 5800X":     50, "Core i7-13700K":    40, "Core i7-14700K":    35,
        "Ryzen 9 7900X":     25, "Ryzen 9 7950X":     20, "Core i9-13900K":    15,
    },
}

GPU_TIERS = {
    "Gaming": {
        "GeForce RTX 4090":         100, "GeForce RTX 4080":           95,
        "Radeon RX 7900 XTX":         92, "GeForce RTX 4070 Ti":        90,
        "GeForce RTX 4070 Super":     88, "GeForce RTX 4070":           85,
        "Radeon RX 7800 XT":          80, "Radeon RX 7700 XT":          76,
        "GeForce RTX 4060 Ti 8GB":    72, "Radeon RX 6700 XT":          68,
        "GeForce RTX 3070":           65, "GeForce RTX 3060 12GB":      62,
        "GeForce RTX 4060 8GB":       60, "Radeon RX 7600":             55,
        "Radeon RX 6600":             45, "GeForce RTX 3050 8GB":       40,
        "Radeon RX 6500 XT":          30,
    },
    "Streaming": {
        "GeForce RTX 4090":         100, "GeForce RTX 4080":           98,
        "GeForce RTX 4070 Ti":        92, "GeForce RTX 4070 Super":     90,
        "GeForce RTX 4070":           88, "GeForce RTX 4060 Ti 8GB":    78,
        "GeForce RTX 3070":           75, "GeForce RTX 3060 12GB":      72,
        "GeForce RTX 4060 8GB":       68, "GeForce RTX 3050 8GB":       55,
        "Radeon RX 7900 XTX":         50, "Radeon RX 7800 XT":          45,
        "Radeon RX 7700 XT":          42, "Radeon RX 6700 XT":          38,
        "Radeon RX 7600":             32, "Radeon RX 6600":             25,
        "Radeon RX 6500 XT":          15,
    },
    "Gaming and Streaming": {
        "GeForce RTX 4090":         100, "GeForce RTX 4080":           96,
        "GeForce RTX 4070 Ti":        92, "GeForce RTX 4070 Super":     89,
        "GeForce RTX 4070":           86, "Radeon RX 7900 XTX":         78,
        "GeForce RTX 4060 Ti 8GB":    75, "Radeon RX 7800 XT":          70,
        "GeForce RTX 3070":           68, "GeForce RTX 3060 12GB":      65,
        "GeForce RTX 4060 8GB":       63, "Radeon RX 7700 XT":          58,
        "Radeon RX 6700 XT":          50, "Radeon RX 7600":             45,
        "GeForce RTX 3050 8GB":       42, "Radeon RX 6600":             35,
        "Radeon RX 6500 XT":          20,
    },
    "Video Editing": {
        "GeForce RTX 4090":         100, "GeForce RTX 4080":           98,
        "GeForce RTX 4070 Ti":        94, "GeForce RTX 4070 Super":     92,
        "GeForce RTX 4070":           90, "GeForce RTX 3070":           82,
        "GeForce RTX 4060 Ti 8GB":    78, "GeForce RTX 3060 12GB":      75,
        "GeForce RTX 4060 8GB":       65, "GeForce RTX 3050 8GB":       50,
        "Radeon RX 7900 XTX":         45, "Radeon RX 7800 XT":          38,
        "Radeon RX 7700 XT":          35, "Radeon RX 6700 XT":          30,
        "Radeon RX 7600":             22, "Radeon RX 6600":             15,
        "Radeon RX 6500 XT":           8,
    },
    "3D Rendering": {
        "GeForce RTX 4090":         100, "GeForce RTX 4080":           95,
        "GeForce RTX 4070 Ti":        90, "GeForce RTX 4070 Super":     88,
        "GeForce RTX 4070":           85, "GeForce RTX 3070":           78,
        "GeForce RTX 3060 12GB":      72, "GeForce RTX 4060 Ti 8GB":    65,
        "GeForce RTX 4060 8GB":       55, "GeForce RTX 3050 8GB":       40,
        "Radeon RX 7900 XTX":         35, "Radeon RX 7800 XT":          28,
        "Radeon RX 7700 XT":          25, "Radeon RX 6700 XT":          20,
        "Radeon RX 7600":             10, "Radeon RX 6600":              5,
        "Radeon RX 6500 XT":           2,
    },
    "Programming": {
        "GeForce RTX 4060 8GB":     100, "GeForce RTX 3060 12GB":      95,
        "Radeon RX 7600":             90, "GeForce RTX 3050 8GB":       88,
        "Radeon RX 6600":             85, "GeForce RTX 4060 Ti 8GB":    75,
        "Radeon RX 6500 XT":          72, "Radeon RX 6700 XT":          65,
        "GeForce RTX 3070":           60, "Radeon RX 7700 XT":          50,
        "GeForce RTX 4070":           45, "Radeon RX 7800 XT":          40,
        "GeForce RTX 4070 Super":     30, "GeForce RTX 4070 Ti":        20,
        "GeForce RTX 4080":           15, "Radeon RX 7900 XTX":         12,
        "GeForce RTX 4090":           10,
    },
    "AI & Model Training": {
        "GeForce RTX 4090":         100, "GeForce RTX 4080":           85,
        "GeForce RTX 4070 Ti":        75, "GeForce RTX 4070 Super":     72,
        "GeForce RTX 4070":           70, "GeForce RTX 3060 12GB":      60,
        "GeForce RTX 3070":           58, "GeForce RTX 4060 Ti 8GB":    45,
        "GeForce RTX 4060 8GB":       40, "GeForce RTX 3050 8GB":       25,
        "Radeon RX 7900 XTX":          5, "Radeon RX 7800 XT":           3,
        "Radeon RX 7700 XT":           3, "Radeon RX 6700 XT":           2,
        "Radeon RX 7600":              1, "Radeon RX 6600":              1,
        "Radeon RX 6500 XT":           1,
    },
    "General Use": {
        "Radeon RX 6500 XT":        100, "Radeon RX 6600":            95,
        "GeForce RTX 3050 8GB":      92, "Radeon RX 7600":            90,
        "GeForce RTX 4060 8GB":      85, "GeForce RTX 3060 12GB":     78,
        "GeForce RTX 4060 Ti 8GB":   60, "Radeon RX 6700 XT":         50,
        "GeForce RTX 3070":          40, "GeForce RTX 4070":          25,
        "Radeon RX 7700 XT":         22, "Radeon RX 7800 XT":         20,
        "GeForce RTX 4070 Super":    15, "GeForce RTX 4070 Ti":       12,
        "GeForce RTX 4080":          10, "Radeon RX 7900 XTX":         8,
        "GeForce RTX 4090":           5,
    },
}


# ---------- Premium parts auto-added to every tier ----------
_PREMIUM_CPU_BONUS = {
    "Threadripper 7980X":  120, "Threadripper 7960X":  115,
    "Xeon w7-3465X":       118, "Core i9-14900KS":     108,
    "Core i9-14900K":      105, "Ryzen 9 9950X3D":     109,
    "Ryzen 9 9950X":       106,
}
_PREMIUM_GPU_BONUS = {
    "RTX 6000 Ada":        120, "RTX A6000":           115,
    "GeForce RTX 5090":    118, "GeForce RTX 4090 Ti": 110,
}
for _purpose, _tiers in CPU_TIERS.items():
    for _name, _score in _PREMIUM_CPU_BONUS.items():
        _tiers.setdefault(_name, _score)
for _purpose, _tiers in GPU_TIERS.items():
    for _name, _score in _PREMIUM_GPU_BONUS.items():
        _tiers.setdefault(_name, _score)

# Workstation parts downscored for consumer purposes
# These are pro-grade silicon — bad for gaming (lower clocks, wrong silicon).
_WORKSTATION_CPUS = ["Threadripper 7980X", "Threadripper 7960X", "Xeon w7-3465X"]
_WORKSTATION_GPUS = ["RTX A6000", "RTX 6000 Ada"]

for _name in _WORKSTATION_CPUS:
    CPU_TIERS["Gaming"][_name] = 30                  # Bad for gaming
    CPU_TIERS["Streaming"][_name] = 40
    CPU_TIERS["Gaming and Streaming"][_name] = 35
    CPU_TIERS["General Use"][_name] = 15
    CPU_TIERS["Programming"][_name] = 80             # Still ok-ish for compile workloads
    CPU_TIERS["Video Editing"][_name] = 60
    # Keep 3D Rendering / AI scores high (already set by _PREMIUM_CPU_BONUS)

for _name in _WORKSTATION_GPUS:
    GPU_TIERS["Gaming"][_name] = 20                  # Bad for gaming
    GPU_TIERS["Streaming"][_name] = 25
    GPU_TIERS["Gaming and Streaming"][_name] = 22
    GPU_TIERS["General Use"][_name] = 10
    GPU_TIERS["Programming"][_name] = 30
    GPU_TIERS["Video Editing"][_name] = 70
    # AI & 3D Rendering keep their high scores

# --- AI & Model Training: user prefers Intel CPUs + NVIDIA GPUs ---
# CUDA is critical for ML, and Intel HEDT/consumer flagships scale better
# for typical training rigs than Threadripper (which is overkill and pricier).
CPU_TIERS["AI & Model Training"]["Xeon w7-3465X"]      = 100   # Top Intel HEDT
CPU_TIERS["AI & Model Training"]["Core i9-14900KS"]    = 98
CPU_TIERS["AI & Model Training"]["Core i9-14900K"]     = 96
CPU_TIERS["AI & Model Training"]["Core i9-13900K"]     = 92
CPU_TIERS["AI & Model Training"]["Core i7-14700K"]     = 88
CPU_TIERS["AI & Model Training"]["Core i7-13700K"]     = 82
CPU_TIERS["AI & Model Training"]["Core i5-14600K"]     = 70
CPU_TIERS["AI & Model Training"]["Core i5-13600K"]     = 64
CPU_TIERS["AI & Model Training"]["Threadripper 7980X"] = 75    # demoted below Intel
CPU_TIERS["AI & Model Training"]["Threadripper 7960X"] = 70
CPU_TIERS["AI & Model Training"]["Ryzen 9 9950X3D"]    = 72
CPU_TIERS["AI & Model Training"]["Ryzen 9 9950X"]      = 68
CPU_TIERS["AI & Model Training"]["Ryzen 9 7950X"]      = 60
CPU_TIERS["AI & Model Training"]["Ryzen 9 7900X"]      = 55
CPU_TIERS["AI & Model Training"]["Ryzen 7 7700X"]      = 45

CPU_TIERS["Gaming"]["Ryzen 9 9950X3D"] = 112
CPU_TIERS["Gaming and Streaming"]["Ryzen 9 9950X3D"] = 110
for _name in ["Ryzen 9 9950X", "Ryzen 9 9950X3D", "Core i9-14900K", "Core i9-14900KS"]:
    CPU_TIERS["General Use"][_name] = 95
    CPU_TIERS["Programming"][_name] = 100

GPU_TIERS["Gaming"]["GeForce RTX 5090"] = 120
GPU_TIERS["Gaming and Streaming"]["GeForce RTX 5090"] = 118
GPU_TIERS["General Use"]["GeForce RTX 5090"] = 85


# ---------- Motherboard tier rankings ----------
# Without this, the picker just grabs the most expensive board, which often
# isn't the newest chipset. X870E (newer) should beat X670E for AM5 builds.
MOTHERBOARD_TIERS = {
    # AM5 (newest first)
    "X870E Aorus Master":       105,    # Newest AMD chipset (2024) — top AM5 board
    "ROG Crosshair X670E Hero":  90,
    "X670E Tomahawk":            85,
    "ROG Strix B650-A":          78,
    "B650 Tomahawk WiFi":        72,
    "B650M-A WiFi":              60,
    # LGA1700 DDR5
    "ROG Maximus Z790 Hero":     95,
    "Z790 Aorus Elite":          85,
    "Z690 Aorus Elite AX":       72,
    # LGA1700 DDR4 (older, cheaper)
    "B760 Tomahawk WiFi":        58,
    "B760M Pro RS":              50,
    # AM4 (legacy)
    "X570 Aorus Elite":          50,
    "TUF Gaming B550-Plus":      40,
    "B550 Tomahawk":             38,
    "B550M-A WiFi":              30,
    "B450M Steel Legend":        20,
    "A520M-A Pro":               15,
    # Workstation
    "TRX50 AERO D":              90,
    "Pro WS W790-ACE":           90,
}


# ---------- Entry-level / newer parts (fill tier gaps) ----------
_ENTRY_GPU_SCORES = {
    # name:                       Gaming Streaming G+S V.Ed 3D Prog AI Gen
    "GeForce GT 1030 2GB":        (5,    5,    5,    5,    3,   50,   1,   80),
    "GeForce GTX 1650 4GB":       (25,  20,  22,   15,    8,   65,   3,   90),
    "GeForce GTX 1660 Super":     (38,  32,  35,   25,   18,   78,   8,   88),
    "GeForce GTX 1070 8GB":       (42,  35,  38,   28,   22,   72,  10,   75),
    "GeForce RTX 2060 6GB":       (50,  45,  48,   42,   30,   75,  20,   70),
    "GeForce RTX 2060 Super":     (58,  52,  55,   48,   35,   78,  25,   65),
    "GeForce RTX 2070 Super":     (66,  60,  62,   58,   45,   72,  35,   55),
    "Radeon RX 6400":             (22,  18,  20,   12,    6,   62,   2,   85),
    "Radeon RX 6600 XT":          (55,  45,  50,   35,   25,   72,   3,   60),
    "GeForce RTX 4070 Ti Super":  (93,  91,  92,   93,   89,   18,  76,   14),
    "Radeon RX 7900 XT":          (88,  48,  68,   42,   33,   11,   4,    9),
    "GeForce RTX 4080 Super":     (96,  98,  97,   98,   95,   16,  86,   10),
    "GeForce RTX 4090 Ti":       (105, 100, 102,  100,   98,   11, 102,    7),
}
_ENTRY_CPU_SCORES = {
    # name:                       Gaming Stream G+S V.Ed 3D Prog AI Gen
    "Ryzen 3 4100":               (35,  25,  28,   15,    8,   40,   5,   75),
    "Ryzen 5 4500":               (55,  40,  45,   30,   18,   55,  12,   88),
    "Ryzen 5 5600X":              (82,  72,  78,   35,   30,   78,  25,   95),
    "Ryzen 5 7500F":              (88,  80,  85,   40,   42,   82,  40,   92),
    "Ryzen 5 7600X":              (90,  85,  88,   45,   48,   88,  45,   88),
    "Ryzen 7 5700X":              (90,  80,  85,   45,   65,   85,  60,   60),
    "Ryzen 7 7700":               (96,  92,  94,   50,   72,   92,  76,   55),
    "Ryzen 7 5800X3D":            (95,  78,  88,   40,   55,   80,  55,   55),
    "Ryzen 7 7800X3D":           (105,  88, 100,   55,   68,   90,  72,   55),
    "Ryzen 9 7900":               (90,  95,  93,   55,   92,   95,  92,   30),
    "Ryzen 9 7950X3D":           (108,  90, 100,   58,  100,   92,  98,   25),
    "Core i3-13100F":             (45,  35,  40,   78,   18,   62,  12,   95),
    "Core i5-13600K":             (88,  90,  90,   92,   78,   88,  72,   65),
}
_PURPOSE_ORDER = ["Gaming","Streaming","Gaming and Streaming","Video Editing",
                  "3D Rendering","Programming","AI & Model Training","General Use"]
for name, scores in _ENTRY_GPU_SCORES.items():
    for purpose, score in zip(_PURPOSE_ORDER, scores):
        GPU_TIERS[purpose].setdefault(name, score)
for name, scores in _ENTRY_CPU_SCORES.items():
    for purpose, score in zip(_PURPOSE_ORDER, scores):
        CPU_TIERS[purpose].setdefault(name, score)


# ---------- Helpers ----------
def _ram_gb(spec):
    if not spec:
        return 0
    m = re.search(r"(\d+)x(\d+)\s*GB", spec, re.IGNORECASE)
    if m:
        return int(m.group(1)) * int(m.group(2))
    m = re.search(r"(\d+)\s*GB", spec, re.IGNORECASE)
    return int(m.group(1)) if m else 0


def ram_filter(comp, purpose):
    gb = _ram_gb(comp.get("specifications", ""))
    # Minimum RAM per purpose
    if purpose == "AI & Model Training":
        min_gb = 32
    elif purpose in ("3D Rendering", "Video Editing"):
        min_gb = 32
    elif purpose in ("Gaming", "Streaming", "Gaming and Streaming", "Programming"):
        min_gb = 16
    else:
        min_gb = 8

    # Maximum sensible RAM per purpose — prevents wasting budget on
    # 96GB/128GB kits for gaming (nobody games on 128GB).
    if purpose in ("Gaming", "Streaming", "Gaming and Streaming"):
        max_gb = 32          # 32GB is plenty for gaming + streaming
    elif purpose == "Programming":
        max_gb = 64
    elif purpose in ("Video Editing", "3D Rendering"):
        max_gb = 64          # 64GB covers most editing/rendering
    elif purpose == "AI & Model Training":
        max_gb = 128         # AI genuinely benefits from huge RAM
    else:  # General Use
        max_gb = 32

    return min_gb <= gb <= max_gb


def storage_filter(comp, purpose):
    spec = (comp.get("specifications") or "").upper()
    if purpose == "AI & Model Training":
        return "NVME" in spec and "PCIE 4.0" in spec
    if purpose in ("Video Editing", "3D Rendering"):
        return "NVME" in spec
    return True


# ---------- Tier-based picker ----------
def pick_tier_based(candidates, max_price, tier_map, strategy="balanced"):
    if not tier_map:
        affordable = [c for c in candidates if float(c["price"]) <= max_price]
        if not affordable:
            return min(candidates, key=lambda c: float(c["price"]))
        if strategy == "top":
            return max(affordable, key=lambda c: float(c["price"]))
        if strategy == "mid":
            affordable.sort(key=lambda c: float(c["price"]))
            return affordable[len(affordable) // 2]
        return affordable[len(affordable) - 1]

    scored = [(tier_map.get(c["component_name"], 0), c) for c in candidates]
    affordable = [(s, c) for s, c in scored if float(c["price"]) <= max_price]
    if not affordable:
        scored.sort(key=lambda x: float(x[1]["price"]))
        return scored[0][1]

    affordable.sort(key=lambda x: x[0], reverse=True)

    if strategy == "top":
        return affordable[0][1]
    if strategy == "mid":
        n = len(affordable)
        if n >= 4:
            mid_pool = affordable[n // 3 : (2 * n) // 3 + 1]
        else:
            mid_pool = affordable[-2:]
        return random.choice(mid_pool)[1]

    n = len(affordable)
    top_n = max(2, int(n * 0.3))
    return random.choice(affordable[:top_n])[1]


def pick_filtered(candidates, max_price, purpose, filter_fn, strategy="balanced"):
    if filter_fn:
        filtered = [c for c in candidates if filter_fn(c, purpose)] or candidates
    else:
        filtered = candidates

    affordable = [c for c in filtered if float(c["price"]) <= max_price]
    if not affordable:
        return min(filtered, key=lambda c: float(c["price"]))

    affordable.sort(key=lambda c: float(c["price"]))

    if strategy == "top":
        return affordable[-1]
    if strategy == "mid":
        return affordable[len(affordable) // 2]

    upper = affordable[len(affordable) // 2:]
    return random.choice(upper) if upper else affordable[-1]


# ---------- Compatibility ----------
def check_compatibility(chosen):
    cpu_info = chosen["CPU"]["compatibility_info"] or ""
    mb_info  = chosen["Motherboard"]["compatibility_info"] or ""
    ram_info = chosen["RAM"]["compatibility_info"] or ""

    # Now includes workstation sockets so the picker can't pair a Ryzen
    # with a Xeon/Threadripper motherboard (or vice versa).
    sockets = ["AM4", "AM5", "LGA1700", "LGA1200", "LGA4677", "sTR5"]
    cpu_sock = next((s for s in sockets if s in cpu_info), None)
    mb_sock  = next((s for s in sockets if s in mb_info),  None)
    if cpu_sock and mb_sock and cpu_sock != mb_sock:
        return False

    if "DDR5" in mb_info and "DDR4" in ram_info and "DDR5" not in ram_info:
        return False
    if "DDR4" in mb_info and "DDR5" in ram_info and "DDR4" not in ram_info:
        return False

    return True


def is_workstation_part(comp):
    """True if this is a workstation/server CPU, GPU, or motherboard."""
    name = (comp.get("component_name") or "").lower()
    info = (comp.get("compatibility_info") or "").lower()
    ctype = comp.get("component_type", "")

    if ctype == "CPU":
        return ("threadripper" in name or "xeon" in name or
                "str5" in info or "lga4677" in info)
    if ctype == "GPU":
        # Workstation NVIDIA cards: A6000, RTX 6000 Ada, A4000, A5000, Quadro
        return ("a6000" in name or "rtx 6000 ada" in name or
                "a4000" in name or "a5000" in name or "quadro" in name)
    if ctype == "Motherboard":
        return ("str5" in info or "lga4677" in info or
                "trx" in name.replace(" ", "") or
                "w790" in name.replace(" ", "") or
                "pro ws" in name.lower())
    return False


# Brand preference rules per purpose.
# For Video Editing and AI & Model Training, NVIDIA GPUs are required for
# proper CUDA acceleration in Premiere/DaVinci/PyTorch/TensorFlow. AMD cards
# are filtered out unless no NVIDIA option fits the budget.
NVIDIA_REQUIRED_PURPOSES = {"Video Editing", "AI & Model Training", "3D Rendering"}

# For AI & Model Training, the user specifically wants Intel CPUs (not AMD/Threadripper)
INTEL_PREFERRED_PURPOSES = {"AI & Model Training"}


def filter_by_brand_preference(parts, ctype, purpose):
    """Apply brand preference. Returns filtered list, or original if empty."""
    if ctype == "GPU" and purpose in NVIDIA_REQUIRED_PURPOSES:
        nvidia = [c for c in parts if (c.get("brand") or "").lower() == "nvidia"]
        if nvidia:
            return nvidia
    if ctype == "CPU" and purpose in INTEL_PREFERRED_PURPOSES:
        intel = [c for c in parts if (c.get("brand") or "").lower() == "intel"]
        if intel:
            return intel
    return parts


# ---------- Build assembly ----------
def fetch_components_by_type(cursor):
    cursor.execute("""
        SELECT component_id, component_name, component_type, brand,
               price, specifications, compatibility_info
        FROM Component
    """)
    by_type = {}
    for row in cursor.fetchall():
        by_type.setdefault(row["component_type"], []).append(row)
    return by_type


def build_one_recommendation(by_type, budget, purpose, build_preference="Balanced"):
    alloc = PURPOSE_ALLOC.get(purpose, PURPOSE_ALLOC["General Use"])
    cpu_tiers = CPU_TIERS.get(purpose, {})
    gpu_tiers = GPU_TIERS.get(purpose, {})

    # Filter out workstation/server parts for consumer purposes.
    # Workstation parts are only appropriate for 3D Rendering and AI & Model Training
    # (and only at very high budgets). Gaming/Streaming/Programming/etc. should
    # never see Threadripper, Xeon, A6000, or Pro WS motherboards.
    CONSUMER_PURPOSES = {"Gaming", "Streaming", "Gaming and Streaming",
                         "Video Editing", "Programming", "General Use"}
    if purpose in CONSUMER_PURPOSES:
        by_type = {
            ctype: [c for c in parts if not is_workstation_part(c)] or parts
            for ctype, parts in by_type.items()
        }

    # Apply brand preferences: NVIDIA GPUs for Video Editing/AI/3D Rendering
    # (CUDA acceleration), Intel CPUs for AI & Model Training.
    by_type = {
        ctype: filter_by_brand_preference(parts, ctype, purpose)
        for ctype, parts in by_type.items()
    }

    usd_tolerance = 0.0
    if build_preference == "Maximum Performance":
        headroom = 1.00
        tier_strategy = "top"
        usd_tolerance = 14.0
    elif build_preference == "Budget Saver":
        headroom = 0.75
        tier_strategy = "mid"
    else:
        headroom = 0.95
        tier_strategy = "balanced"

    hard_cap = budget + usd_tolerance

    BALANCE_RULES = {
        "Gaming":               (1.3, 5.0),
        "Streaming":            (1.1, 4.0),
        "Gaming and Streaming": (1.2, 4.5),
        "Video Editing":        (0.6, 2.5),
        "3D Rendering":         (0.5, 2.5),
        "Programming":          (0.2, 1.5),
        "AI & Model Training":  (1.5, 8.0),
        "General Use":          (0.3, 2.0),
    }
    balance_min, balance_max = BALANCE_RULES.get(purpose, (0.3, 5.0))

    def is_balanced(components_dict):
        cpu_p = float(components_dict["CPU"]["price"])
        gpu_p = float(components_dict["GPU"]["price"])
        if cpu_p <= 0:
            return True
        ratio = gpu_p / cpu_p
        return balance_min <= ratio <= balance_max

    chosen = {}
    for _ in range(20):
        chosen = {}
        for ctype, frac in alloc.items():
            if ctype not in by_type:
                return None
            max_price = budget * frac * headroom
            if ctype == "CPU":
                chosen[ctype] = pick_tier_based(by_type[ctype], max_price, cpu_tiers, tier_strategy)
            elif ctype == "GPU":
                chosen[ctype] = pick_tier_based(by_type[ctype], max_price, gpu_tiers, tier_strategy)
            elif ctype == "RAM":
                chosen[ctype] = pick_filtered(by_type[ctype], max_price, purpose, ram_filter, tier_strategy)
            elif ctype == "Storage":
                chosen[ctype] = pick_filtered(by_type[ctype], max_price, purpose, storage_filter, tier_strategy)
            elif ctype == "Motherboard":
                # Use motherboard tier ranking (X870E > X670E > etc.)
                chosen[ctype] = pick_tier_based(by_type[ctype], max_price,
                                                MOTHERBOARD_TIERS, tier_strategy)
            else:
                chosen[ctype] = pick_filtered(by_type[ctype], max_price, purpose, None, tier_strategy)
        if check_compatibility(chosen):
            break

    # If we still failed compat after 20 random tries, FORCE a match by
    # picking a motherboard/RAM that matches the CPU's socket.
    if not check_compatibility(chosen):
        cpu_info = chosen["CPU"].get("compatibility_info") or ""
        sockets = ["AM4", "AM5", "LGA1700", "LGA1200", "LGA4677", "sTR5"]
        cpu_sock = next((s for s in sockets if s in cpu_info), None)
        if cpu_sock:
            # Find best motherboard matching this socket
            mb_max = budget * alloc.get("Motherboard", 0.10) * headroom * 2.0  # 2x leeway
            mb_candidates = [c for c in by_type["Motherboard"]
                             if cpu_sock in (c.get("compatibility_info") or "")
                             and float(c["price"]) <= mb_max]
            if not mb_candidates:
                mb_candidates = [c for c in by_type["Motherboard"]
                                 if cpu_sock in (c.get("compatibility_info") or "")]
            if mb_candidates:
                # Pick using motherboard tier ranking (newest chipset wins)
                if tier_strategy == "top":
                    mb_candidates.sort(key=lambda c: (MOTHERBOARD_TIERS.get(c["component_name"], 0),
                                                       float(c["price"])), reverse=True)
                    chosen["Motherboard"] = mb_candidates[0]
                elif tier_strategy == "mid":
                    mb_candidates.sort(key=lambda c: float(c["price"]))
                    chosen["Motherboard"] = mb_candidates[len(mb_candidates)//2]
                else:
                    mb_candidates.sort(key=lambda c: MOTHERBOARD_TIERS.get(c["component_name"], 0), reverse=True)
                    chosen["Motherboard"] = mb_candidates[0]

        # Also force RAM type to match motherboard
        mb_info = chosen["Motherboard"].get("compatibility_info") or ""
        if "DDR5" in mb_info:
            ram_pool = [c for c in by_type["RAM"]
                        if "DDR5" in (c.get("compatibility_info") or "")
                        and ram_filter(c, purpose)]
        elif "DDR4" in mb_info:
            ram_pool = [c for c in by_type["RAM"]
                        if "DDR4" in (c.get("compatibility_info") or "")
                        and ram_filter(c, purpose)]
        else:
            ram_pool = []
        if ram_pool:
            ram_max = budget * alloc.get("RAM", 0.08) * headroom * 2.0
            affordable_ram = [c for c in ram_pool if float(c["price"]) <= ram_max]
            if affordable_ram:
                if tier_strategy == "top":
                    chosen["RAM"] = max(affordable_ram, key=lambda c: float(c["price"]))
                else:
                    chosen["RAM"] = affordable_ram[len(affordable_ram)//2]
            else:
                chosen["RAM"] = min(ram_pool, key=lambda c: float(c["price"]))

    ram_qty = 1
    if purpose == "AI & Model Training" and budget > 2500:
        ram_qty = 2
    elif purpose in ("3D Rendering", "Video Editing") and budget > 1800:
        if random.random() < 0.7:
            ram_qty = 2

    extra_storage = None
    if build_preference != "Budget Saver" and budget > 1200 and random.random() < 0.35:
        hdds = [c for c in by_type.get("Storage", [])
                if "HDD" in (c["specifications"] or "")
                and c["component_id"] != chosen["Storage"]["component_id"]]
        if hdds:
            extra_storage = random.choice(hdds)

    total = sum(float(c["price"]) for c in chosen.values())
    if ram_qty == 2:
        total += float(chosen["RAM"]["price"])
    if extra_storage:
        total += float(extra_storage["price"])

    # ---- Max Performance: balance-fix + multi-pass sweeper ----
    if build_preference == "Maximum Performance":

        def fix_balance():
            for _ in range(15):
                cpu_p = float(chosen["CPU"]["price"])
                gpu_p = float(chosen["GPU"]["price"])
                if cpu_p <= 0:
                    return
                ratio = gpu_p / cpu_p
                t = sum(float(c["price"]) for c in chosen.values())
                if ram_qty == 2: t += float(chosen["RAM"]["price"])
                if extra_storage: t += float(extra_storage["price"])
                room = hard_cap - t

                if ratio < balance_min:
                    target_gpu_price = cpu_p * balance_min
                    candidates = [c for c in by_type["GPU"]
                                  if gpu_p < float(c["price"]) <= min(gpu_p + room, target_gpu_price * 1.3)]
                    if not candidates:
                        target_cpu_price = gpu_p / balance_min
                        cheaper_cpus = [c for c in by_type["CPU"]
                                        if target_cpu_price * 0.7 <= float(c["price"]) < cpu_p]
                        if not cheaper_cpus:
                            break
                        # Sort by CPU TIER SCORE (descending), not just price
                        cheaper_cpus.sort(key=lambda c: (cpu_tiers.get(c["component_name"], 0),
                                                        float(c["price"])), reverse=True)
                        swapped = False
                        for cand in cheaper_cpus:
                            test = dict(chosen); test["CPU"] = cand
                            if check_compatibility(test):
                                chosen["CPU"] = cand; swapped = True; break
                        if not swapped: break
                        continue
                    # Sort GPUs by TIER SCORE (descending), not just price
                    candidates.sort(key=lambda c: (gpu_tiers.get(c["component_name"], 0),
                                                   float(c["price"])), reverse=True)
                    swapped = False
                    for cand in candidates:
                        test = dict(chosen); test["GPU"] = cand
                        if check_compatibility(test):
                            chosen["GPU"] = cand; swapped = True; break
                    if not swapped: break

                elif ratio > balance_max:
                    target_cpu_price = gpu_p / balance_max
                    candidates = [c for c in by_type["CPU"]
                                  if cpu_p < float(c["price"]) <= min(cpu_p + room, target_cpu_price * 1.3)]
                    if not candidates: break
                    # CRITICAL FIX: sort by CPU TIER SCORE for this purpose, not price.
                    # This prevents Threadripper from being picked for gaming.
                    candidates.sort(key=lambda c: (cpu_tiers.get(c["component_name"], 0),
                                                   float(c["price"])), reverse=True)
                    swapped = False
                    for cand in candidates:
                        test = dict(chosen); test["CPU"] = cand
                        if check_compatibility(test):
                            chosen["CPU"] = cand; swapped = True; break
                    if not swapped: break
                else:
                    return

        fix_balance()

        priority_by_purpose = {
            "Gaming":              ["GPU", "CPU", "RAM", "Storage", "Motherboard", "Cooler", "PSU", "Case"],
            "Streaming":           ["GPU", "CPU", "RAM", "Storage", "Motherboard", "Cooler", "PSU", "Case"],
            "Gaming and Streaming":["GPU", "CPU", "RAM", "Storage", "Motherboard", "Cooler", "PSU", "Case"],
            "Video Editing":       ["CPU", "RAM", "GPU", "Storage", "Motherboard", "Cooler", "PSU", "Case"],
            "3D Rendering":        ["CPU", "RAM", "GPU", "Storage", "Motherboard", "Cooler", "PSU", "Case"],
            "Programming":         ["CPU", "RAM", "Storage", "GPU", "Motherboard", "Cooler", "PSU", "Case"],
            "AI & Model Training": ["GPU", "RAM", "CPU", "Storage", "Motherboard", "Cooler", "PSU", "Case"],
            "General Use":         ["CPU", "Storage", "RAM", "GPU", "Motherboard", "Cooler", "PSU", "Case"],
        }
        upgrade_order = priority_by_purpose.get(purpose,
            ["GPU", "CPU", "RAM", "Storage", "Motherboard", "Cooler", "PSU", "Case"])

        def _recompute_total():
            t = sum(float(c["price"]) for c in chosen.values())
            if ram_qty == 2: t += float(chosen["RAM"]["price"])
            if extra_storage: t += float(extra_storage["price"])
            return t

        def _fix_motherboard_tier():
            """Swap to the highest-tier compatible board within budget, even if
            it's cheaper. Runs regardless of remaining budget so X870E always
            beats X670E Hero for AM5 builds."""
            current = chosen["Motherboard"]
            current_score = MOTHERBOARD_TIERS.get(current["component_name"], 0)
            current_price = float(current["price"])
            socket = None
            for s in ["AM4", "AM5", "LGA1700", "LGA1200", "LGA4677", "sTR5"]:
                if s in (current.get("compatibility_info") or ""):
                    socket = s; break
            t = _recompute_total()
            room = hard_cap - t
            # A board is affordable if its price <= current + room
            best = current
            best_score = current_score
            for cand in by_type["Motherboard"]:
                if socket and socket not in (cand.get("compatibility_info") or ""):
                    continue
                cand_score = MOTHERBOARD_TIERS.get(cand["component_name"], 0)
                if cand_score <= best_score:
                    continue
                if float(cand["price"]) > current_price + room:
                    continue
                test = dict(chosen); test["Motherboard"] = cand
                if check_compatibility(test):
                    best = cand
                    best_score = cand_score
            if best is not current:
                chosen["Motherboard"] = best

        def _try_upgrade(ctype):
            t = _recompute_total()
            if t >= hard_cap:
                return False
            current_comp = chosen[ctype]
            current_price = float(current_comp["price"])
            remaining_room = hard_cap - t
            max_allowable_price = current_price + remaining_room
            if ctype == "RAM" and ram_qty == 2:
                max_allowable_price = current_price + (remaining_room / 2)

            if ctype == "RAM":
                filtered = [c for c in by_type[ctype] if ram_filter(c, purpose)] or by_type[ctype]
            elif ctype == "Storage":
                filtered = [c for c in by_type[ctype] if storage_filter(c, purpose)] or by_type[ctype]
            else:
                filtered = by_type[ctype]
            affordable = [c for c in filtered
                          if current_price < float(c["price"]) <= max_allowable_price]
            if not affordable:
                return False

            if ctype in ("CPU", "GPU"):
                tiers = cpu_tiers if ctype == "CPU" else gpu_tiers
                current_score = tiers.get(current_comp["component_name"], 0)
                # ONLY consider candidates that don't drop tier score significantly.
                # This is what prevents Threadripper from replacing a 9950X3D.
                # Threshold: candidate must score at least 95% of current.
                valid = []
                for cand in affordable:
                    if tiers.get(cand["component_name"], 0) < current_score * 0.95:
                        continue
                    test = dict(chosen); test[ctype] = cand
                    if is_balanced(test) and check_compatibility(test):
                        valid.append(cand)
                if not valid:
                    return False
                # Sort by tier score first (descending), then by price (descending).
                valid.sort(key=lambda c: (tiers.get(c["component_name"], 0),
                                          float(c["price"])), reverse=True)
                best = valid[0]
            elif ctype == "Motherboard":
                # Use motherboard tier ranking (X870E > X670E) — newer chipset wins.
                # IMPORTANT: allow swaps to a higher-tier board even if it's CHEAPER
                # (X870E Master $620 should replace X670E Hero $770).
                current_score = MOTHERBOARD_TIERS.get(current_comp["component_name"], 0)
                socket = None
                for s in ["AM4", "AM5", "LGA1700", "LGA1200", "LGA4677", "sTR5"]:
                    if s in (current_comp.get("compatibility_info") or ""):
                        socket = s; break
                valid = []
                for cand in by_type["Motherboard"]:
                    if socket and socket not in (cand.get("compatibility_info") or ""):
                        continue
                    cand_score = MOTHERBOARD_TIERS.get(cand["component_name"], 0)
                    if cand_score <= current_score:
                        continue
                    # Must fit budget (can be cheaper OR pricier, just within cap)
                    if float(cand["price"]) > max_allowable_price:
                        continue
                    test = dict(chosen); test[ctype] = cand
                    if check_compatibility(test):
                        valid.append(cand)
                if not valid:
                    return False
                valid.sort(key=lambda c: (MOTHERBOARD_TIERS.get(c["component_name"], 0),
                                          -float(c["price"])), reverse=True)
                best = valid[0]
            else:
                affordable.sort(key=lambda c: float(c["price"]), reverse=True)
                best = None
                for cand in affordable:
                    test = dict(chosen); test[ctype] = cand
                    if check_compatibility(test):
                        best = cand; break
                if best is None:
                    return False

            chosen[ctype] = best
            if _recompute_total() > hard_cap:
                chosen[ctype] = current_comp
                return False
            return True

        for _pass in range(20):
            any_upgrade = False
            for ctype in upgrade_order:
                if _try_upgrade(ctype):
                    any_upgrade = True
            if not any_upgrade:
                break

        # ---- TRADE-SWAP PASS ----
        # After normal upgrades exhaust, try to "trade" cheap part downgrades
        # to fund a major GPU/CPU upgrade. Example: drop 4TB HDD ($110) and
        # cheaper case to bump GPU from GTX 1660 Super to RX 6600 XT.
        def _try_trade_swap(primary_type):
            """Try to upgrade primary_type by downgrading other parts."""
            current_primary = chosen[primary_type]
            current_price = float(current_primary["price"])
            t = _recompute_total()
            room = hard_cap - t

            tiers = cpu_tiers if primary_type == "CPU" else gpu_tiers if primary_type == "GPU" else None

            # Look at next-tier-up candidates for primary
            candidates = [c for c in by_type[primary_type] if float(c["price"]) > current_price]
            if not candidates:
                return False

            # CRITICAL: for CPU/GPU, require the candidate to be at least as good
            # as the current part for this purpose. Prevents Threadripper sneaking
            # into Gaming builds.
            if tiers:
                current_score = tiers.get(current_primary["component_name"], 0)
                candidates = [c for c in candidates
                              if tiers.get(c["component_name"], 0) >= current_score * 0.95]
                if not candidates:
                    return False

            # Sort candidates: prefer higher tier score, then closer in price
            if tiers:
                candidates.sort(key=lambda c: (-tiers.get(c["component_name"], 0), float(c["price"])))
            else:
                candidates.sort(key=lambda c: float(c["price"]))

            # Try each upgrade and see if we can fund it by downgrading other parts
            for upgrade in candidates[:5]:  # try top 5 candidates
                upgrade_price = float(upgrade["price"])
                price_diff = upgrade_price - current_price
                if price_diff - room > 200:  # too expensive even with trades
                    continue

                needed = price_diff - room  # how much we need to free up
                if needed <= 0:
                    # Should have been caught by _try_upgrade, but just in case
                    continue

                # Find downgrades for non-essential parts to free up `needed` USD
                # Don't touch the primary type, RAM (compat), or Motherboard (compat)
                tradeable = ["Case", "Cooler", "Storage", "PSU"]
                trades = {}  # ctype -> candidate
                freed = 0.0
                for trade_type in tradeable:
                    cur_part = chosen[trade_type]
                    cur_p = float(cur_part["price"])
                    cheaper = [c for c in by_type[trade_type] if float(c["price"]) < cur_p]
                    if not cheaper:
                        continue
                    cheaper.sort(key=lambda c: float(c["price"]), reverse=True)
                    for cand in cheaper:
                        savings = cur_p - float(cand["price"])
                        if freed + savings >= needed:
                            trades[trade_type] = cand
                            freed += savings
                            break
                        # Take this downgrade and look for more savings elsewhere
                        trades[trade_type] = cand
                        freed += savings
                        break
                    if freed >= needed:
                        break

                if freed < needed:
                    continue

                # Apply tentatively and verify
                test_chosen = dict(chosen)
                test_chosen[primary_type] = upgrade
                for tt, cand in trades.items():
                    test_chosen[tt] = cand

                # Check balance + compat
                if primary_type in ("CPU", "GPU"):
                    if not is_balanced(test_chosen):
                        continue
                if not check_compatibility(test_chosen):
                    continue

                # Apply for real
                chosen[primary_type] = upgrade
                for tt, cand in trades.items():
                    chosen[tt] = cand
                if _recompute_total() > hard_cap:
                    # Revert
                    chosen[primary_type] = current_primary
                    return False
                return True
            return False

        # Run trade-swap a few times to chain upgrades
        # Focus on the most important component for the purpose
        primary_focus = "GPU" if purpose in ("Gaming", "Streaming", "Gaming and Streaming",
                                              "AI & Model Training") else "CPU"
        for _ in range(5):
            if not _try_trade_swap(primary_focus):
                break
        # Also try one swap on the secondary
        secondary = "CPU" if primary_focus == "GPU" else "GPU"
        _try_trade_swap(secondary)

        # ---- FINAL "SPEND THE BUDGET" PASS ----
        # If significant budget remains after the balance-aware sweeper, the
        # user paid for max performance — give them the best peripherals their
        # money allows. This upgrades non-CPU/GPU parts ignoring balance rules
        # (since RAM/Storage/Cooler don't affect CPU/GPU ratio).
        def _spend_remaining():
            t = _recompute_total()
            if t >= hard_cap - 5:  # already maxed out
                return
            # Allow up to 8 generous passes to soak up leftover money
            for _ in range(8):
                t = _recompute_total()
                room = hard_cap - t
                if room < 2:
                    return
                upgraded_something = False
                # Order: motherboard first (get to X870E), then RAM, cooling, etc.
                for ctype in ["Motherboard", "RAM", "Cooler", "PSU", "Storage",
                              "Case", "GPU", "CPU"]:
                    t = _recompute_total()
                    room = hard_cap - t
                    if room < 2:
                        break
                    current = chosen[ctype]
                    current_price = float(current["price"])
                    max_p = current_price + room
                    if ctype == "RAM" and ram_qty == 2:
                        max_p = current_price + (room / 2)

                    # Filter
                    if ctype == "RAM":
                        pool = [c for c in by_type[ctype] if ram_filter(c, purpose)] or by_type[ctype]
                    elif ctype == "Storage":
                        pool = [c for c in by_type[ctype] if storage_filter(c, purpose)] or by_type[ctype]
                    else:
                        pool = by_type[ctype]

                    affordable = [c for c in pool
                                  if current_price < float(c["price"]) <= max_p]
                    if not affordable:
                        continue
                    # Pick best upgrade: motherboard uses tier ranking; others by price
                    if ctype == "Motherboard":
                        current_score = MOTHERBOARD_TIERS.get(current["component_name"], 0)
                        # Prefer the highest-TIER board that's compatible and affordable,
                        # even if it's CHEAPER than the current one (newer chipset wins).
                        socket = None
                        for s in ["AM4", "AM5", "LGA1700", "LGA1200", "LGA4677", "sTR5"]:
                            if s in (current.get("compatibility_info") or ""):
                                socket = s; break
                        mb_pool = [c for c in by_type["Motherboard"]
                                   if (socket is None or socket in (c.get("compatibility_info") or ""))
                                   and float(c["price"]) <= current_price + room
                                   and MOTHERBOARD_TIERS.get(c["component_name"], 0) > current_score]
                        if not mb_pool:
                            continue
                        mb_pool.sort(key=lambda c: (MOTHERBOARD_TIERS.get(c["component_name"], 0),
                                                    float(c["price"])), reverse=True)
                        best_mb = mb_pool[0]
                        test = dict(chosen); test["Motherboard"] = best_mb
                        if check_compatibility(test) and _recompute_total() - current_price + float(best_mb["price"]) <= hard_cap:
                            chosen["Motherboard"] = best_mb
                            upgraded_something = True
                        continue
                    swapped = False
                    for cand in affordable:
                        test = dict(chosen); test[ctype] = cand
                        # For CPU/GPU still enforce balance
                        if ctype in ("CPU", "GPU") and not is_balanced(test):
                            continue
                        if not check_compatibility(test):
                            continue
                        chosen[ctype] = cand
                        if _recompute_total() > hard_cap:
                            chosen[ctype] = current
                            continue
                        swapped = True
                        upgraded_something = True
                        break
                    if not swapped:
                        continue
                if not upgraded_something:
                    return

        _spend_remaining()

        # Final: ensure the motherboard is the highest-tier compatible board
        # (X870E beats X670E Hero even though X670E Hero is pricier).
        _fix_motherboard_tier()

        # ---- SPLURGE PASS ----
        # At high budgets, GPU/CPU might be maxed but lots of money left over.
        # Splurge on peripherals: bigger storage, premium cooler, premium PSU,
        # nicer case. Order matters: storage/cooler are most useful upgrades.
        splurge_order = ["Storage", "RAM", "Cooler", "PSU", "Case"]
        for _pass in range(10):
            any_upgrade = False
            for ctype in splurge_order:
                t = _recompute_total()
                if t >= hard_cap - 2:  # essentially full
                    break
                current = chosen[ctype]
                current_price = float(current["price"])
                room = hard_cap - t
                max_price = current_price + room

                # Get candidates respecting filters
                if ctype == "RAM":
                    pool = [c for c in by_type[ctype] if ram_filter(c, purpose)] or by_type[ctype]
                elif ctype == "Storage":
                    pool = [c for c in by_type[ctype] if storage_filter(c, purpose)] or by_type[ctype]
                else:
                    pool = by_type[ctype]
                affordable = [c for c in pool
                              if current_price < float(c["price"]) <= max_price]
                if not affordable:
                    continue
                # Pick the most expensive affordable (true splurge)
                affordable.sort(key=lambda c: float(c["price"]), reverse=True)
                for cand in affordable:
                    test = dict(chosen); test[ctype] = cand
                    if not check_compatibility(test):
                        continue
                    chosen[ctype] = cand
                    if _recompute_total() > hard_cap:
                        chosen[ctype] = current
                        continue
                    any_upgrade = True
                    break
            if not any_upgrade:
                break

        # ---- SECOND RAM KIT splurge ----
        # If we still have money left and RAM is high-end already, add a 2nd kit (qty=2)
        if ram_qty == 1:
            t = _recompute_total()
            room = hard_cap - t
            current_ram_price = float(chosen["RAM"]["price"])
            if room >= current_ram_price and float(chosen["RAM"]["price"]) >= 100:
                # Adding a second kit fits — bump qty
                ram_qty = 2

        # ---- ADD secondary HDD if room ----
        if not extra_storage:
            t = _recompute_total()
            room = hard_cap - t
            if room >= 50:  # at least $50 spare
                hdds = [c for c in by_type.get("Storage", [])
                        if "HDD" in (c["specifications"] or "")
                        and c["component_id"] != chosen["Storage"]["component_id"]
                        and float(c["price"]) <= room]
                if hdds:
                    # Pick the biggest HDD that fits
                    hdds.sort(key=lambda c: float(c["price"]), reverse=True)
                    extra_storage = hdds[0]

        # FINAL motherboard tier fix — after all splurge passes, ensure the
        # highest-tier compatible board is selected (X870E beats X670E Hero).
        _fix_motherboard_tier()

    # ---- Final downgrade loop ----
    total = sum(float(c["price"]) for c in chosen.values())
    if ram_qty == 2:
        total += float(chosen["RAM"]["price"])
    if extra_storage:
        total += float(extra_storage["price"])

    max_iterations = 30
    while total > hard_cap and max_iterations > 0:
        max_iterations -= 1
        ctype_to_downgrade = max(chosen.keys(), key=lambda k: float(chosen[k]["price"]))
        current = chosen[ctype_to_downgrade]
        cheaper = [c for c in by_type[ctype_to_downgrade] if float(c["price"]) < float(current["price"])]
        if not cheaper:
            break
        cheaper.sort(key=lambda c: float(c["price"]), reverse=True)
        swapped = False
        for candidate in cheaper:
            test_chosen = dict(chosen); test_chosen[ctype_to_downgrade] = candidate
            if check_compatibility(test_chosen):
                chosen[ctype_to_downgrade] = candidate; swapped = True; break
        if not swapped:
            break
        total = sum(float(c["price"]) for c in chosen.values())
        if ram_qty == 2: total += float(chosen["RAM"]["price"])
        if extra_storage: total += float(extra_storage["price"])

    if total > hard_cap and extra_storage:
        total -= float(extra_storage["price"])
        extra_storage = None

    # ---- AGGRESSIVE final enforcement ----
    # The loop above only downgrades the single most-expensive part and stops
    # as soon as one type has nothing cheaper. If we're STILL over budget,
    # sweep every component type repeatedly, downgrading wherever possible,
    # ignoring the balance rules (staying under budget matters more than
    # perfect GPU/CPU ratios when money is tight).
    def _calc_total():
        t = sum(float(c["price"]) for c in chosen.values())
        if ram_qty == 2: t += float(chosen["RAM"]["price"])
        if extra_storage: t += float(extra_storage["price"])
        return t

    sweep_iterations = 60
    while total > hard_cap and sweep_iterations > 0:
        sweep_iterations -= 1
        # Find the single best downgrade across ALL types that keeps
        # compatibility and reduces total the most without breaking it.
        best_swap = None      # (new_total, ctype, candidate)
        for ctype in chosen:
            current = chosen[ctype]
            cur_price = float(current["price"])
            cheaper = [c for c in by_type[ctype] if float(c["price"]) < cur_price]
            if not cheaper:
                continue
            # Take the most expensive cheaper option that's compatible
            cheaper.sort(key=lambda c: float(c["price"]), reverse=True)
            for cand in cheaper:
                test = dict(chosen); test[ctype] = cand
                if check_compatibility(test):
                    new_total = total - cur_price + float(cand["price"])
                    # Prefer the swap that lands us closest to (but under) cap
                    if best_swap is None or new_total < best_swap[0]:
                        best_swap = (new_total, ctype, cand)
                    break
        if best_swap is None:
            break  # nothing left to downgrade anywhere
        _, ctype, cand = best_swap
        chosen[ctype] = cand
        total = _calc_total()

    # Last resort: if STILL over budget, drop RAM second-kit / extra storage
    if total > hard_cap and ram_qty == 2:
        ram_qty = 1
        total = _calc_total()
    if total > hard_cap and extra_storage:
        extra_storage = None
        total = _calc_total()

    return {
        "components": chosen,
        "ram_qty": ram_qty,
        "extra_storage": extra_storage,
        "total_cost": round(total, 2),
        "over_budget": total > hard_cap,   # flag so caller knows
    }


def generate_recommendations(conn, request_id, budget, purpose, build_preference="Balanced"):
    cur = conn.cursor(dictionary=True)
    by_type = fetch_components_by_type(cur)
    cur.close()

    n_builds = 2 if random.random() < 0.3 else 1
    created_ids = []

    cur = conn.cursor()
    for _ in range(n_builds):
        build = build_one_recommendation(by_type, budget, purpose, build_preference)
        if not build:
            continue

        rec_date = date.today()
        cur.execute("""
            INSERT INTO Recommended_Build (total_cost, recommendation_date, request_id)
            VALUES (%s, %s, %s)
        """, (build["total_cost"], rec_date, request_id))
        build_id = cur.lastrowid
        created_ids.append(build_id)

        for ctype, comp in build["components"].items():
            qty = build["ram_qty"] if ctype == "RAM" else 1
            cur.execute("""
                INSERT INTO Build_Component (quantity, build_id, component_id)
                VALUES (%s, %s, %s)
            """, (qty, build_id, comp["component_id"]))

        if build["extra_storage"]:
            try:
                cur.execute("""
                    INSERT INTO Build_Component (quantity, build_id, component_id)
                    VALUES (%s, %s, %s)
                """, (1, build_id, build["extra_storage"]["component_id"]))
            except Exception:
                pass

    conn.commit()
    cur.close()
    return created_ids

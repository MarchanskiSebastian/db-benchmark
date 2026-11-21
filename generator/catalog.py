"""Reference data and per-category product templates for the computer parts store.

Model tables approximate real products and launch prices (USD) so names, specs and prices
look plausible; each generated product is one template plus random variant choices.
"""

CATEGORIES = [
    "CPU", "GPU", "Motherboard", "RAM", "SSD", "HDD", "PSU",
    "Case", "Cooler", "Monitor", "Laptop", "Keyboard", "Mouse", "Headset",
]

SKU_PREFIX = {
    "CPU": "CPU", "GPU": "GPU", "Motherboard": "MB", "RAM": "RAM", "SSD": "SSD", "HDD": "HDD",
    "PSU": "PSU", "Case": "CASE", "Cooler": "COOL", "Monitor": "MON", "Laptop": "LAP",
    "Keyboard": "KB", "Mouse": "MOU", "Headset": "HS",
}

BRANDS = {
    "AMD": "US", "Intel": "US", "NVIDIA": "US", "ASUS": "TW", "MSI": "TW", "Gigabyte": "TW",
    "ASRock": "TW", "Zotac": "HK", "Sapphire": "HK", "PowerColor": "TW", "XFX": "US",
    "Corsair": "US", "Kingston": "US", "G.Skill": "TW", "Crucial": "US", "TeamGroup": "TW",
    "Samsung": "KR", "Western Digital": "US", "Seagate": "US", "Toshiba": "JP",
    "Seasonic": "TW", "be quiet!": "DE", "Cooler Master": "TW", "Fractal Design": "SE",
    "NZXT": "US", "Lian Li": "TW", "Noctua": "AT", "Arctic": "CH", "Dell": "US", "LG": "KR",
    "AOC": "TW", "BenQ": "TW", "Lenovo": "CN", "HP": "US", "Acer": "TW", "Apple": "US",
    "Logitech": "CH", "Razer": "US", "SteelSeries": "DK", "HyperX": "US", "Sennheiser": "DE",
    "Glorious": "US",
}

SOCKET_MEMORY = {
    "AM4": ("DDR4",), "AM5": ("DDR5",), "LGA1200": ("DDR4",),
    "LGA1700": ("DDR4", "DDR5"), "LGA1851": ("DDR5",),
}

CPUS = [
    # brand, model, cores, threads, base GHz, boost GHz, socket, TDP W, USD
    ("AMD", "Ryzen 5 5600", 6, 12, 3.5, 4.4, "AM4", 65, 129),
    ("AMD", "Ryzen 7 5800X3D", 8, 16, 3.4, 4.5, "AM4", 105, 299),
    ("AMD", "Ryzen 9 5900X", 12, 24, 3.7, 4.8, "AM4", 105, 279),
    ("AMD", "Ryzen 5 7600X", 6, 12, 4.7, 5.3, "AM5", 105, 199),
    ("AMD", "Ryzen 7 7800X3D", 8, 16, 4.2, 5.0, "AM5", 120, 449),
    ("AMD", "Ryzen 7 9700X", 8, 16, 3.8, 5.5, "AM5", 65, 329),
    ("AMD", "Ryzen 9 9950X", 16, 32, 4.3, 5.7, "AM5", 170, 649),
    ("Intel", "Core i5-11400F", 6, 12, 2.6, 4.4, "LGA1200", 65, 119),
    ("Intel", "Core i7-11700K", 8, 16, 3.6, 5.0, "LGA1200", 125, 249),
    ("Intel", "Core i5-12400F", 6, 12, 2.5, 4.4, "LGA1700", 65, 139),
    ("Intel", "Core i5-13600K", 14, 20, 3.5, 5.1, "LGA1700", 125, 289),
    ("Intel", "Core i7-14700K", 20, 28, 3.4, 5.6, "LGA1700", 125, 399),
    ("Intel", "Core i9-14900K", 24, 32, 3.2, 6.0, "LGA1700", 125, 549),
    ("Intel", "Core Ultra 5 245K", 14, 14, 4.2, 5.2, "LGA1851", 125, 309),
    ("Intel", "Core Ultra 9 285K", 24, 24, 3.7, 5.7, "LGA1851", 125, 589),
]

CHIPSETS = [
    # chipset, socket, USD
    ("B550", "AM4", 130), ("X570", "AM4", 210),
    ("B650", "AM5", 170), ("X670E", "AM5", 330), ("B850", "AM5", 200),
    ("B560", "LGA1200", 110), ("Z590", "LGA1200", 180),
    ("B760", "LGA1700", 140), ("Z790", "LGA1700", 260),
    ("B860", "LGA1851", 180), ("Z890", "LGA1851", 310),
]
# Every (chipset, memory type) pair; boards cycle through it so each socket and memory
# type is covered as soon as there are enough motherboards, even in the smallest dataset.
BOARD_VARIANTS = [(c, s, m, usd) for c, s, usd in CHIPSETS for m in SOCKET_MEMORY[s]]
BOARD_SERIES = {
    "ASUS": ["TUF Gaming", "ROG Strix", "Prime"],
    "MSI": ["MAG Tomahawk", "MPG Carbon", "PRO"],
    "Gigabyte": ["Aorus Elite", "Gaming X", "UD"],
    "ASRock": ["Steel Legend", "Pro RS", "Phantom Gaming"],
}
BOARD_FORMS = [("ATX", "", 4, 1.0), ("Micro-ATX", "M", 4, 0.9), ("Mini-ITX", "I", 2, 1.2)]

RAM_LINES = {
    "Corsair": ["Vengeance", "Vengeance RGB", "Dominator Platinum"],
    "Kingston": ["Fury Beast", "Fury Renegade"],
    "G.Skill": ["Ripjaws", "Trident Z5"],
    "Crucial": ["Pro"],
    "TeamGroup": ["T-Force Delta"],
}
RAM_SPEEDS = {"DDR4": [(3200, 16), (3600, 18)], "DDR5": [(5600, 36), (6000, 30), (6400, 32)]}
RAM_USD_PER_GB = {"DDR4": 2.2, "DDR5": 3.0}

GPUS = [
    # vendor, chipset, VRAM GB, memory type, TDP W, USD
    ("NVIDIA", "GeForce RTX 4060", 8, "GDDR6", 115, 299),
    ("NVIDIA", "GeForce RTX 4060 Ti", 16, "GDDR6", 165, 449),
    ("NVIDIA", "GeForce RTX 4070 Super", 12, "GDDR6X", 220, 599),
    ("NVIDIA", "GeForce RTX 4080 Super", 16, "GDDR6X", 320, 999),
    ("NVIDIA", "GeForce RTX 4090", 24, "GDDR6X", 450, 1799),
    ("NVIDIA", "GeForce RTX 5070", 12, "GDDR7", 250, 549),
    ("NVIDIA", "GeForce RTX 5080", 16, "GDDR7", 360, 999),
    ("NVIDIA", "GeForce RTX 5090", 32, "GDDR7", 575, 1999),
    ("AMD", "Radeon RX 7600", 8, "GDDR6", 165, 269),
    ("AMD", "Radeon RX 7700 XT", 12, "GDDR6", 245, 419),
    ("AMD", "Radeon RX 7800 XT", 16, "GDDR6", 263, 499),
    ("AMD", "Radeon RX 7900 XTX", 24, "GDDR6", 355, 949),
    ("AMD", "Radeon RX 9070 XT", 16, "GDDR6", 304, 599),
]
GPU_PARTNERS = {
    "NVIDIA": [
        ("ASUS", "TUF Gaming"), ("ASUS", "ROG Strix"), ("MSI", "Ventus 2X"),
        ("MSI", "Gaming X Trio"), ("Gigabyte", "Windforce"), ("Gigabyte", "Aorus Master"),
        ("Zotac", "Twin Edge"), ("NVIDIA", "Founders Edition"),
    ],
    "AMD": [
        ("Sapphire", "Pulse"), ("Sapphire", "Nitro+"), ("PowerColor", "Hellhound"),
        ("PowerColor", "Red Devil"), ("XFX", "Speedster"), ("ASUS", "TUF Gaming"),
        ("Gigabyte", "Gaming OC"),
    ],
}

SSDS = [
    # brand, model, interface, read MB/s, USD per TB
    ("Samsung", "990 PRO", "NVMe PCIe 4.0", 7450, 110),
    ("Samsung", "9100 PRO", "NVMe PCIe 5.0", 14700, 180),
    ("Samsung", "870 EVO", "SATA III", 560, 80),
    ("Western Digital", "Black SN850X", "NVMe PCIe 4.0", 7300, 95),
    ("Western Digital", "Blue SA510", "SATA III", 560, 60),
    ("Crucial", "T705", "NVMe PCIe 5.0", 14500, 170),
    ("Crucial", "P3 Plus", "NVMe PCIe 4.0", 5000, 60),
    ("Crucial", "MX500", "SATA III", 560, 65),
    ("Kingston", "KC3000", "NVMe PCIe 4.0", 7000, 85),
    ("Kingston", "NV3", "NVMe PCIe 4.0", 6000, 55),
    ("Seagate", "FireCuda 530R", "NVMe PCIe 4.0", 7300, 100),
]
SSD_CAPACITIES = [500, 1000, 2000, 4000]

HDDS = [
    # brand, model, rpm, cache MB, USD per TB
    ("Seagate", "BarraCuda", 7200, 256, 22), ("Seagate", "IronWolf", 5400, 256, 28),
    ("Western Digital", "Blue", 5400, 256, 21), ("Western Digital", "Red Plus", 7200, 512, 30),
    ("Toshiba", "P300", 7200, 256, 20), ("Toshiba", "N300", 7200, 512, 27),
]
HDD_CAPACITIES = [2000, 4000, 8000, 12000, 16000]

PSUS = [
    # brand, line, efficiency, modular, USD per 100 W
    ("Corsair", "RM", "80+ Gold", "Full", 14), ("Corsair", "CX", "80+ Bronze", "Semi", 10),
    ("Seasonic", "Focus GX", "80+ Gold", "Full", 15), ("Seasonic", "Prime TX", "80+ Titanium", "Full", 30),
    ("be quiet!", "Pure Power 12 M", "80+ Gold", "Full", 14),
    ("be quiet!", "Dark Power 13", "80+ Titanium", "Full", 28),
    ("Cooler Master", "MWE Gold V2", "80+ Gold", "Full", 12), ("MSI", "MAG A-BN", "80+ Bronze", "No", 9),
]
PSU_WATTAGES = [550, 650, 750, 850, 1000, 1200]

CASES = [
    # brand, model, form factor, USD
    ("Fractal Design", "North", "ATX Mid Tower", 139), ("Fractal Design", "Meshify 2 Compact", "ATX Mid Tower", 119),
    ("Fractal Design", "Pop Air", "ATX Mid Tower", 89), ("NZXT", "H5 Flow", "ATX Mid Tower", 94),
    ("NZXT", "H9 Flow", "ATX Mid Tower", 159), ("Lian Li", "O11 Dynamic EVO", "ATX Mid Tower", 169),
    ("Lian Li", "Lancool 216", "ATX Mid Tower", 99), ("Lian Li", "A3-mATX", "Micro-ATX Tower", 79),
    ("Corsair", "4000D Airflow", "ATX Mid Tower", 104), ("Corsair", "3500X", "ATX Mid Tower", 99),
    ("be quiet!", "Pure Base 500DX", "ATX Mid Tower", 109), ("be quiet!", "Light Base 900", "ATX Full Tower", 249),
    ("Cooler Master", "NR200P", "Mini-ITX", 99),
]

COOLERS = [
    # brand, model, type, radiator mm (0 = air), max TDP W, USD
    ("Noctua", "NH-D15 G2", "Air", 0, 250, 149), ("Noctua", "NH-U12S", "Air", 0, 180, 79),
    ("be quiet!", "Dark Rock Pro 5", "Air", 0, 270, 99), ("be quiet!", "Pure Rock 3", "Air", 0, 190, 45),
    ("Arctic", "Freezer 36", "Air", 0, 200, 39), ("Arctic", "Liquid Freezer III 360", "AIO", 360, 300, 119),
    ("Cooler Master", "Hyper 212", "Air", 0, 180, 30), ("Corsair", "iCUE H150i Elite", "AIO", 360, 300, 199),
    ("NZXT", "Kraken 240", "AIO", 240, 250, 139),
]

MONITOR_SERIES = {
    "Dell": ["Alienware", "S Series", "UltraSharp"], "LG": ["UltraGear", "UltraFine"],
    "Samsung": ["Odyssey G5", "Odyssey G7", "Odyssey OLED G8"], "ASUS": ["TUF Gaming", "ROG Swift", "ProArt"],
    "AOC": ["Gaming", "Agon Pro"], "BenQ": ["Mobiuz", "Zowie XL"],
}
MONITOR_PANELS = [
    # size in, resolution, label, refresh rates, panels, USD
    (24, "1920x1080", "FHD", [144, 165, 240], ["IPS", "VA"], 150),
    (27, "2560x1440", "QHD", [144, 165, 180, 240], ["IPS", "VA", "OLED"], 280),
    (27, "3840x2160", "4K UHD", [60, 144, 160], ["IPS"], 450),
    (32, "3840x2160", "4K UHD", [60, 144, 240], ["IPS", "VA", "OLED"], 600),
    (34, "3440x1440", "UWQHD", [100, 144, 175], ["VA", "OLED"], 550),
]

LAPTOPS = [
    # brand, line, CPUs, GPUs, screen in, USD
    ("Lenovo", "Legion 5", ["Ryzen 7 8845HS", "Core i7-14650HX"], ["GeForce RTX 4060", "GeForce RTX 4070"], 16.0, 1299),
    ("Lenovo", "ThinkPad T14", ["Core Ultra 5 125U", "Ryzen 7 PRO 8840U"], ["Integrated"], 14.0, 1099),
    ("Dell", "XPS 14", ["Core Ultra 7 155H"], ["Integrated", "GeForce RTX 4050"], 14.5, 1599),
    ("Dell", "Inspiron 15", ["Core i5-1335U", "Ryzen 5 7530U"], ["Integrated"], 15.6, 649),
    ("HP", "Omen 16", ["Core i7-14700HX", "Ryzen 9 8945HS"], ["GeForce RTX 4060", "GeForce RTX 4070"], 16.1, 1399),
    ("HP", "Pavilion 15", ["Core i5-1335U"], ["Integrated"], 15.6, 599),
    ("ASUS", "ROG Zephyrus G14", ["Ryzen 9 8945HS"], ["GeForce RTX 4060", "GeForce RTX 4070"], 14.0, 1599),
    ("ASUS", "Zenbook 14 OLED", ["Core Ultra 7 155H"], ["Integrated"], 14.0, 999),
    ("Acer", "Nitro V 15", ["Core i5-13420H", "Ryzen 5 7535HS"], ["GeForce RTX 4050"], 15.6, 799),
    ("Acer", "Swift Go 14", ["Core Ultra 5 125H"], ["Integrated"], 14.0, 799),
    ("MSI", "Katana 15", ["Core i7-13620H"], ["GeForce RTX 4060", "GeForce RTX 4070"], 15.6, 1099),
    ("Apple", "MacBook Air 13", ["M3", "M4"], ["Integrated"], 13.6, 1099),
    ("Apple", "MacBook Pro 14", ["M4 Pro"], ["Integrated"], 14.2, 1999),
]

KEYBOARDS = [
    # brand, model, layout, connection, switches, USD
    ("Logitech", "G915 TKL", "TKL", "Wireless", ["GL Linear", "GL Tactile", "GL Clicky"], 199),
    ("Logitech", "MX Keys S", "Full", "Wireless", ["Scissor"], 109),
    ("Razer", "BlackWidow V4", "Full", "Wired", ["Green Clicky", "Yellow Linear"], 169),
    ("Razer", "Huntsman Mini", "60%", "Wired", ["Optical Linear", "Optical Clicky"], 119),
    ("SteelSeries", "Apex Pro TKL", "TKL", "Wired", ["OmniPoint Hall Effect"], 189),
    ("Corsair", "K70 RGB Pro", "Full", "Wired", ["Cherry MX Red", "Cherry MX Brown", "Cherry MX Speed"], 159),
    ("HyperX", "Alloy Origins 65", "65%", "Wired", ["HyperX Red", "HyperX Aqua"], 89),
]

MICE = [
    # brand, model, DPI, weight g, buttons, connection, USD
    ("Logitech", "G Pro X Superlight 2", 32000, 60, 5, "Wireless", 159),
    ("Logitech", "MX Master 3S", 8000, 141, 7, "Wireless", 99),
    ("Logitech", "G502 X", 25600, 89, 13, "Wired", 79),
    ("Razer", "DeathAdder V3", 30000, 59, 6, "Wired", 69),
    ("Razer", "Viper V3 Pro", 35000, 54, 6, "Wireless", 159),
    ("SteelSeries", "Rival 3", 8500, 77, 6, "Wired", 29),
    ("SteelSeries", "Aerox 5 Wireless", 18000, 74, 9, "Wireless", 139),
    ("Glorious", "Model O 2", 26000, 59, 6, "Wired", 59),
]

HEADSETS = [
    # brand, model, connection, driver mm, microphone, USD
    ("Logitech", "G Pro X 2", "Wireless", 50, True, 249),
    ("Razer", "BlackShark V2 Pro", "Wireless", 50, True, 199),
    ("SteelSeries", "Arctis Nova 7", "Wireless", 40, True, 179),
    ("HyperX", "Cloud III", "Wired", 53, True, 99),
    ("Sennheiser", "HD 560S", "Wired", 38, False, 169),
]

PERIPHERAL_COLORS = ["Black", "White"]


def _cpu(rng, _):
    brand, model, cores, threads, base, boost, socket, tdp, usd = rng.choice(CPUS)
    packaging = rng.choice(["Box", "Tray"])
    specs = {
        "cores": cores, "threads": threads, "socket": socket, "base_clock_ghz": base,
        "boost_clock_ghz": boost, "tdp_w": tdp, "packaging": packaging,
    }
    return brand, f"{brand} {model} {packaging}", specs, usd * (0.95 if packaging == "Tray" else 1)


def _gpu(rng, _):
    vendor, chipset, vram, mem, tdp, usd = rng.choice(GPUS)
    brand, series = rng.choice(GPU_PARTNERS[vendor])
    specs = {
        "chipset": chipset, "gpu_vendor": vendor, "vram_gb": vram, "memory_type": mem,
        "tdp_w": tdp, "length_mm": rng.randrange(240, 360, 5),
    }
    premium = 1.15 if series in ("ROG Strix", "Aorus Master", "Gaming X Trio", "Nitro+", "Red Devil") else 1
    return brand, f"{brand} {chipset} {series} {vram}GB", specs, usd * premium


def _motherboard(rng, index):
    chipset, socket, mem, usd = BOARD_VARIANTS[index % len(BOARD_VARIANTS)]
    brand = rng.choice(list(BOARD_SERIES))
    series = rng.choice(BOARD_SERIES[brand])
    form, suffix, slots, factor = rng.choice(BOARD_FORMS)
    ddr_suffix = f" {mem}" if len(SOCKET_MEMORY[socket]) > 1 else ""
    specs = {
        "socket": socket, "chipset": chipset, "form_factor": form,
        "memory_type": mem, "memory_slots": slots,
    }
    return brand, f"{brand} {series} {chipset}{suffix}{ddr_suffix}", specs, usd * factor


def _ram(rng, _):
    brand = rng.choice(list(RAM_LINES))
    line = rng.choice(RAM_LINES[brand])
    mem = rng.choice(list(RAM_SPEEDS))
    speed, cl = rng.choice(RAM_SPEEDS[mem])
    capacity = rng.choice([16, 32, 64])
    specs = {
        "memory_type": mem, "capacity_gb": capacity, "modules": 2,
        "speed_mhz": speed, "cas_latency": cl,
    }
    name = f"{brand} {line} {capacity}GB (2x{capacity // 2}GB) {mem}-{speed} CL{cl}"
    return brand, name, specs, capacity * RAM_USD_PER_GB[mem] + 10


def _capacity_label(gb):
    return f"{gb // 1000}TB" if gb >= 1000 else f"{gb}GB"


def _ssd(rng, _):
    brand, model, interface, read, usd_tb = rng.choice(SSDS)
    capacity = rng.choice(SSD_CAPACITIES)
    form = "2.5-inch" if interface == "SATA III" else "M.2 2280"
    specs = {"capacity_gb": capacity, "interface": interface, "form_factor": form, "read_mbps": read}
    return brand, f"{brand} {model} {_capacity_label(capacity)}", specs, usd_tb * capacity / 1000 + 25


def _hdd(rng, _):
    brand, model, rpm, cache, usd_tb = rng.choice(HDDS)
    capacity = rng.choice(HDD_CAPACITIES)
    specs = {
        "capacity_gb": capacity, "rpm": rpm, "cache_mb": cache,
        "interface": "SATA III", "form_factor": "3.5-inch",
    }
    return brand, f"{brand} {model} {_capacity_label(capacity)} {rpm} RPM", specs, usd_tb * capacity / 1000 + 30


def _psu(rng, _):
    brand, line, efficiency, modular, usd_100w = rng.choice(PSUS)
    watts = rng.choice(PSU_WATTAGES)
    specs = {"wattage_w": watts, "efficiency": efficiency, "modular": modular}
    return brand, f"{brand} {line} {watts}W {efficiency}", specs, usd_100w * watts / 100


def _case(rng, _):
    brand, model, form, usd = rng.choice(CASES)
    color = rng.choice(PERIPHERAL_COLORS)
    specs = {
        "form_factor": form, "color": color, "fans_included": rng.randint(1, 4),
        "tempered_glass": rng.random() < 0.7,
    }
    return brand, f"{brand} {model} {color}", specs, usd


def _cooler(rng, _):
    brand, model, kind, radiator, tdp, usd = rng.choice(COOLERS)
    color = rng.choice(PERIPHERAL_COLORS)
    specs = {"cooler_type": kind, "max_tdp_w": tdp, "supported_sockets": ",".join(SOCKET_MEMORY), "color": color}
    if radiator:
        specs["radiator_mm"] = radiator
    return brand, f"{brand} {model} {color}", specs, usd


def _monitor(rng, _):
    brand = rng.choice(list(MONITOR_SERIES))
    series = rng.choice(MONITOR_SERIES[brand])
    size, resolution, label, rates, panels, usd = rng.choice(MONITOR_PANELS)
    hz = rng.choice(rates)
    panel = rng.choice(panels)
    specs = {
        "size_in": float(size), "resolution": resolution, "refresh_hz": hz,
        "panel": panel, "response_ms": 0.03 if panel == "OLED" else 1.0,
    }
    price = usd * (1.8 if panel == "OLED" else 1) * (1 + (hz - 60) / 400)
    return brand, f'{brand} {series} {size}" {label} {hz}Hz {panel}', specs, price


def _laptop(rng, _):
    brand, line, cpus, gpus, screen, usd = rng.choice(LAPTOPS)
    cpu = rng.choice(cpus)
    gpu = rng.choice(gpus)
    ram = rng.choice([8, 16, 32])
    storage = rng.choice([512, 1000, 2000])
    specs = {"cpu": cpu, "gpu": gpu, "ram_gb": ram, "storage_gb": storage, "screen_in": screen}
    gpu_part = "" if gpu == "Integrated" else f" {gpu}"
    name = f"{brand} {line} {cpu}{gpu_part} {ram}GB/{_capacity_label(storage)}"
    return brand, name, specs, usd + (ram - 16) * 8 + (storage - 512) * 0.1


def _keyboard(rng, _):
    brand, model, layout, connection, switches, usd = rng.choice(KEYBOARDS)
    switch = rng.choice(switches)
    color = rng.choice(PERIPHERAL_COLORS)
    specs = {"layout": layout, "switch_type": switch, "connection": connection, "color": color}
    return brand, f"{brand} {model} {switch} {color}", specs, usd


def _mouse(rng, _):
    brand, model, dpi, weight, buttons, connection, usd = rng.choice(MICE)
    color = rng.choice(PERIPHERAL_COLORS)
    specs = {"dpi": dpi, "weight_g": weight, "buttons": buttons, "connection": connection, "color": color}
    return brand, f"{brand} {model} {color}", specs, usd


def _headset(rng, _):
    brand, model, connection, driver, mic, usd = rng.choice(HEADSETS)
    color = rng.choice(PERIPHERAL_COLORS)
    specs = {"connection": connection, "driver_mm": driver, "microphone": mic, "color": color}
    return brand, f"{brand} {model} {color}", specs, usd


TEMPLATES = {
    "CPU": _cpu, "GPU": _gpu, "Motherboard": _motherboard, "RAM": _ram, "SSD": _ssd,
    "HDD": _hdd, "PSU": _psu, "Case": _case, "Cooler": _cooler, "Monitor": _monitor,
    "Laptop": _laptop, "Keyboard": _keyboard, "Mouse": _mouse, "Headset": _headset,
}


def make_product(category, rng, index):
    """Return (brand, name, specs, price_cents) for the index-th product of a category."""
    brand, name, specs, usd = TEMPLATES[category](rng, index)
    dollars = max(int(usd * rng.uniform(0.9, 1.15)), 5)
    return brand, name, specs, dollars * 100 - 1

"""
Management command: seed 150 products across all 5 categories with real Unsplash image URLs.

Usage:
    python manage.py seed_products           # add if < 150 exist
    python manage.py seed_products --clear   # wipe & re-seed
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from inventory.models import Product
from accounts.models import User
import random

# ──────────────────────────────────────────────────────────────────────────────
# 30 products per category  ×  5 categories  =  150 total
# Images come from Unsplash (free, no auth required, deterministic URLs)
# ──────────────────────────────────────────────────────────────────────────────

PRODUCTS = {
    "electronics": [
        ("4K Smart TV 65\"",         "🖥️", 89999,  45, "Quantum dot display, HDR10+, built-in AI upscaling",       "https://images.unsplash.com/photo-1593359677879-a4bb92f4e8f?w=400"),
        ("Gaming Laptop Pro",        "💻", 129999, 20, "RTX 4070, 32GB RAM, 1TB NVMe, 240Hz display",              "https://images.unsplash.com/photo-1525547719571-a2d4ac8945e2?w=400"),
        ("Mechanical Keyboard RGB",  "⌨️", 12999,  80, "Cherry MX Red switches, per-key RGB, aluminium frame",     "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=400"),
        ("Wireless Earbuds Pro",     "🎧", 18999,  60, "ANC, 40hr battery, Hi-Res audio certification",            "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=400"),
        ("Portable SSD 2TB",         "💾", 14999, 100, "USB 3.2 Gen2, 2000 MB/s read, military-grade shock proof", "https://images.unsplash.com/photo-1618424181497-157f25b6ddd5?w=400"),
        ("DSLR Camera Body",         "📷", 74999,  15, "45MP full-frame sensor, 8K video, dual CFexpress slots",   "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=400"),
        ("Curved Gaming Monitor",    "🖥️", 45999,  25, "34\" 3440×1440, 165Hz, 1ms, HDR400",                      "https://images.unsplash.com/photo-1527443224154-c4a573d1b5c2?w=400"),
        ("Smart Home Hub",           "🏠", 8999,   50, "Matter & Thread compatible, controls 200+ devices",        "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400"),
        ("Bluetooth Speaker 360°",   "🔊", 7999,   70, "30W, IP67 waterproof, 24hr battery, PartyBoost",          "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=400"),
        ("USB-C Docking Station",    "🔌", 11999,  55, "14-in-1, 100W PD, 4K×2 HDMI, 10Gbps USB-A",              "https://images.unsplash.com/photo-1591488320449-011701bb6704?w=400"),
        ("Noise-Cancelling Headset", "🎙️", 22999,  35, "ENC mic, 60hr ANC playback, multipoint BT 5.3",           "https://images.unsplash.com/photo-1583394838336-acd977736f90?w=400"),
        ("Action Camera 8K",         "📹", 34999,  30, "8K/30fps, HorizonSteady Pro, 10m waterproof",              "https://images.unsplash.com/photo-1493119508027-2b584f234d6c?w=400"),
        ("Smart Projector 4K",       "📽️", 69999,  10, "3000 ANSI lumens, Android TV, auto-keystone",             "https://images.unsplash.com/photo-1478720568477-152d9b164e26?w=400"),
        ("NAS Storage 8TB",          "🗄️", 29999,  20, "2-bay RAID, Plex server, 2.5GbE, M.2 cache",             "https://images.unsplash.com/photo-1600267185393-1b14dbc9a096?w=400"),
        ("E-Ink Tablet 10.3\"",      "📱", 39999,  25, "E-paper display, 4096 pressure levels, 4 weeks battery",  "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=400"),
        ("Wi-Fi 7 Mesh Router",      "📡", 24999,  40, "BE19000, tri-band, 12 streams, 2500m² coverage",           "https://images.unsplash.com/photo-1606904825846-647eb07f5be2?w=400"),
        ("Mirrorless Camera Kit",    "📸", 99999,  8,  "50MP, In-body 8-axis OIS, 4K/120fps ProRes",              "https://images.unsplash.com/photo-1502920917128-1aa500764cbd?w=400"),
        ("Smart Thermostat",         "🌡️", 9999,   60, "AI schedule learning, geofencing, HVAC diagnostics",       "https://images.unsplash.com/photo-1558089687-f282ffcbc126?w=400"),
        ("LED Strip Kit 10m",        "💡", 3999,  200, "RGBIC, music sync, 16M colours, Matter compatible",        "https://images.unsplash.com/photo-1567515004624-219c11d31f2e?w=400"),
        ("Wireless Charger 65W",     "⚡", 4999,  120, "MagSafe compatible, multi-device pad, foreign object det.", "https://images.unsplash.com/photo-1591799265444-d66432b91588?w=400"),
        ("Graphic Tablet Pro",       "🖊️", 44999,  18, "16\" 4K OLED pen display, 8192 pressure, 120Hz",          "https://images.unsplash.com/photo-1626379953822-baec19c3accd?w=400"),
        ("Sound Bar Dolby Atmos",    "🔈", 32999,  22, "5.1.2 ch, 500W, eARC, room correction AI",                "https://images.unsplash.com/photo-1545454675-3531b543be5d?w=400"),
        ("Smart Lock Fingerprint",   "🔐", 15999,  45, "Bluetooth, pin, fingerprint, NFC, auto lock",              "https://images.unsplash.com/photo-1558618047-f4e60cde6ef5?w=400"),
        ("Mini PC Intel N100",       "🖥️", 19999,  30, "16GB RAM, 512GB SSD, 4×USB4, triple 4K display",         "https://images.unsplash.com/photo-1587202372634-32705e3bf49c?w=400"),
        ("RGB LED Desk Lamp",        "💡", 4499,  150, "Wireless charging base, 10 colour modes, USB-C port",      "https://images.unsplash.com/photo-1540932239986-30128078f3c5?w=400"),
        ("Security Camera 4K PoE",  "📹", 12999,  55, "AI person/vehicle detect, colour night vision, two-way",   "https://images.unsplash.com/photo-1580894894513-541e068a3e2b?w=400"),
        ("Smart Doorbell",           "🔔", 13999,  40, "2K HDR video, package detection, 180° field of view",      "https://images.unsplash.com/photo-1558089687-db19757c6276?w=400"),
        ("Portable Power Station",   "🔋", 49999,  12, "1000Wh, 2000W AC, LiFePO4, solar-ready, UPS mode",        "https://images.unsplash.com/photo-1594131431833-3e3c35a1c21c?w=400"),
        ("VR Headset All-in-One",    "🥽", 59999,   7, "4K per-eye, 120Hz, inside-out tracking, 128GB",           "https://images.unsplash.com/photo-1626379953797-1ab2a0de75e4?w=400"),
        ("Gaming Capture Card 4K",  "🎮", 17999,  35, "USB-C, 4K60 passthrough, 1080p240 capture, zero latency",  "https://images.unsplash.com/photo-1612287230202-1ff1d85d1bdf?w=400"),
    ],

    "wearables": [
        ("Smart Watch Ultra",        "⌚", 49999,  30, "Titanium case, always-on AMOLED, ECG, crash detection",    "https://images.unsplash.com/photo-1546868871-7041f2a55e12?w=400"),
        ("Fitness Tracker Pro",      "💪", 8999,   80, "Blood glucose, SpO2, 21-day battery, swim-proof 50m",      "https://images.unsplash.com/photo-1575311373937-040b8e1fd5b6?w=400"),
        ("Smart Ring Health",        "💍", 24999,  40, "HRV, skin temp, sleep staging, titanium size 10",          "https://images.unsplash.com/photo-1588776814546-1ffcf47267a5?w=400"),
        ("AR Smart Glasses",         "👓", 79999,  10, "Micro-LED waveguide, 50° FoV, hand tracking, 3hr active",  "https://images.unsplash.com/photo-1616348436168-de43ad0db179?w=400"),
        ("Sports GPS Watch",         "🏃", 34999,  25, "Dual-band GPS, 200hr expedition, VO2 max, trail maps",     "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400"),
        ("Open-Ear Bone Conduction", "🎵", 13999,  60, "IP68, 9hr, directional audio, ideal for cycling",          "https://images.unsplash.com/photo-1625865408780-52ec38b0f01e?w=400"),
        ("Kids Smart Watch 4G",      "👦", 7999,   70, "Video call, SOS, GPS tracking, step counter, 4G SIM",      "https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?w=400"),
        ("ECG Smart Watch",          "❤️", 29999,  20, "Medical-grade ECG, AFib detection, blood pressure cuff",   "https://images.unsplash.com/photo-1434494878577-86c23bcb06b9?w=400"),
        ("Haptic Feedback Gloves",   "🖐️", 44999,  12, "VR haptic feedback, 20 actuators, gesture recognition",    "https://images.unsplash.com/photo-1605296867304-46d5465a13f1?w=400"),
        ("Smart Posture Corrector",  "🧘", 5999,  100, "Vibration feedback, posture score, 7-day training plan",   "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400"),
        ("Noise-Cancel Earbuds",     "🎶", 16999,  55, "Adaptive ANC, 36hr total, Hi-Res wireless, multipoint",    "https://images.unsplash.com/photo-1484704849700-f032a568e944?w=400"),
        ("Smart Sunglasses Audio",   "🕶️", 19999,  35, "Open-ear speakers, UV400, 6hr, IPX4, voice assistant",    "https://images.unsplash.com/photo-1572635196237-14b3f281503f?w=400"),
        ("Running Pod Footpod",      "👟", 8499,   90, "Cadence, stride length, vertical oscillation, BLE/ANT+",   "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400"),
        ("Wrist BP Monitor",         "💉", 11999,  45, "Clinical accuracy, arrhythmia alert, 60-reading memory",   "https://images.unsplash.com/photo-1576091160550-2173dba999ef?w=400"),
        ("Sleep Tracking Band",      "😴", 6999,   85, "Sleep stage AI, snore detect, smart alarm, 21 days",       "https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=400"),
        ("Cycling Smart Helmet",     "🚴", 17999,  20, "Built-in light, brake-detect flash, BT audio, 4hr",        "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400"),
        ("Smartwatch Charger Dock",  "🔌", 2999,  200, "Magnetic wireless, USB-C input, LED indicator",            "https://images.unsplash.com/photo-1612817288484-6f916006741a?w=400"),
        ("Stress Relief Wristband",  "🧠", 9999,   60, "EDA sensor, breathing guide, stress score real-time",      "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400"),
        ("Smart Insole Foot Track",  "👣", 12999,  40, "Pressure mapping, gait analysis, Bluetooth app",           "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400"),
        ("Hybrid Smartwatch",        "⌚", 23999,  30, "Analog hands + hidden display, 45-day battery, NFC pay",   "https://images.unsplash.com/photo-1579586337278-3befd40fd17a?w=400"),
        ("Smart Vest Biometric",     "👕", 31999,  15, "ECG, EMG, posture, 12-lead, washable, sports version",     "https://images.unsplash.com/photo-1558769132-cb1aea458c5e?w=400"),
        ("Hearing Aid Smart",        "👂", 54999,   8, "Bluetooth streaming, app EQ, fall detection, IP68",        "https://images.unsplash.com/photo-1558769132-cb1aea458c5e?w=400"),
        ("Smart Cap UV Monitor",     "🧢", 4499,  120, "UV index, step counter, calories, BLE sync",               "https://images.unsplash.com/photo-1534482421-64566f976cfa?w=400"),
        ("Ankle Rehab Sensor",       "🦵", 18999,  18, "ROM measurement, exercise guidance, therapist app link",   "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400"),
        ("Smart Headband Meditation","🧘", 14999,  35, "EEG brainwave, real-time calm score, guided meditation",   "https://images.unsplash.com/photo-1508387027939-27cccde23525?w=400"),
        ("AR Running Glasses",       "🏅", 42999,  12, "HUD pace/HR/map, 4hr, IPX4, low 26g weight",              "https://images.unsplash.com/photo-1508507779520-8346db95c9e3?w=400"),
        ("Sports Earbuds IP68",      "🎵", 9999,   75, "Secure fin fit, 10hr, IP68, ambient mode, ultra fast chg", "https://images.unsplash.com/photo-1484704849700-f032a568e944?w=400"),
        ("Smart Necklace Jewellery", "💎", 22999,  20, "SOS alert, step tracker, sapphire glass, 7-day battery",  "https://images.unsplash.com/photo-1515562141207-7a88fb7ce338?w=400"),
        ("Posture Trainer Clip",     "📌", 3999,  150, "Discreet clip, 200 posture events, vibration nudge",       "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400"),
        ("Smart Water Bottle",       "💧", 5999,   90, "Hydration tracking, glowing reminder, BLE sync, 1L",       "https://images.unsplash.com/photo-1602143407151-7111542de6e8?w=400"),
    ],

    "drones": [
        ("Foldable 4K Drone Pro",    "🚁", 89999,  15, "4K/60fps, 3-axis gimbal, 40min, 15km link, auto-return",  "https://images.unsplash.com/photo-1473968512647-3e447244af8f?w=400"),
        ("Mini Nano Drone 250g",     "🚁", 24999,  40, "Sub-250g, 4K, 31min, follow-me, QuickShots",              "https://images.unsplash.com/photo-1579829366248-204fe8413f31?w=400"),
        ("FPV Racing Drone Kit",     "🏎️", 44999,  20, "6S, 120mph top speed, DJI O3 link, DIY build kit",        "https://images.unsplash.com/photo-1549480017-d76466a4b7e8?w=400"),
        ("Agricultural Spray Drone", "🌾", 249999,  5, "20L tank, 10 acres/hr, RTK precision, obstacle avoidance", "https://images.unsplash.com/photo-1508614999368-9260051292e5?w=400"),
        ("Underwater ROV 4K",        "🤿", 59999,   8, "100m depth, 4K cam, 6-thruster, sonar, 4hr dive",         "https://images.unsplash.com/photo-1564419320461-6870880221ad?w=400"),
        ("Cinema Drone Octocopter",  "🎬", 399999,  3, "35kg payload, 8K Cinematic, 25min loaded flight",         "https://images.unsplash.com/photo-1516192518150-0d8fee5425e3?w=400"),
        ("Mapping Survey Drone",     "📐", 149999,  6, "RTK/PPK, 20MP cam, 45min, generates orthomosaic maps",    "https://images.unsplash.com/photo-1508614999368-9260051292e5?w=400"),
        ("Indoor Mini Drone",        "🐝", 5999,  100, "Palm-size, prop guards, altitude hold, 360 flips, gift",  "https://images.unsplash.com/photo-1579829366248-204fe8413f31?w=400"),
        ("Search & Rescue Drone",    "🆘", 199999,  4, "Thermal + 4K cam, 60min, 5km link, 12-propeller redundancy","https://images.unsplash.com/photo-1473968512647-3e447244af8f?w=400"),
        ("Delivery Cargo Drone",     "📦", 299999,  3, "10kg payload, 30km range, BVLOS ready, VTOL wing hybrid", "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400"),
        ("FPV Goggles V3",           "🥽", 34999,  25, "1080p OLED, 110° FoV, 120fps, 52ms latency, DVR record",  "https://images.unsplash.com/photo-1626379953797-1ab2a0de75e4?w=400"),
        ("Drone Backpack Case",      "🎒", 6999,   60, "Waterproof shell, fits 4 rotors + remote, TSA-approved",  "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400"),
        ("Drone Propeller Guard Set","🛡️", 1499,  300, "Carbon fibre reinforced guards, universal 5-inch fit",    "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400"),
        ("Long Range Fixed Wing",    "✈️", 179999,  5, "VTOL, 3hr endurance, 60km link, 1:10 glide ratio",        "https://images.unsplash.com/photo-1474302770737-173ee21bab63?w=400"),
        ("Swarm Drone Starter Pack", "🐝", 89999,   8, "5-drone swarm, light show SDK, indoor GPS mesh, 20min",   "https://images.unsplash.com/photo-1579829366248-204fe8413f31?w=400"),
        ("Racing Gate Obstacle Set", "🎯", 12999,  30, "LED gate set of 8, foldable, UV-resistant, 3m diameter",  "https://images.unsplash.com/photo-1557862921-37829c790f19?w=400"),
        ("Gimbal 3-Axis 1kg",        "📷", 19999,  22, "Max 1kg payload, 32-bit, 0.01° stabilisation, follow mode","https://images.unsplash.com/photo-1502920917128-1aa500764cbd?w=400"),
        ("Smart Battery 6000mAh",    "🔋", 9999,   80, "LiHV cells, self-heating -20°C, auto-discharge, 200 cycles","https://images.unsplash.com/photo-1594131431833-3e3c35a1c21c?w=400"),
        ("Drone Solar Charger",      "☀️", 14999,  25, "120W foldable panel, dual XT60 output, MPPT, field use",  "https://images.unsplash.com/photo-1509391366360-2e959784a276?w=400"),
        ("Night Vision Drone Cam",   "🌙", 29999,  18, "STARVIS 2 sensor, f/1.6, 0.0001 lux, 4K night colour",   "https://images.unsplash.com/photo-1516192518150-0d8fee5425e3?w=400"),
        ("Parachute Recovery Sys",   "🪂", 8999,   40, "Auto-deploy on crash detect, 2kg drone max, repackable",  "https://images.unsplash.com/photo-1518611012118-696072aa579a?w=400"),
        ("Tethered Power Drone",     "⚡", 129999,  6, "Unlimited flight via ground power, 300m tether, 5kg payload","https://images.unsplash.com/photo-1473968512647-3e447244af8f?w=400"),
        ("Dual-Operator Drone",      "👥", 99999,   4, "Pilot + camera-op dual remote, 6km HD link, 40min",       "https://images.unsplash.com/photo-1516192518150-0d8fee5425e3?w=400"),
        ("Micro FPV Whoop 65mm",     "🐝", 8499,   50, "1S 65mm frame, digital VTX optional, 4min race-tuned",    "https://images.unsplash.com/photo-1579829366248-204fe8413f31?w=400"),
        ("Wind-Resistant Drone",     "💨", 74999,  10, "Level 7 wind resistance, 45min, dual gimbal EO+IR",       "https://images.unsplash.com/photo-1473968512647-3e447244af8f?w=400"),
        ("Drone Controller Sim",     "🕹️", 11999,  35, "USB hall-effect sticks, works with DJI Simulator, ACRRO", "https://images.unsplash.com/photo-1612287230202-1ff1d85d1bdf?w=400"),
        ("Aerial Photography Kit",   "📸", 54999,  12, "Drone + ND filter set + lens + carrying case bundle",     "https://images.unsplash.com/photo-1502920917128-1aa500764cbd?w=400"),
        ("Hydrogen Fuel Cell Drone", "⚗️", 349999,  2, "2hr endurance, 6kg payload, zero-emission, 15L H2 tank",  "https://images.unsplash.com/photo-1473968512647-3e447244af8f?w=400"),
        ("Kids Beginner Drone",      "🎈", 3999,  120, "One-key fly, auto-hover, prop guards, 3 batteries, WiFi cam","https://images.unsplash.com/photo-1579829366248-204fe8413f31?w=400"),
        ("Thermal Inspection Drone", "🌡️", 189999,  4, "Radiometric FLIR, 640×512 thermal, AI hot-spot detect",   "https://images.unsplash.com/photo-1516192518150-0d8fee5425e3?w=400"),
    ],

    "home": [
        ("Robot Vacuum Mop Combo",   "🤖", 39999,  30, "LiDAR mapping, 6500Pa suction, self-empty 60-day base",   "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400"),
        ("Air Purifier HEPA 13",     "💨", 24999,  45, "CADR 600 m³/hr, covers 80m², PM0.1 detection",            "https://images.unsplash.com/photo-1585771724684-38269d6639fd?w=400"),
        ("Smart Coffee Maker",       "☕", 19999,  40, "Brew by voice, schedule, PID 93°C, 12-cup carafe, grinder","https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=400"),
        ("Inverter Microwave 30L",   "🍲", 14999,  55, "900W, convection+grill combo, 10 auto-cook menus",        "https://images.unsplash.com/photo-1574269909862-7e1d70bb8078?w=400"),
        ("Smart Air Conditioner",    "❄️", 54999,  20, "5-star inverter, Alexa+Google, self-cleaning, 1.5T split", "https://images.unsplash.com/photo-1585771724684-38269d6639fd?w=400"),
        ("Instant Pot 8L",           "🍛", 12999,  65, "Pressure, slow, air-fry, sous-vide, 13-in-1 functions",   "https://images.unsplash.com/photo-1585771724684-38269d6639fd?w=400"),
        ("Smart Refrigerator 600L",  "🧊", 129999, 10, "InstaView door, craft ice, meal plan screen, AI cool",    "https://images.unsplash.com/photo-1584568694244-14fbdf83bd30?w=400"),
        ("Cordless Vacuum 200AW",    "🧹", 29999,  35, "200AW suction, 90min, anti-tangle head, HEPA, 1.4kg",     "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400"),
        ("Water Purifier RO+UV",     "💧", 18999,  50, "RO+UV+UF+TDS controller, 12LPH, 8L storage tank",        "https://images.unsplash.com/photo-1563729784474-d77dbb933a9e?w=400"),
        ("Smart Washing Machine 8kg","🫧", 44999,  18, "AI dirt sensing, steam, 15min quick wash, 5-star",        "https://images.unsplash.com/photo-1582735689369-4fe89db7114c?w=400"),
        ("Standing Desk Electric",   "💼", 34999,  22, "Dual motor, 3 memory, cable management, 150cm width",     "https://images.unsplash.com/photo-1593642632559-0c6d3fc62b89?w=400"),
        ("Ergonomic Office Chair",   "🪑", 29999,  25, "Lumbar+headrest adjustable, mesh back, 4D armrests, 150kg","https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=400"),
        ("Smart Bed Frame King",     "🛏️", 89999,  8,  "Adjustable base, under-bed LED, USB-A/C, zero-gravity pos","https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?w=400"),
        ("Air Fryer 6L XXL",         "🍟", 9999,   80, "1800W, 9 presets, dishwasher-safe basket, rapid air",     "https://images.unsplash.com/photo-1585771724684-38269d6639fd?w=400"),
        ("Smart Ceiling Fan 52\"",   "🌀", 16999,  30, "DC motor, 6 speeds, app+voice, reversible, 35W",          "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400"),
        ("Induction Cooktop 3-zone", "🔥", 22999,  28, "3×3kW zones, bridge zone, boost 3.6kW, 17 power levels",  "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=400"),
        ("Smart Home Security Kit",  "🔒", 34999,  15, "4×cam, base, 3×sensor, 2×motion, 1yr cloud plan",        "https://images.unsplash.com/photo-1580894894513-541e068a3e2b?w=400"),
        ("Mattress Memory Foam 6\"", "😴", 19999,  20, "7-zone, cooling gel, medium-firm, CertiPUR certified",    "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?w=400"),
        ("Smart Garden Indoor",      "🌿", 12999,  45, "LED grow light, self-watering, 12 pods, app control",     "https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=400"),
        ("Bathroom Smart Mirror",    "🪞", 24999,  12, "4K display, defogging, motion sensor, temp/time overlay",  "https://images.unsplash.com/photo-1552321554-5fefe8c9ef14?w=400"),
        ("Dishwasher 14 Place",      "🍽️", 42999,  10, "15L/cycle, half-load, hygiene 70°C, delay start",         "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=400"),
        ("Smart Smoke Detector",     "🚨", 4999,  100, "10yr battery, CO+smoke, app alert, voice alert",           "https://images.unsplash.com/photo-1558089687-f282ffcbc126?w=400"),
        ("Heated Electric Blanket",  "🔥", 5999,   90, "Dual control, 10 heat levels, auto-off 12hr, washable",   "https://images.unsplash.com/photo-1564430489930-7f9e58c4de6a?w=400"),
        ("Smart Sofa Recliner",      "🛋️", 74999,   6, "USB ports, cup holder, heat+massage, USB-C, sectional",   "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=400"),
        ("4K Doorbell Intercom",     "📹", 16999,  35, "2K indoor screen, 3-way call, auto-record, door unlock",  "https://images.unsplash.com/photo-1558089687-db19757c6276?w=400"),
        ("Window Smart Blind",       "🌄", 11999,  40, "Solar powered, schedule, voice, app, noise reduction",     "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=400"),
        ("Digital Photo Frame 15\"", "🖼️", 13999,  50, "Cloud sync, facial recognition albums, 2K IPS, ambient",  "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400"),
        ("Portable AC 1-ton",        "❄️", 36999,  14, "No install, dehumidify, 3-in-1, 12hr timer, R290 eco gas", "https://images.unsplash.com/photo-1585771724684-38269d6639fd?w=400"),
        ("Smart Garage Door Opener", "🚗", 14999,  30, "MYQ app, tilt+laser parking, package delivery guard",     "https://images.unsplash.com/photo-1606904825846-647eb07f5be2?w=400"),
        ("UV Sanitiser Box Large",   "🧼", 7999,   70, "Phone, keys, toys, 10min UV-C cycle, 99.9% germ kill",    "https://images.unsplash.com/photo-1584820927498-cfe5211fd8bf?w=400"),
    ],

    "limited": [
        ("Cyberpunk Desk Setup Kit", "🟣", 149999,  5, "Custom RGB keyboard+mouse+pad+hub, neon-signed edition",   "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=400"),
        ("24K Gold iPhone Case",     "✨", 79999,   3, "Hand-crafted 24K plated, real leather back, 1-of-50",      "https://images.unsplash.com/photo-1512499617640-c74ae3a79d37?w=400"),
        ("Titanium Smartwatch",      "⌚", 199999,  2, "Grade 5 Ti case, sapphire crystal, unique engraving, 1/100","https://images.unsplash.com/photo-1619134778706-7015533a6150?w=400"),
        ("Neon Gaming Chair",        "🪑", 89999,   5, "RGB underglow, massage lumbar, aluminium base, 200kg",     "https://images.unsplash.com/photo-1598550476439-6847785fcea6?w=400"),
        ("Holographic Display Cube", "🔮", 249999,  2, "30cm 3D hologram fan array, 8K content, BT app control",   "https://images.unsplash.com/photo-1531746020798-e6953c6e8e04?w=400"),
        ("Liquid Cooled PC Build",   "🖥️", 349999,  1, "Custom loop, i9+RTX4090, 128GB DDR5, watercooled SSD bay", "https://images.unsplash.com/photo-1587202372775-e229f172b9d7?w=400"),
        ("NFT Art Frame 27\"",       "🖼️", 54999,   7, "4K art display, NFT wallet integration, signed by artist",  "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400"),
        ("Fossil Amber Smartwatch",  "🌿", 119999,  3, "Genuine amber inlay, Swiss movement, BLE, 100 units global","https://images.unsplash.com/photo-1619134778706-7015533a6150?w=400"),
        ("Steampunk Keyboard",       "⚙️", 44999,   8, "Solid brass keycaps, vintage switches, leather wrist rest", "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=400"),
        ("Crystal Speaker Orb",      "🔊", 174999,  3, "Hand-blown crystal cabinet, 300W class-A, pair included",  "https://images.unsplash.com/photo-1545454675-3531b543be5d?w=400"),
        ("Signed Astronaut Helmet",  "🪖", 299999,  1, "Apollo-replica, NASA astronaut signed, display pedestal",  "https://images.unsplash.com/photo-1446776709462-d6b525b2b0c6?w=400"),
        ("Carbon Fibre Laptop Skin", "🖤", 9999,   20, "Dry carbon 0.2mm, precision-cut for MacBook, heat-safe",   "https://images.unsplash.com/photo-1525547719571-a2d4ac8945e2?w=400"),
        ("Bespoke Mechanical Watch", "⌛", 499999,  1, "In-house movement, 72hr reserve, platinum case, 1 piece",  "https://images.unsplash.com/photo-1617627143750-d86bc21e42bb?w=400"),
        ("Luxury Drone Briefcase",   "💼", 89999,   4, "Italian leather, foam CNC, fits DJI Mavic + 5 batteries",  "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400"),
        ("Gaming Rig Flight Sim",    "✈️", 189999,  2, "Honeycomb yoke+throttle+rudder+3×4K monitor + chair rig",  "https://images.unsplash.com/photo-1612287230202-1ff1d85d1bdf?w=400"),
        ("Diamond-Tip Stylus",       "💎", 29999,  10, "Synthetic diamond tip, silver barrel, iPad+Surface compat", "https://images.unsplash.com/photo-1542744095-fcf48d80b0fd?w=400"),
        ("Space-Grade Telescope",    "🔭", 399999,  1, "14\" Cassegrain, goto mount, WiFi control, astrophotography","https://images.unsplash.com/photo-1446776709462-d6b525b2b0c6?w=400"),
        ("RGB Aquarium PC Case",     "🐠", 64999,   3, "Live fish tank side panel, custom routing, 360 rad support","https://images.unsplash.com/photo-1587202372775-e229f172b9d7?w=400"),
        ("Limited Run Gaming Mouse", "🖱️", 24999,   6, "Signed by pro player, sapphire feet, 36000 DPI, custom box","https://images.unsplash.com/photo-1527814050087-3793815479db?w=400"),
        ("Aurora Lamp Edition",      "💡", 34999,   8, "Hand-painted aurora glass shade, 16M colour LED, dimmable", "https://images.unsplash.com/photo-1540932239986-30128078f3c5?w=400"),
        ("Vintage Globe Smart Hub",  "🌍", 49999,   5, "Antique wood globe, hidden Alexa, internal speaker 30W",   "https://images.unsplash.com/photo-1589519160732-576f165b9aad?w=400"),
        ("3D Printed Keyboard",      "⌨️", 39999,   6, "Custom 40% layout, hot-swap, printed case, your color",    "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=400"),
        ("Ghost Edition Earbuds",    "👻", 27999,   7, "Transparent housing, visible internals, haunt-glow at dark","https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=400"),
        ("Bamboo Wireless Charger",  "🎋", 12999,  12, "Real bamboo pad, 15W, qi2, FSC certified sustainable wood", "https://images.unsplash.com/photo-1591799265444-d66432b91588?w=400"),
        ("Lava Lamp RGB Speaker",    "🌋", 21999,   9, "Liquid motion + 30W 360° audio, Bluetooth 5.3, USB-C",     "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=400"),
        ("Star Map Custom Frame",    "⭐", 8999,   25, "Your date/location sky map, 4K print, LED backlit frame",  "https://images.unsplash.com/photo-1531746020798-e6953c6e8e04?w=400"),
        ("Handmade Leather Desk Pad","🟤", 16999,  15, "Full-grain leather, stitched edges, 90×45cm, pen loops",   "https://images.unsplash.com/photo-1593642632559-0c6d3fc62b89?w=400"),
        ("Meteorite Fragment Ring",  "🪨", 69999,   4, "Gibeon meteorite inlay, titanium band, certificate of auth","https://images.unsplash.com/photo-1515562141207-7a88fb7ce338?w=400"),
        ("Carbon Fibre Phone Stand", "🔲", 11999,  18, "Monocoque CF shell, CNC aluminium base, MagSafe charger",  "https://images.unsplash.com/photo-1512499617640-c74ae3a79d37?w=400"),
        ("Obsidian Mouse Pad XL",    "🖤", 6999,   30, "Natural obsidian surface, anti-fatigue foam, 90×40cm",     "https://images.unsplash.com/photo-1527814050087-3793815479db?w=400"),
    ],
}


class Command(BaseCommand):
    help = "Seed 150 products (30 per category) with real Unsplash images."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all existing products before seeding.",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            deleted, _ = Product.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Cleared {deleted} existing products."))

        admin_user = User.objects.filter(role__in=["admin", "staff"]).first()
        if not admin_user:
            admin_user = User.objects.first()
        if not admin_user:
            self.stdout.write(self.style.ERROR("No users found. Create a user first."))
            return

        created = 0
        skipped = 0
        sku_counter = 1000

        for category, items in PRODUCTS.items():
            for idx, (name, icon, price, stock, description, image_url) in enumerate(items):
                sku = f"NX-{category[:3].upper()}-{sku_counter}"
                sku_counter += 1

                if Product.objects.filter(sku=sku).exists():
                    skipped += 1
                    continue

                Product.objects.create(
                    name=name,
                    icon=icon,
                    price=price,
                    stock=stock,
                    category=category,
                    description=description,
                    image_url=image_url,
                    sku=sku,
                    is_active=True,
                    created_by=admin_user,
                )

                created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Created: {created} products, Skipped (already exist): {skipped}."
            )
        )

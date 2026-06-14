import os
import json
import urllib.parse
import hashlib
import re
from http.server import SimpleHTTPRequestHandler, HTTPServer

PORT = 8080
HISTORY_FILE = "history.json"
USERS_FILE = "users.json"
# Session helpers and file operations
def read_users_file():
    if not os.path.exists(USERS_FILE):
        return {"users": {}, "sessions": {}}
    try:
        with open(USERS_FILE, "r") as f:
            data = json.load(f)
            if "sessions" not in data:
                data["sessions"] = {}
            if "users" not in data:
                data["users"] = {}
            return data
    except:
        return {"users": {}, "sessions": {}}

def write_users_file(data):
    try:
        with open(USERS_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error writing to users.json: {e}")

def get_active_session(token):
    users_data = read_users_file()
    return users_data.get("sessions", {}).get(token)

def save_active_session(token, phone):
    users_data = read_users_file()
    users_data.setdefault("sessions", {})[token] = phone
    write_users_file(users_data)

def delete_active_session(token):
    users_data = read_users_file()
    if "sessions" in users_data and token in users_data["sessions"]:
        del users_data["sessions"][token]
        write_users_file(users_data)


def normalize_identifier(identifier):
    identifier = identifier.strip()
    if not identifier:
        return None, "invalid"
    if "@" in identifier:
        email_regex = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
        if re.match(email_regex, identifier):
            return identifier.lower(), "email"
        return None, "invalid"
    else:
        cleaned = re.sub(r"[\s\-\(\)\.]", "", identifier)
        if re.match(r"^\+?\d{7,15}$", cleaned):
            return cleaned, "phone"
        return None, "invalid"


# 60-item Waste Database
WASTE_DATABASE = [
  {
    "id": "apple_core",
    "name": "Apple Core",
    "keywords": ["apple", "core", "fruit", "food scrap", "biodegradable", "organic"],
    "category": "biodegradable",
    "material": "Organic Matter",
    "confidence": 99,
    "prep": ["Remove any stickers or plastic tags", "Place directly into compost bin"],
    "destination": "Compost Bin / Green Yard Waste Bin",
    "impact": { "co2": 0.15, "decompose": "2-4 weeks", "points": 15 },
    "upcycle": "Can be used to make apple cider vinegar or thrown in your garden compost pile to enrich soil.",
    "funFact": "Food waste decomposing in landfills produces methane, a greenhouse gas 28x more potent than CO2. Composting prevents this!",
    "image": "assets/apple.png"
  },
  {
    "id": "banana_peel",
    "name": "Banana Peel",
    "keywords": ["banana", "peel", "fruit", "food scrap", "biodegradable", "organic"],
    "category": "biodegradable",
    "material": "Organic Matter",
    "confidence": 98,
    "prep": ["Remove barcode sticker if present", "Throw in compost bin"],
    "destination": "Compost Bin / Green Yard Waste Bin",
    "impact": { "co2": 0.12, "decompose": "3-4 weeks", "points": 10 },
    "upcycle": "Rub the inside of a banana peel on houseplant leaves to clean them and give them a natural shine.",
    "funFact": "Banana peels are rich in potassium, phosphorus, and calcium, making them an excellent fertilizer for your garden.",
    "image": "assets/banana.png"
  },
  {
    "id": "vegetable_waste",
    "name": "Vegetable Waste",
    "keywords": ["vegetable", "waste", "salad", "carrot", "potato", "onion", "scraps", "biodegradable", "organic"],
    "category": "biodegradable",
    "material": "Organic Matter",
    "confidence": 97,
    "prep": ["Ensure free from plastic ties or rubber bands", "Place in green bin"],
    "destination": "Compost Bin / Green Yard Waste Bin",
    "impact": { "co2": 0.14, "decompose": "2-3 weeks", "points": 10 },
    "upcycle": "Collect clean vegetable peels (onion, carrot, celery) in a freezer bag. Boil them later to make delicious home-made vegetable stock!",
    "funFact": "Composted vegetable waste returns key nitrogen and moisture to the soil, building natural crop resilience.",
    "image": "assets/vegetable_waste.png"
  },
  {
    "id": "plastic_bottle",
    "name": "Plastic Water Bottle",
    "keywords": ["plastic bottle", "water bottle", "soda bottle", "pet bottle", "coke bottle", "plastic", "recyclable"],
    "category": "recyclable",
    "material": "PET (Type 1 Plastic)",
    "confidence": 97,
    "prep": ["Empty all liquid contents", "Rinse briefly", "Crush bottle to save space", "Screw cap back on (if allowed locally)"],
    "destination": "Blue Recycling Bin",
    "impact": { "co2": 0.25, "decompose": "450 years", "points": 20 },
    "upcycle": "Can be cut and used as a seedling starter pot, a self-watering planter, or a funnel.",
    "funFact": "Recycling a single plastic bottle saves enough energy to power a 60-watt lightbulb for 3 hours!",
    "image": "assets/bottle.png"
  },
  {
    "id": "soda_can",
    "name": "Aluminum Soda Can",
    "keywords": ["soda can", "coke can", "aluminum can", "beer can", "metal can", "tin can", "recyclable"],
    "category": "recyclable",
    "material": "Aluminum",
    "confidence": 99,
    "prep": ["Ensure empty", "Rinse out residue", "Do not crush completely (helps optical sorting machines)"],
    "destination": "Blue Recycling Bin",
    "impact": { "co2": 0.35, "decompose": "80-200 years", "points": 25 },
    "upcycle": "Can be repurposed into pencil holders, wind chimes, or creative metal artwork.",
    "funFact": "Aluminum is 100% recyclable and can be recycled indefinitely without losing its quality. A recycled can is often back on shelves within 60 days!",
    "image": None
  },
  {
    "id": "aa_battery",
    "name": "Alkaline Battery (AA/AAA/C/D)",
    "keywords": ["battery", "alkaline battery", "aa battery", "aaa battery", "duracell", "energizer", "ewaste"],
    "category": "ewaste",
    "material": "Zinc/Manganese",
    "confidence": 96,
    "prep": ["Place tape over both terminals to prevent fire hazards", "Store in a cool dry container until drop-off"],
    "destination": "E-Waste Recycling Center / Retail Battery Collection point",
    "impact": { "co2": 0.10, "decompose": "100+ years", "points": 30 },
    "upcycle": "Not safe for upcycling. Must be processed professionally to recover metals safely.",
    "funFact": "Although alkaline batteries are less toxic than mercury ones, they still leak corrosive chemicals if landfilled, contaminating groundwater.",
    "image": "assets/battery.png"
  },
  {
    "id": "lithium_battery",
    "name": "Lithium-Ion Battery",
    "keywords": ["lithium battery", "li-ion battery", "rechargeable battery", "phone battery", "laptop battery", "ewaste"],
    "category": "ewaste",
    "material": "Lithium / Cobalt / Carbon",
    "confidence": 94,
    "prep": ["Tape the terminals with electrical tape", "Do not puncture or damage", "Keep away from flammable items"],
    "destination": "E-Waste Recycling Center / Special Battery Collection Hub",
    "impact": { "co2": 0.80, "decompose": "Indestructible (Corrosive leak)", "points": 40 },
    "upcycle": "Must be recycled. Reclaimed cobalt and lithium are highly valuable and reused in new electric car batteries.",
    "funFact": "Lithium-ion batteries are a major cause of fires in garbage trucks and recycling plants when compressed. NEVER put them in household bins!",
    "image": "assets/battery.png"
  },
  {
    "id": "smartphone",
    "name": "Old Smartphone / Tablet",
    "keywords": ["phone", "smartphone", "iphone", "android", "tablet", "ipad", "cellphone", "electronics", "ewaste"],
    "category": "ewaste",
    "material": "Silicon, Copper, Gold, Plastic, Glass",
    "confidence": 95,
    "prep": ["Perform factory reset to wipe data", "Remove SIM card and case", "Do not remove internal battery manually"],
    "destination": "E-Waste Recycling Facility / Retailer Buyback Program",
    "impact": { "co2": 2.50, "decompose": "1000+ years", "points": 50 },
    "upcycle": "Can be repurposed as a dedicated security camera, a smart home controller, or a digital photo frame.",
    "funFact": "One ton of smartphones contains about 300 times more gold than one ton of gold ore!",
    "image": None
  },
  {
    "id": "cardboard_box",
    "name": "Cardboard Box",
    "keywords": ["cardboard", "box", "shipping box", "amazon box", "packing box", "paperboard", "recyclable"],
    "category": "recyclable",
    "material": "Corrugated Cardboard",
    "confidence": 98,
    "prep": ["Remove heavy plastic packing tape and shipping labels", "Flatten the box completely to save bin space", "Keep dry"],
    "destination": "Blue Recycling Bin / Cardboard Dumpster",
    "impact": { "co2": 0.40, "decompose": "2-3 months", "points": 15 },
    "upcycle": "Excellent for drawer dividers, cat playhouses, storage bins, or sheet mulching in the garden.",
    "funFact": "Recycling cardboard saves 24% of the energy required to make new cardboard and saves trees!",
    "image": None
  },
  {
    "id": "glass_jar",
    "name": "Glass Jar / Glass Bottle",
    "keywords": ["glass jar", "glass bottle", "mason jar", "wine bottle", "beer bottle", "glass", "recyclable"],
    "category": "recyclable",
    "material": "Silica Glass",
    "confidence": 99,
    "prep": ["Empty contents fully", "Rinse clean", "Remove metal lid (recycle metal lid separately)"],
    "destination": "Blue Recycling Bin / Glass Only Collection",
    "impact": { "co2": 0.30, "decompose": "1 million years", "points": 20 },
    "upcycle": "Extremely versatile. Can be used for food storage, pencil cups, flower vases, or candle holders.",
    "funFact": "Glass is 100% recyclable and can be melted down and remade infinitely. It never wears out or degrades in quality.",
    "image": None
  },
  {
    "id": "coffee_grounds",
    "name": "Used Coffee Grounds",
    "keywords": ["coffee", "coffee grounds", "espresso", "starbucks", "caffeine", "biodegradable", "organic"],
    "category": "biodegradable",
    "material": "Organic Matter",
    "confidence": 98,
    "prep": ["Separate from plastic pods", "Paper filter is compostable (if unbleached)"],
    "destination": "Compost Bin",
    "impact": { "co2": 0.10, "decompose": "2 weeks", "points": 10 },
    "upcycle": "Can be sprinkled directly on garden soil as a nitrogen-rich fertilizer, used as a natural skin scrub, or as a refrigerator deodorizer.",
    "funFact": "Ants and snails dislike coffee grounds! Use them around your garden borders as a natural pest deterrent.",
    "image": None
  },
  {
    "id": "eggshells",
    "name": "Eggshells",
    "keywords": ["egg", "eggshells", "egg shell", "breakfast", "biodegradable", "organic"],
    "category": "biodegradable",
    "material": "Calcium Carbonate (Organic)",
    "confidence": 97,
    "prep": ["Rinse slightly to prevent odor", "Crush them to speed up decomposition"],
    "destination": "Compost Bin",
    "impact": { "co2": 0.08, "decompose": "3-4 weeks", "points": 10 },
    "upcycle": "Crush them finely and feed them back to chickens for calcium, or mix them into garden soil for tomato plants to prevent blossom end rot.",
    "funFact": "Coarse eggshells act as a natural slug barrier when scattered around tender garden plants.",
    "image": None
  },
  {
    "id": "plastic_bag",
    "name": "Plastic Grocery Bag",
    "keywords": ["plastic bag", "grocery bag", "shopping bag", "target bag", "walmart bag", "polyethylene bag", "non-recyclable"],
    "category": "non-recyclable",
    "material": "LDPE (Type 4 Plastic)",
    "confidence": 94,
    "prep": ["Empty any contents", "Ensure dry", "DO NOT put in household recycling bin (they clog sorting machines)"],
    "destination": "Black Non-Recyclable Bin / Special Retail Store Takeback Bin",
    "impact": { "co2": 0.05, "decompose": "10-20 years", "points": 5 },
    "upcycle": "Use as small trash can liners, dog waste bags, or stuff them inside pillows to make outdoor pet beds.",
    "funFact": "Plastic bags are the #1 culprit for jamming automated sorting machinery at recycling plants, requiring workers to shut down the line to cut them free.",
    "image": None
  },
  {
    "id": "styrofoam_cup",
    "name": "Styrofoam Cup / Container",
    "keywords": ["styrofoam", "polystyrene", "styrofoam cup", "takeout box", "foam", "packing peanut", "non-recyclable"],
    "category": "non-recyclable",
    "material": "Expanded Polystyrene (Type 6 Plastic)",
    "confidence": 95,
    "prep": ["Scrape off food residue", "Throw in trash bin"],
    "destination": "Black Non-Recyclable Bin",
    "impact": { "co2": -0.10, "decompose": "500+ years", "points": -5 },
    "upcycle": "Can be broken down and used in the bottom of potted plants to improve drainage (but do not use for edible plants).",
    "funFact": "Styrofoam is made of 95% air, which makes it extremely lightweight but incredibly bulky. It takes up vast amounts of space in landfills and easily blows away to become marine pollution.",
    "image": None
  },
  {
    "id": "pizza_box_greasy",
    "name": "Greasy Pizza Box",
    "keywords": ["pizza", "pizza box", "grease", "greasy box", "dirty cardboard", "biodegradable"],
    "category": "biodegradable",
    "material": "Soiled Paperboard",
    "confidence": 92,
    "prep": ["Remove all remaining pizza crusts, wax paper, and plastic box savers", "Tear off non-greasy top lid (recycle top lid)", "Compost the greasy bottom half"],
    "destination": "Compost Bin / Green Bin (If local yard waste accepts food-soiled paper) otherwise Non-Recyclable",
    "impact": { "co2": 0.15, "decompose": "2 months", "points": 15 },
    "upcycle": "Excellent food for red wiggler worms in a home vermicomposting bin.",
    "funFact": "Grease and oil from pizza boxes cannot be separated from paper fibers during the recycling slurry process, ruining the entire batch of paper.",
    "image": None
  },
  {
    "id": "pizza_box_clean",
    "name": "Clean Pizza Box",
    "keywords": ["pizza box clean", "clean cardboard", "unused pizza box", "recyclable"],
    "category": "recyclable",
    "material": "Corrugated Cardboard",
    "confidence": 96,
    "prep": ["Ensure there is absolutely no food debris or grease spots", "Flatten and place in recycling"],
    "destination": "Blue Recycling Bin",
    "impact": { "co2": 0.35, "decompose": "2-3 months", "points": 20 },
    "upcycle": "Can be used as a canvas for painting or cut up for children's cardboard crafts.",
    "funFact": "If the lid is clean but the bottom is greasy, you can tear the box in half and recycle the top and compost the bottom!",
    "image": None
  },
  {
    "id": "newspaper",
    "name": "Newspaper / Ads",
    "keywords": ["newspaper", "news", "paper", "magazine", "flyer", "junk mail", "recyclable"],
    "category": "recyclable",
    "material": "Newsprint Paper",
    "confidence": 99,
    "prep": ["Remove plastic wrappers or rubber bands", "Keep dry"],
    "destination": "Blue Recycling Bin",
    "impact": { "co2": 0.20, "decompose": "6 weeks", "points": 15 },
    "upcycle": "Excellent for cleaning windows (with vinegar/water), wrapping gifts, making papier-mâché, or lining birdcages.",
    "funFact": "Recycling a single run of the Sunday New York Times would save approximately 75,000 trees!",
    "image": "assets/newspaper.png"
  },
  {
    "id": "led_bulb",
    "name": "LED Light Bulb",
    "keywords": ["led", "lightbulb", "led bulb", "bulb", "light", "lamp", "ewaste"],
    "category": "ewaste",
    "material": "Glass, Metal, Small LED Circuit Board",
    "confidence": 93,
    "prep": ["Handle carefully to avoid breaking glass", "Wrap in cloth or box for transport"],
    "destination": "E-Waste Recycling Center / Retailer Light Bulb collection bin",
    "impact": { "co2": 0.50, "decompose": "100+ years", "points": 25 },
    "upcycle": "With safety precautions, empty bulbs can be crafted into miniature terrariums or tree ornaments.",
    "funFact": "Unlike fluorescent bulbs, LEDs do not contain hazardous mercury, but they do have electronic microchips that should be recycled as e-waste.",
    "image": None
  },
  {
    "id": "fluorescent_tube",
    "name": "Fluorescent Light Tube / CFL",
    "keywords": ["cfl", "fluorescent", "neon bulb", "light tube", "mercury bulb", "ewaste"],
    "category": "ewaste",
    "material": "Mercury Vapor, Glass, Phosphor",
    "confidence": 95,
    "prep": ["NEVER break. If broken, ventilate room immediately and avoid inhaling dust", "Store safely in original box or cardboard wrap"],
    "destination": "Household E-Waste / Hazardous Waste Collection Facility",
    "impact": { "co2": 0.70, "decompose": "Indestructible (Mercury hazard)", "points": 35 },
    "upcycle": "Not safe for upcycling due to toxic mercury content.",
    "funFact": "CFLs contain a tiny amount of mercury gas. If they end up in landfills, the mercury leaks out and can contaminate air and water supplies.",
    "image": None
  },
  {
    "id": "yogurt_container",
    "name": "Yogurt Cup / Tub",
    "keywords": ["yogurt", "yogurt cup", "yogurt tub", "greek yogurt", "plastic cup", "recyclable"],
    "category": "recyclable",
    "material": "Polypropylene (Type 5 Plastic)",
    "confidence": 96,
    "prep": ["Peel off aluminum foil lid (recycle lid separately if large enough, or throw in non-recyclable)", "Rinse thoroughly to remove yogurt residue", "Leave labels on"],
    "destination": "Blue Recycling Bin",
    "impact": { "co2": 0.18, "decompose": "200-300 years", "points": 15 },
    "upcycle": "Great for freezing batch sauces, organizing small screws/pins, or mixing paint.",
    "funFact": "Type 5 plastic (PP) is highly sought after by recyclers. It is often recycled into auto parts, industrial fibers, and gardening tools.",
    "image": None
  },
  {
    "id": "chip_bag",
    "name": "Potato Chip Bag",
    "keywords": ["chip bag", "lays", "doritos", "crisps", "snack bag", "foil bag", "mylar", "food wrapper", "non-recyclable"],
    "category": "non-recyclable",
    "material": "Metallized Plastic Film (Mylar/Polypropylene)",
    "confidence": 94,
    "prep": ["Empty crumbs completely", "Throw in trash"],
    "destination": "Black Non-Recyclable Bin",
    "impact": { "co2": -0.05, "decompose": "100+ years", "points": -2 },
    "upcycle": "Can be used in specialized crafts like chip bag wallets, or used as stuffing material.",
    "funFact": "Chip bags look like metallic foil, but they are actually a sandwich of plastic and aluminum layers that cannot be separated for recycling.",
    "image": None
  },
  {
    "id": "milk_carton",
    "name": "Milk / Juice Carton",
    "keywords": ["milk carton", "juice carton", "soymilk carton", "gabled carton", "waxy carton", "recyclable"],
    "category": "recyclable",
    "material": "Polycoated Paperboard",
    "confidence": 97,
    "prep": ["Rinse clean", "Flatten carton", "Keep plastic cap on (if attached)"],
    "destination": "Blue Recycling Bin",
    "impact": { "co2": 0.30, "decompose": "5 years (carton portion)", "points": 20 },
    "upcycle": "Can be converted into bird feeders, coin banks, or seedling planters.",
    "funFact": "Cartons are made of high-quality virgin wood fiber, which is highly valuable for making tissue paper and paper towels when recycled.",
    "image": None
  },
  {
    "id": "paper_towel_used",
    "name": "Used Paper Towel / Napkin",
    "keywords": ["paper towel", "napkin", "tissue", "kleenex", "used tissue", "wipes", "biodegradable"],
    "category": "biodegradable",
    "material": "Short-fiber Paper (Soiled)",
    "confidence": 90,
    "prep": ["Ensure it does not contain chemicals or chemical cleaners (only food or water)", "Place in compost"],
    "destination": "Compost Bin / Green Bin",
    "impact": { "co2": 0.10, "decompose": "2-4 weeks", "points": 10 },
    "upcycle": "Should be composted. If soaked with chemical cleaners or disinfectants, throw in the non-recyclable bin.",
    "funFact": "Paper towels cannot be recycled because their wood fibers are already too short and weak to be bonded into new paper products.",
    "image": None
  },
  {
    "id": "soup_can",
    "name": "Steel Soup Can",
    "keywords": ["soup can", "tin can", "steel can", "tuna can", "canned food", "metal can", "recyclable"],
    "category": "recyclable",
    "material": "Steel / Tin-plated Steel",
    "confidence": 98,
    "prep": ["Rinse out remaining soup", "Place lid inside the can so it doesn't cut recycling workers"],
    "destination": "Blue Recycling Bin",
    "impact": { "co2": 0.40, "decompose": "50 years", "points": 25 },
    "upcycle": "Can be painted and used as herb planters, stationary organizers, or lanterns (by punching small holes).",
    "funFact": "Steel is the most recycled material on Earth! Over 80 million tons of steel are recycled in North America alone each year.",
    "image": None
  },
  {
    "id": "aerosol_can_empty",
    "name": "Empty Aerosol Can",
    "keywords": ["aerosol", "hairspray can", "deodorant spray", "spray paint empty", "whipped cream can", "recyclable"],
    "category": "recyclable",
    "material": "Steel or Aluminum",
    "confidence": 92,
    "prep": ["Ensure it is completely empty (no hiss when pressing button)", "Remove plastic cap"],
    "destination": "Blue Recycling Bin",
    "impact": { "co2": 0.30, "decompose": "50-100 years", "points": 20 },
    "upcycle": "Must be recycled. Never attempt to puncture or decorate.",
    "funFact": "Empty aerosol cans are completely recyclable. They are processed alongside other steel and aluminum scrap metal.",
    "image": None
  },
  {
    "id": "aerosol_can_full",
    "name": "Full / Partially Full Aerosol Can",
    "keywords": ["spray paint full", "full aerosol", "hazardous spray", "bug spray can", "non-recyclable"],
    "category": "non-recyclable",
    "material": "Metal, Propellant, Chemical contents",
    "confidence": 93,
    "prep": ["Do not depress or puncture", "Do not expose to high heat", "Store in box for HHW collection"],
    "destination": "Household Hazardous Waste Drop-off Facility",
    "impact": { "co2": 0.00, "decompose": "Explosion hazard", "points": 15 },
    "upcycle": "Strictly hazardous. Must be handled professionally.",
    "funFact": "Pressurized aerosol cans containing paint, solvent, or fuel can explode in waste trucks or incinerators, creating serious fires.",
    "image": None
  },
  {
    "id": "nail_polish",
    "name": "Nail Polish Bottle",
    "keywords": ["nail polish", "manicure", "lacquer", "makeup", "cosmetics", "non-recyclable"],
    "category": "non-recyclable",
    "material": "Solvent-based Lacquer, Glass",
    "confidence": 91,
    "prep": ["Keep lid tightly sealed to prevent leaking", "Do not rinse with water or pour down drain"],
    "destination": "Household Hazardous Waste Drop-off",
    "impact": { "co2": 0.05, "decompose": "100+ years", "points": 20 },
    "upcycle": "Can be used as a small craft paint bottle if cleaned with acetone (but acetone must be disposed of properly).",
    "funFact": "Nail polish is flammable and contains chemicals like toluene and formaldehyde, classifying it as household hazardous waste.",
    "image": None
  },
  {
    "id": "motor_oil",
    "name": "Used Motor Oil / Bottle",
    "keywords": ["motor oil", "car oil", "engine oil", "mobil 1", "lubricant", "non-recyclable"],
    "category": "non-recyclable",
    "material": "Petroleum Hydrocarbons, HDPE Plastic",
    "confidence": 97,
    "prep": ["Keep in a tightly sealed leak-proof plastic container", "Do not mix with water, antifreeze, or paint"],
    "destination": "Auto Parts Retailer / Automotive Recycling Station / HHW Facility",
    "impact": { "co2": 1.50, "decompose": "Toxic bio-accumulation", "points": 40 },
    "upcycle": "Cannot be upcycled. Re-refining motor oil saves valuable crude resources.",
    "funFact": "One gallon of motor oil can contaminate 1 million gallons of fresh water – a year's supply for 50 people!",
    "image": None
  },
  {
    "id": "laptop",
    "name": "Old Laptop / Computer",
    "keywords": ["laptop", "computer", "macbook", "pc", "chromebook", "keyboard", "monitor", "ewaste"],
    "category": "ewaste",
    "material": "Alloys, Plastics, Glass, Lithium Battery, Heavy Metals",
    "confidence": 96,
    "prep": ["Backup files", "Perform a secure data wipe", "Tape over battery area if damaged"],
    "destination": "E-Waste Recycling Depot / Manufacturer Return Program",
    "impact": { "co2": 5.00, "decompose": "1000+ years", "points": 100 },
    "upcycle": "Can be connected to a TV as a home media center, donated to schools, or converted into an additional monitor.",
    "funFact": "Recycling 1 million laptops saves the equivalent energy of powering over 3,600 homes for a full year.",
    "image": None
  },
  {
    "id": "charging_cable",
    "name": "Charging Cable / Wire",
    "keywords": ["cable", "wire", "charger", "usb cable", "hdmi", "power cord", "cords", "ewaste"],
    "category": "ewaste",
    "material": "Copper, PVC Plastic coating",
    "confidence": 95,
    "prep": ["Coil wire neatly", "Remove any plastic tags"],
    "destination": "E-Waste Collection Box / Best Buy drop-off",
    "impact": { "co2": 0.40, "decompose": "100+ years", "points": 20 },
    "upcycle": "Use twist ties to organize cables, or use colored cables for jewelry crafts or rope tying.",
    "funFact": "Copper inside electrical cords is highly sought after by recyclers and can be melted down and re-purposed indefinitely.",
    "image": None
  },
  {
    "id": "teabag",
    "name": "Tea Bag (Plastic-Free)",
    "keywords": ["tea", "teabag", "earl grey", "chamomile", "herbal", "biodegradable", "organic"],
    "category": "biodegradable",
    "material": "Paper, Tea Leaves",
    "confidence": 92,
    "prep": ["Remove metal staple if present", "Ensure bag is not made of plastic mesh (silky bags)"],
    "destination": "Compost Bin",
    "impact": { "co2": 0.05, "decompose": "1-2 months", "points": 10 },
    "upcycle": "Steeped tea bags can be cooled and placed on eyes to reduce puffiness, or added to bathwater.",
    "funFact": "Some modern 'pyramid' tea bags are actually made of plastic (PET or nylon) and will never break down in compost. Check packaging!",
    "image": None
  },
  {
    "id": "bread_crusts",
    "name": "Stale Bread / Crusts",
    "keywords": ["bread", "crust", "toast", "bagel", "pastry", "biodegradable", "organic"],
    "category": "biodegradable",
    "material": "Food waste",
    "confidence": 99,
    "prep": ["Place in green compost bin", "Remove plastic bread bag tie"],
    "destination": "Compost Bin",
    "impact": { "co2": 0.10, "decompose": "1-2 weeks", "points": 10 },
    "upcycle": "Can be baked into croutons, ground into breadcrumbs, or fed to garden birds (in small quantities).",
    "funFact": "Bread is one of the most wasted food products globally. Over 240 million slices are thrown out in the UK alone each year.",
    "image": None
  },
  {
    "id": "bones",
    "name": "Meat / Fish Bones",
    "keywords": ["bones", "chicken bone", "beef bone", "ribs", "steak", "biodegradable", "organic"],
    "category": "biodegradable",
    "material": "Calcium phosphate / collagen",
    "confidence": 95,
    "prep": ["Scrape off heavy spices", "Throw in compost (if your city accepts meat compost)"],
    "destination": "Green Yard/Food Waste Bin (check local rules; home compost bins may attract pests)",
    "impact": { "co2": 0.15, "decompose": "3-6 months", "points": 15 },
    "upcycle": "Boil chicken or beef bones to create a highly nutritious, collagen-rich bone broth.",
    "funFact": "Bones take longer to decompose than soft foods, but industrial composting facilities grind them up where they decompose rapidly.",
    "image": None
  },
  {
    "id": "grass_clippings",
    "name": "Lawn / Grass Clippings",
    "keywords": ["grass", "lawn", "clippings", "garden waste", "biodegradable", "organic"],
    "category": "biodegradable",
    "material": "Organic Matter",
    "confidence": 98,
    "prep": ["Do not mix with plastic yard waste bags", "Keep free of garbage"],
    "destination": "Green Yard Waste Bin / Home Compost Pile",
    "impact": { "co2": 0.50, "decompose": "3-4 weeks", "points": 15 },
    "upcycle": "Practice 'grasscycling' – leave clippings on your lawn. They decompose quickly and return valuable nitrogen to the soil naturally.",
    "funFact": "A lawn mower clipping deposit is composed of 80% water and decomposes rapidly, returning trace minerals back to the turf.",
    "image": None
  },
  {
    "id": "foil_clean",
    "name": "Clean Aluminum Foil",
    "keywords": ["aluminum foil", "tin foil", "foil sheet", "clean foil", "foil tray", "recyclable"],
    "category": "recyclable",
    "material": "Aluminum",
    "confidence": 96,
    "prep": ["Ensure completely clean of food/grease", "Roll multiple pieces of foil into a ball (at least 2 inches wide so sorting machines can detect it)"],
    "destination": "Blue Recycling Bin",
    "impact": { "co2": 0.30, "decompose": "80-100 years", "points": 20 },
    "upcycle": "Can be smoothed out and reused for baking, or used to scrub rusty iron pots.",
    "funFact": "Unlike plastic, aluminum foil is infinitely recyclable. Melting recycled aluminum saves 95% of the energy needed to mine raw bauxite.",
    "image": None
  },
  {
    "id": "foil_dirty",
    "name": "Dirty / Greasy Aluminum Foil",
    "keywords": ["dirty foil", "greasy foil", "soiled aluminum", "food foil", "non-recyclable"],
    "category": "non-recyclable",
    "material": "Soiled Aluminum",
    "confidence": 92,
    "prep": ["Throw in trash bin", "Do not recycle as the food oils interfere with recycling processes"],
    "destination": "Black Non-Recyclable Bin",
    "impact": { "co2": -0.05, "decompose": "80-100 years", "points": -2 },
    "upcycle": "Should be disposed of. If you have backyard chickens, greasy foil is strictly a hazard.",
    "funFact": "Food residue on recyclables can contaminate entire truckloads of recycling, sending the whole batch to the landfill.",
    "image": None
  },
  {
    "id": "wine_cork_natural",
    "name": "Natural Wine Cork",
    "keywords": ["cork", "wine cork", "wooden cork", "wood cork", "biodegradable", "organic"],
    "category": "biodegradable",
    "material": "Cork Wood",
    "confidence": 94,
    "prep": ["Ensure it is 100% natural cork wood (feels woody/spongy)", "Remove any foil wraps"],
    "destination": "Compost Bin / Backyard Compost",
    "impact": { "co2": 0.10, "decompose": "3-6 months", "points": 15 },
    "upcycle": "Natural corks are highly popular for DIY coasters, keychains, bulletin boards, or plant labels.",
    "funFact": "Cork is harvested from the bark of Cork Oak trees, which grows back. It is a highly sustainable, carbon-sequestering material.",
    "image": None
  },
  {
    "id": "wine_cork_synthetic",
    "name": "Synthetic Wine Cork",
    "keywords": ["synthetic cork", "plastic cork", "fake cork", "non-recyclable"],
    "category": "non-recyclable",
    "material": "Plastic Polymer",
    "confidence": 91,
    "prep": ["Throw in garbage bin"],
    "destination": "Black Non-Recyclable Bin",
    "impact": { "co2": -0.05, "decompose": "300+ years", "points": -2 },
    "upcycle": "Can be used as rubbery stamps for kids' painting projects.",
    "funFact": "Synthetic wine corks look like wood, but are actually made of plastic. They do not biodegrade and cannot be recycled with plastic bottles.",
    "image": None
  },
  {
    "id": "ceramic_mug",
    "name": "Ceramic Mug / Plate",
    "keywords": ["ceramic", "mug", "cup", "plate", "porcelain", "clay pot", "dish", "non-recyclable"],
    "category": "non-recyclable",
    "material": "Ceramic / Clay",
    "confidence": 98,
    "prep": ["Ensure it is wrapped in paper if broken to protect sanitation workers", "Throw in trash"],
    "destination": "Black Non-Recyclable Bin",
    "impact": { "co2": -0.15, "decompose": "Indestructible (Stable)", "points": -5 },
    "upcycle": "If chipped, use as a succulent planter. If broken, smash further (safely) and use as drainage stones at the bottom of flower pots.",
    "funFact": "Ceramics melt at a much higher temperature than glass bottles. If mixed with recyclable glass, a single ceramic piece can ruin a glass kiln batch.",
    "image": None
  },
  {
    "id": "coffee_cup_disposable",
    "name": "Disposable Coffee Cup (Paper)",
    "keywords": ["starbucks cup", "coffee cup paper", "paper cup", "mcdonalds cup", "takeout cup", "non-recyclable"],
    "category": "non-recyclable",
    "material": "Paper lined with Polyethylene",
    "confidence": 95,
    "prep": ["Separate plastic lid (usually recyclable Type 5, check label)", "Throw paper cup in trash"],
    "destination": "Black Non-Recyclable Bin",
    "impact": { "co2": -0.08, "decompose": "20-30 years", "points": -2 },
    "upcycle": "Clean paper cups can be used for kid crafts or seed starters, though they decompose very slowly due to the plastic lining.",
    "funFact": "Though they look like paper, disposable coffee cups are lined with a thin plastic layer to prevent leaking, making them unrecyclable in standard facilities.",
    "image": None
  },
  {
    "id": "plastic_cutlery",
    "name": "Plastic Cutlery (Fork/Spoon/Knife)",
    "keywords": ["fork", "spoon", "knife", "plastic fork", "plastic spoon", "plastic cutlery", "utensil", "non-recyclable"],
    "category": "non-recyclable",
    "material": "Polystyrene (Type 6) or Polypropylene",
    "confidence": 96,
    "prep": ["Wipe clean", "Throw in trash"],
    "destination": "Black Non-Recyclable Bin",
    "impact": { "co2": -0.05, "decompose": "400 years", "points": -2 },
    "upcycle": "Wash and reuse them for outdoor picnics, campings, or garden plant markers.",
    "funFact": "Due to their lightweight and thin shape, plastic cutlery falls through recycling sorting screens and jams gears, making them landfill-only.",
    "image": None
  },
  {
    "id": "cardboard_egg_carton",
    "name": "Paper Egg Carton",
    "keywords": ["egg carton paper", "cardboard egg", "egg box paper", "molded pulp", "recyclable"],
    "category": "recyclable",
    "material": "Molded Paper Pulp",
    "confidence": 98,
    "prep": ["Ensure empty", "Flatten slightly", "Can also go into compost"],
    "destination": "Blue Recycling Bin / Compost Bin",
    "impact": { "co2": 0.25, "decompose": "1 month", "points": 15 },
    "upcycle": "Excellent for starter trays for seedlings, paint mixing trays, or soundproofing acoustic absorption setups.",
    "funFact": "Molded pulp egg cartons are made from highly recycled newspaper and cardboard. They break down extremely quickly in compost.",
    "image": None
  },
  {
    "id": "bubble_wrap",
    "name": "Bubble Wrap",
    "keywords": ["bubble wrap", "bubble packing", "protective wrap", "popping bubbles", "non-recyclable"],
    "category": "non-recyclable",
    "material": "LDPE (Type 4 Plastic Film)",
    "confidence": 93,
    "prep": ["Pop the bubbles (fun!)", "Do not put in blue bin"],
    "destination": "Black Non-Recyclable Bin / Special Plastic Film Store Drop-off",
    "impact": { "co2": 0.02, "decompose": "300+ years", "points": 2 },
    "upcycle": "Save and reuse for your next shipping package, or use to insulate potted plants in the winter.",
    "funFact": "Like plastic bags, thin plastic film wrap wraps around rotating gears in standard recycling centers, damaging machinery.",
    "image": None
  },
  {
    "id": "lightbulb_incandescent",
    "name": "Incandescent Light Bulb",
    "keywords": ["lightbulb classic", "old bulb", "tungsten bulb", "filament bulb", "non-recyclable"],
    "category": "non-recyclable",
    "material": "Soda-lime Glass, Metal",
    "confidence": 95,
    "prep": ["Wrap in paper to prevent safety hazards if it breaks", "Throw in trash"],
    "destination": "Black Non-Recyclable Bin",
    "impact": { "co2": -0.05, "decompose": "100+ years", "points": -2 },
    "upcycle": "Can be carefully hollowed out and turned into tiny hanging flower vases or air plant holders.",
    "funFact": "Old-style incandescent bulbs do not contain toxic chemicals like fluorescents, but they are not made of recyclable bottle glass.",
    "image": None
  },
  {
    "id": "acrylic_paint",
    "name": "Latex / Acrylic Paint (Dried)",
    "keywords": ["paint can", "acrylic paint", "latex paint", "dried paint", "wall paint", "non-recyclable"],
    "category": "non-recyclable",
    "material": "Dried Acrylic Polymer, Steel Can",
    "confidence": 92,
    "prep": ["Ensure paint is completely solid/dry (mix with cat litter or paint hardener to dry it out)", "Leave lid off so trash collector can see it's dry"],
    "destination": "Black Non-Recyclable Bin (If 100% dry) / HHW Center if liquid",
    "impact": { "co2": 0.10, "decompose": "100+ years", "points": 15 },
    "upcycle": "Steel paint cans can be cleaned and used as heavy duty buckets or tool storage.",
    "funFact": "Liquid latex paint is banned from trash because it leaks and stains garbage trucks, but once solidified, it is safe for municipal landfills.",
    "image": None
  },
  {
    "id": "oil_paint",
    "name": "Oil-Based Paint (Liquid)",
    "keywords": ["oil paint", "solvent paint", "varnish", "stain", "paint liquid", "non-recyclable"],
    "category": "non-recyclable",
    "material": "Alkyd resin, Solvents, Heavy Metals",
    "confidence": 94,
    "prep": ["Keep lid sealed tightly", "Store upright", "Do not dry out at home"],
    "destination": "Household Hazardous Waste Drop-off",
    "impact": { "co2": 0.50, "decompose": "Biohazard", "points": 30 },
    "upcycle": "Not safe for upcycling. Solvents are flammable and highly toxic.",
    "funFact": "Oil-based paints contain volatile organic compounds (VOCs) that are flammable and can leach into soils if placed in regular landfills.",
    "image": None
  },
  {
    "id": "medicine_bottle",
    "name": "Prescription Medicine Bottle (Empty)",
    "keywords": ["pill bottle", "medicine bottle", "orange bottle", "rx bottle", "recyclable"],
    "category": "recyclable",
    "material": "Polypropylene (Type 5 Plastic)",
    "confidence": 95,
    "prep": ["Rinse out any pill powder", "Peel off or black out personal patient details with a marker", "Recycle with cap on"],
    "destination": "Blue Recycling Bin (If large enough - usually >2 inches. If too small, non-recyclable)",
    "impact": { "co2": 0.10, "decompose": "200+ years", "points": 15 },
    "upcycle": "Excellent container for storing small sewing needles, seeds, buttons, or loose coins.",
    "funFact": "Many animal shelters and humanitarian charities collect clean, empty pill bottles to reuse in developing nations.",
    "image": None
  },
  {
    "id": "unused_medicine",
    "name": "Unused / Expired Medicine",
    "keywords": ["pills", "drugs", "expired medicine", "prescription", "antibiotics", "aspirin", "non-recyclable"],
    "category": "non-recyclable",
    "material": "Chemical Pharmaceuticals",
    "confidence": 91,
    "prep": ["Leave in original container", "Keep away from children", "NEVER flush down toilet or sink"],
    "destination": "Pharmacy Take-Back Box / Drug Take-Back Day",
    "impact": { "co2": 0.50, "decompose": "Chemical hazard", "points": 25 },
    "upcycle": "Must be disposed of professionally to prevent environmental poisoning.",
    "funFact": "Flushing medicines down the drain sends them directly into waterways, where they bypass sewage treatments and harm fish and aquatic ecosystems.",
    "image": None
  },
  {
    "id": "jeans_old",
    "name": "Old Jeans / Denim",
    "keywords": ["jeans", "denim", "pants", "clothes", "fabric", "cotton pants", "recyclable"],
    "category": "recyclable",
    "material": "Cotton / Elastane",
    "confidence": 95,
    "prep": ["Wash beforehand", "Dry completely", "Place in textile donation bin (even if ripped or stained)"],
    "destination": "Textile Donation Box / Clothing Drop-off Hub",
    "impact": { "co2": 1.20, "decompose": "6-12 months (if 100% cotton)", "points": 30 },
    "upcycle": "Denim is incredibly durable. Cut it up to make tote bags, denim shorts, cleaning rags, or insulated pot holders.",
    "funFact": "Over 85% of all textiles end up in landfills. Ripped and stained clothes can be shredded and turned into insulation or car seat stuffing!",
    "image": None
  },
  {
    "id": "aluminum_tray",
    "name": "Aluminum Baking Tray",
    "keywords": ["baking tray", "pie tin", "foil pan", "turkey pan", "foil tray", "recyclable"],
    "category": "recyclable",
    "material": "Aluminum",
    "confidence": 98,
    "prep": ["Scrape away food scraps", "Rinse off grease", "Crumple to fit in recycle container"],
    "destination": "Blue Recycling Bin",
    "impact": { "co2": 0.35, "decompose": "80-100 years", "points": 20 },
    "upcycle": "Can be washed and used again for baking, or used as a plant drip tray.",
    "funFact": "Aluminum foil baking trays are made from the exact same alloy as soda cans and are highly recyclable.",
    "image": None
  },
  {
    "id": "mirror_glass",
    "name": "Broken Mirror Glass",
    "keywords": ["mirror", "broken mirror", "silvered glass", "reflective glass", "non-recyclable"],
    "category": "non-recyclable",
    "material": "Glass with Silver backing",
    "confidence": 94,
    "prep": ["Wrap carefully in several sheets of newspaper or cardboard", "Label 'BROKEN GLASS' for safety", "Throw in trash"],
    "destination": "Black Non-Recyclable Bin",
    "impact": { "co2": -0.10, "decompose": "1 million years", "points": -5 },
    "upcycle": "Intact mirror parts can be cut (carefully) for mosaic mirror art or disco ball decorations.",
    "funFact": "Mirror glass is treated with a metallic backing layer, making it incompatible with standard container glass recycling furnaces.",
    "image": None
  }
]

FALLBACK_CATEGORIES = {
  "biodegradable": {
    "name": "Unlisted Biodegradable Item",
    "category": "biodegradable",
    "material": "Organic Matter",
    "prep": ["Ensure item is free of plastic and chemicals", "Throw in compost"],
    "destination": "Compost Bin",
    "impact": { "co2": 0.10, "decompose": "1-3 months", "points": 10 },
    "upcycle": "Incorporate into yard mulch or home compost bin.",
    "funFact": "Organic items rot cleanly in compost but produce toxic leachate and gas if compressed in oxygen-poor landfills."
  },
  "recyclable": {
    "name": "Unlisted Recyclable Item",
    "category": "recyclable",
    "material": "Assorted Recyclable",
    "prep": ["Rinse off food residue", "Check for recycling symbols 1 through 7"],
    "destination": "Blue Recycling Bin",
    "impact": { "co2": 0.20, "decompose": "100+ years", "points": 15 },
    "upcycle": "Check if you can repurpose the container for household storage before discarding.",
    "funFact": "Look for the triangular resin identification code on plastics to know if your city accepts them."
  },
  "ewaste": {
    "name": "Unlisted E-Waste Item",
    "category": "ewaste",
    "material": "Electronic Circuitry & Metal",
    "prep": ["Backup and delete personal data", "Do not throw in household trash"],
    "destination": "Electronics Recycling Depot",
    "impact": { "co2": 1.50, "decompose": "1000+ years", "points": 30 },
    "upcycle": "Donate working electronics to local non-profits or community schools.",
    "funFact": "Electronic waste is the fastest-growing solid waste stream in the world."
  },
  "non-recyclable": {
    "name": "Unlisted Non-Recyclable Waste",
    "category": "non-recyclable",
    "material": "Composite Material / Non-recyclable",
    "prep": ["Dispose of securely in trash", "Ensure no liquids are leaking"],
    "destination": "Black Non-Recyclable Bin",
    "impact": { "co2": -0.05, "decompose": "100+ years", "points": -2 },
    "upcycle": "Consider how to reduce buying single-use composite materials in the future.",
    "funFact": "Landfills are carefully engineered cells dug into the ground, lined with plastic to prevent toxic fluids from entering groundwater."
  }
}

class EcoSortHTTPHandler(SimpleHTTPRequestHandler):
    
    def log_message(self, format, *args):
        # Override to suppress standard HTTP logging to keep server console clean
        pass

    def get_authenticated_user(self):
        auth_header = self.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:].strip()
            return get_active_session(token)
        return None

    def do_GET(self):
        url_parsed = urllib.parse.urlparse(self.path)
        path = url_parsed.path
        query = urllib.parse.parse_qs(url_parsed.query)
        
        # Route: API Search
        if path == "/api/search":
            q_param = query.get("q", [""])[0].strip().lower()
            if not q_param:
                self.send_json_response([])
                return
                
            matches = []
            for item in WASTE_DATABASE:
                # Fuzzy keyword or name matching
                if q_param in item["name"].lower() or any(q_param in kw for kw in item["keywords"]):
                    matches.append(item)
            
            # Limit to 5 suggestions
            self.send_json_response(matches[:5])
            return

        # Route: API Classify
        elif path == "/api/classify":
            item_id = query.get("id", [""])[0]
            guess_q = query.get("guess", [""])[0].strip()
            
            # Attempt lookup by ID
            if item_id:
                matched_item = next((item for item in WASTE_DATABASE if item["id"] == item_id), None)
                if matched_item:
                    self.send_json_response(matched_item)
                    return
            
            # Guessed category logic on backend
            if guess_q:
                lowercase_query = guess_q.lower()
                guessed_category = "non-recyclable"
                
                # Check keywords
                if any(x in lowercase_query for x in ["apple", "banana", "orange", "grape", "fruit", "food", "salad", "vegetable", "carrot", "potato", "onion", "bread", "meat", "bone", "compost", "coffee", "egg", "leaf", "leaves", "grass", "cork"]):
                    guessed_category = "biodegradable"
                elif any(x in lowercase_query for x in ["plastic", "bottle", "can", "box", "paper", "newspaper", "cardboard", "jar", "glass", "aluminum", "metal", "soup", "foil"]):
                    guessed_category = "recyclable"
                elif any(x in lowercase_query for x in ["phone", "smartphone", "mobile", "laptop", "computer", "cable", "wire", "battery", "bulb", "led", "screen", "electronics", "charger"]):
                    guessed_category = "ewaste"
                    
                fallback = FALLBACK_CATEGORIES[guessed_category]
                custom_item = {
                    "id": f"unlisted_{int(urllib.parse.time.time() * 1000) if hasattr(urllib.parse, 'time') else 123456}",
                    "name": guess_q.capitalize(),
                    "category": guessed_category,
                    "material": fallback["material"],
                    "confidence": 85,
                    "prep": fallback["prep"],
                    "destination": fallback["destination"],
                    "impact": fallback["impact"],
                    "upcycle": fallback["upcycle"],
                    "funFact": fallback["funFact"],
                    "image": None
                }
                self.send_json_response(custom_item)
                return
                
            self.send_error_response(400, "Missing ID or Guess parameters")
            return

        # Route: API Fetch History
        elif path == "/api/history":
            email = self.get_authenticated_user()
            if not email:
                self.send_error_response(401, "Unauthorized")
                return
            users_data = read_users_file()
            user_info = users_data.get("users", {}).get(email, {})
            history_data = user_info.get("history", [])
            self.send_json_response(history_data)
            return

        # Route: API Leaderboard
        elif path == "/api/leaderboard":
            users_data = read_users_file()
            users_list = []
            for identifier, user_info in users_data.get("users", {}).items():
                name = user_info.get("name", "Eco Sorter")
                history = user_info.get("history", [])
                total_points = sum(item.get("points", 0) for item in history)
                co2_saved = sum(item.get("co2", 0.0) for item in history)
                items_count = len(history)
                # Obfuscate phone number/identifier for privacy if name is not set
                display_name = name if name else "User " + identifier[-4:]
                users_list.append({
                    "name": display_name,
                    "points": total_points,
                    "co2": round(co2_saved, 2),
                    "items": items_count
                })
            
            # Sort by points descending
            users_list.sort(key=lambda x: x["points"], reverse=True)
            self.send_json_response(users_list[:10])
            return

        # Route: Fallback to serving static html/css/js files
        else:
            return super().do_GET()

    def do_POST(self):
        url_parsed = urllib.parse.urlparse(self.path)
        path = url_parsed.path
        
        # Route: Add item to history log
        if path == "/api/history":
            email = self.get_authenticated_user()
            if not email:
                self.send_error_response(401, "Unauthorized")
                return

            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                new_scan_or_list = json.loads(post_data.decode('utf-8'))
                users_data = read_users_file()
                user_info = users_data.setdefault("users", {}).setdefault(email, {})
                
                # Check if payload is a list (clear history sends [])
                if isinstance(new_scan_or_list, list):
                    user_info["history"] = new_scan_or_list
                else:
                    history_data = user_info.get("history", [])
                    history_data.insert(0, new_scan_or_list)
                    if len(history_data) > 15:
                        history_data.pop()
                    user_info["history"] = history_data
                    
                write_users_file(users_data)
                self.send_json_response(user_info["history"])
            except Exception as e:
                self.send_error_response(500, f"Error processing POST: {str(e)}")
            return

        elif path == "/api/register":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                name = data.get("name", "").strip()
                raw_phone = data.get("phone", "").strip()
                password = data.get("password", "")
                
                if not name or not raw_phone or not password:
                    self.send_error_response(400, "All fields are required")
                    return
                
                phone, phone_type = normalize_identifier(raw_phone)
                
                if phone_type != "phone":
                    self.send_error_response(400, "Invalid phone number format")
                    return
                
                users_data = read_users_file()
                if phone in users_data.get("users", {}):
                    self.send_error_response(400, "Phone number already registered")
                    return
                
                # Generate random salt
                salt = os.urandom(16).hex()
                # Hash password with salt
                password_hash = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
                
                # Create user
                users_data.setdefault("users", {})[phone] = {
                    "password_hash": password_hash,
                    "password_salt": salt,
                    "name": name,
                    "phone": phone,
                    "history": []
                }
                write_users_file(users_data)
                
                # Generate token and save active session
                token = os.urandom(16).hex()
                save_active_session(token, phone)
                
                self.send_json_response({"token": token, "phone": phone, "name": name})
            except Exception as e:
                self.send_error_response(500, f"Error registering: {str(e)}")
            return

        elif path == "/api/login":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                raw_phone = data.get("phone", "").strip()
                password = data.get("password", "")
                
                if not raw_phone or not password:
                    self.send_error_response(400, "Phone number and password are required")
                    return
                
                phone, phone_type = normalize_identifier(raw_phone)
                if phone_type != "phone":
                    self.send_error_response(400, "Invalid phone number format")
                    return
                
                users_data = read_users_file()
                user = users_data.get("users", {}).get(phone)
                
                if not user:
                    # Try suffix match
                    cleaned_input = re.sub(r"\D", "", phone)
                    if len(cleaned_input) >= 7:
                        for u_phone, u_data in users_data.get("users", {}).items():
                            cleaned_u_phone = re.sub(r"\D", "", u_phone)
                            if cleaned_u_phone.endswith(cleaned_input):
                                user = u_data
                                phone = u_phone
                                break
                                
                if not user:
                    self.send_error_response(401, "Invalid phone number or password")
                    return
                
                # Salted password verification (backward-compatible)
                stored_hash = user.get("password_hash")
                stored_salt = user.get("password_salt")
                
                if stored_salt:
                    computed_hash = hashlib.sha256((password + stored_salt).encode('utf-8')).hexdigest()
                else:
                    computed_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
                    
                if stored_hash != computed_hash:
                    self.send_error_response(401, "Invalid phone number or password")
                    return
                
                # Generate token and save active session
                token = os.urandom(16).hex()
                save_active_session(token, phone)
                
                self.send_json_response({"token": token, "phone": phone, "name": user.get("name", "")})
            except Exception as e:
                self.send_error_response(500, f"Error logging in: {str(e)}")
            return

        elif path == "/api/logout":
            auth_header = self.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                token = auth_header[7:].strip()
                delete_active_session(token)
            self.send_json_response({"success": True})
            return
            
        else:
            self.send_error_response(404, "Endpoint not found")

    def send_json_response(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        # Enable CORS for local cross-port testing if required
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def send_error_response(self, code, message):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"error": message}).encode('utf-8'))



def run_server():
    server_address = ('', PORT)
    httpd = HTTPServer(server_address, EcoSortHTTPHandler)
    print(f"==================================================")
    print(f" EcoSort AI python backend serving on port {PORT}")
    print(f" Open http://localhost:{PORT} in your web browser!")
    print(f"==================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping EcoSort server.")
        httpd.server_close()

if __name__ == "__main__":
    run_server()

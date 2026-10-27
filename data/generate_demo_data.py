"""
Generates rich synthetic retail dataset for DataLens Demo Mode.
Creates:
1. data/demo_retail_data.csv (consolidated view)
2. data/demo_store_sales.csv
3. data/demo_web_sales.csv
4. data/demo_catalog_sales.csv
5. data/demo_item.csv
6. data/demo_customer.csv
7. data/demo_date_dim.csv
"""

import os
import random
from datetime import datetime, timedelta
import pandas as pd

random.seed(42)

# Product catalog
PRODUCTS = [
    # Electronics
    {"id": "PROD-101", "name": "UltraHD 4K Smart OLED TV 65-inch", "category": "Electronics", "brand": "ApexTech", "price": 1299.99},
    {"id": "PROD-102", "name": "Noise-Cancelling Wireless Pro Headphones", "category": "Electronics", "brand": "SoundWave", "price": 249.99},
    {"id": "PROD-103", "name": "Titan Gaming Laptop 16GB RTX 4070", "category": "Electronics", "brand": "ApexTech", "price": 1799.50},
    {"id": "PROD-104", "name": "Smart Fitness & Health Tracker Band", "category": "Electronics", "brand": "PulseFit", "price": 89.95},
    {"id": "PROD-105", "name": "True Wireless Studio Earbuds", "category": "Electronics", "brand": "SoundWave", "price": 129.00},
    {"id": "PROD-106", "name": "Ultra-Wide Curved Productivity Monitor 34-inch", "category": "Electronics", "brand": "ApexTech", "price": 499.00},
    
    # Apparel
    {"id": "PROD-201", "name": "Premium All-Weather Gore-Tex Parka", "category": "Apparel", "brand": "NorthSummit", "price": 280.00},
    {"id": "PROD-202", "name": "Organic Cotton Slim-Fit Chinos", "category": "Apparel", "brand": "UrbanLoom", "price": 65.00},
    {"id": "PROD-203", "name": "Merino Wool Thermal Crewneck Sweater", "category": "Apparel", "brand": "NordicWeave", "price": 115.00},
    {"id": "PROD-204", "name": "Performance Moisture-Wicking Running Shoes", "category": "Apparel", "brand": "Stride", "price": 140.00},
    {"id": "PROD-205", "name": "Classic Tailored Italian Wool Blazer", "category": "Apparel", "brand": "Sartorial", "price": 320.00},
    
    # Home & Kitchen
    {"id": "PROD-301", "name": "Precision Espresso Machine & Grinder Combo", "category": "Home & Kitchen", "brand": "BaristaPro", "price": 699.00},
    {"id": "PROD-302", "name": "Multi-Cooker Air Fryer Deluxe 8-in-1", "category": "Home & Kitchen", "brand": "CuisineMaster", "price": 159.99},
    {"id": "PROD-303", "name": "Cordless Smart Robotic Vacuum & Mop", "category": "Home & Kitchen", "brand": "CleanBot", "price": 450.00},
    {"id": "PROD-304", "name": "Cast Iron Enamelled Dutch Oven 6-Quart", "category": "Home & Kitchen", "brand": "HeritageCook", "price": 135.00},
    {"id": "PROD-305", "name": "Ergonomic Memory Foam Cooling Pillow", "category": "Home & Kitchen", "brand": "CloudRest", "price": 55.00},

    # Books & Media
    {"id": "PROD-401", "name": "Modern Data Architecture with Cloud Warehouses", "category": "Books", "brand": "TechPress", "price": 48.00},
    {"id": "PROD-402", "name": "Designing AI Agents & Foundation Models", "category": "Books", "brand": "TechPress", "price": 54.00},
    {"id": "PROD-403", "name": "The Art of Financial Forecasting", "category": "Books", "brand": "GuildPub", "price": 35.00},
    {"id": "PROD-404", "name": "Gourmet Artisan Sourdough Masterclass", "category": "Books", "brand": "CulinaryArts", "price": 29.99},

    # Sports & Outdoors
    {"id": "PROD-501", "name": "Aerodynamic Carbon Gravel Bike", "category": "Sports", "brand": "Veloce", "price": 2250.00},
    {"id": "PROD-502", "name": "Ultralight 2-Person Backpacking Tent", "category": "Sports", "brand": "NorthSummit", "price": 210.00},
    {"id": "PROD-503", "name": "Adjustable Quick-Select Dumbbell Set 50lb", "category": "Sports", "brand": "IronCore", "price": 349.00},
    {"id": "PROD-504", "name": "Inflatable Stand-Up Touring Paddleboard", "category": "Sports", "brand": "AquaGlide", "price": 395.00},
]

CUSTOMERS = [
    {"sk": 1001, "id": "CUST-001", "first_name": "Eleanor", "last_name": "Vance", "email": "e.vance@example.com"},
    {"sk": 1002, "id": "CUST-002", "first_name": "Marcus", "last_name": "Brody", "email": "m.brody@example.com"},
    {"sk": 1003, "id": "CUST-003", "first_name": "Sophia", "last_name": "Chen", "email": "s.chen@example.com"},
    {"sk": 1004, "id": "CUST-004", "first_name": "Liam", "last_name": "O'Connor", "email": "l.oconnor@example.com"},
    {"sk": 1005, "id": "CUST-005", "first_name": "Zara", "last_name": "Ahmed", "email": "z.ahmed@example.com"},
    {"sk": 1006, "id": "CUST-006", "first_name": "Alexander", "last_name": "Wright", "email": "a.wright@example.com"},
    {"sk": 1007, "id": "CUST-007", "first_name": "Camila", "last_name": "Reyes", "email": "c.reyes@example.com"},
    {"sk": 1008, "id": "CUST-008", "first_name": "David", "last_name": "Kim", "email": "d.kim@example.com"},
    {"sk": 1009, "id": "CUST-009", "first_name": "Olivia", "last_name": "Dubois", "email": "o.dubois@example.com"},
    {"sk": 1010, "id": "CUST-010", "first_name": "Julian", "last_name": "Morales", "email": "j.morales@example.com"},
]

CHANNELS = ["Store", "Web", "Catalog"]
CHANNEL_WEIGHTS = [0.50, 0.35, 0.15]

def generate_datasets():
    out_dir = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(out_dir, exist_ok=True)

    # Date range: 2024-01-01 to 2025-12-31 (730 days)
    start_date = datetime(2024, 1, 1)
    dates = [start_date + timedelta(days=i) for i in range(730)]

    # 1. Date Dim
    date_rows = []
    for d in dates:
        sk = int(d.strftime("%Y%m%d"))
        date_rows.append({
            "d_date_sk": sk,
            "d_date_id": d.strftime("%Y-%m-%d"),
            "d_date": d.strftime("%Y-%m-%d"),
            "d_year": d.year,
            "d_moy": d.month,
            "d_dom": d.day,
            "d_qoy": (d.month - 1) // 3 + 1,
            "d_month_name": d.strftime("%B"),
            "d_holiday": "Y" if d.month == 12 and d.day == 25 else "N",
            "d_weekend": "Y" if d.weekday() >= 5 else "N",
        })
    df_date_dim = pd.DataFrame(date_rows)
    df_date_dim.to_csv(os.path.join(out_dir, "demo_date_dim.csv"), index=False)

    # 2. Item Dim
    item_rows = []
    for idx, p in enumerate(PRODUCTS, start=1):
        item_rows.append({
            "i_item_sk": idx,
            "i_item_id": p["id"],
            "i_product_name": p["name"],
            "i_item_desc": p["name"],
            "i_category": p["category"],
            "i_brand": p["brand"],
            "i_class": p["category"].lower().replace(" ", "_"),
            "i_current_price": p["price"],
            "i_wholesale_cost": round(p["price"] * 0.55, 2),
        })
    df_item = pd.DataFrame(item_rows)
    df_item.to_csv(os.path.join(out_dir, "demo_item.csv"), index=False)

    # 3. Customer Dim
    df_customer = pd.DataFrame([{
        "c_customer_sk": c["sk"],
        "c_customer_id": c["id"],
        "c_first_name": c["first_name"],
        "c_last_name": c["last_name"],
        "c_email_address": c["email"],
    } for c in CUSTOMERS])
    df_customer.to_csv(os.path.join(out_dir, "demo_customer.csv"), index=False)

    # 4. Generate Transactions
    consolidated_rows = []
    store_rows = []
    web_rows = []
    catalog_rows = []

    tx_counter = 100000

    # Generate roughly 3000 realistic sales transactions across the two years
    for _ in range(3200):
        tx_counter += 1
        d = random.choice(dates)
        date_sk = int(d.strftime("%Y%m%d"))
        
        # Seasonality boost for Q4 (Nov, Dec)
        if d.month in [11, 12] and random.random() < 0.3:
            d = random.choice([dt for dt in dates if dt.month in [11, 12]])
            date_sk = int(d.strftime("%Y%m%d"))

        item_meta = random.choice(PRODUCTS)
        item_sk = [i["i_item_sk"] for i in item_rows if i["i_item_id"] == item_meta["id"]][0]
        cust = random.choice(CUSTOMERS)
        cust_sk = cust["sk"]

        channel = random.choices(CHANNELS, weights=CHANNEL_WEIGHTS, k=1)[0]
        quantity = random.choices([1, 2, 3, 4, 5, 8, 10], weights=[0.45, 0.25, 0.15, 0.08, 0.04, 0.02, 0.01], k=1)[0]
        
        unit_price = item_meta["price"]
        wholesale_cost = round(unit_price * 0.55, 2)
        sales_amount = round(quantity * unit_price, 2)
        net_profit = round(sales_amount - (quantity * wholesale_cost), 2)

        record = {
            "sale_id": f"TX-{tx_counter}",
            "date": d.strftime("%Y-%m-%d"),
            "year": d.year,
            "month": d.month,
            "month_name": d.strftime("%B"),
            "channel": channel,
            "item_id": item_meta["id"],
            "item_name": item_meta["name"],
            "category": item_meta["category"],
            "brand": item_meta["brand"],
            "quantity": quantity,
            "unit_price": unit_price,
            "sales_amount": sales_amount,
            "net_profit": net_profit,
            "customer_id": cust["id"],
            "customer_name": f"{cust['first_name']} {cust['last_name']}",
        }
        consolidated_rows.append(record)

        # Fact table formats
        if channel == "Store":
            store_rows.append({
                "ss_sold_date_sk": date_sk,
                "ss_item_sk": item_sk,
                "ss_customer_sk": cust_sk,
                "ss_quantity": quantity,
                "ss_wholesale_cost": wholesale_cost,
                "ss_list_price": unit_price,
                "ss_sales_price": unit_price,
                "ss_ext_sales_price": sales_amount,
                "ss_net_paid": sales_amount,
                "ss_net_profit": net_profit,
            })
        elif channel == "Web":
            web_rows.append({
                "ws_sold_date_sk": date_sk,
                "ws_item_sk": item_sk,
                "ws_bill_customer_sk": cust_sk,
                "ws_quantity": quantity,
                "ws_wholesale_cost": wholesale_cost,
                "ws_list_price": unit_price,
                "ws_sales_price": unit_price,
                "ws_ext_sales_price": sales_amount,
                "ws_net_paid": sales_amount,
                "ws_net_profit": net_profit,
            })
        else: # Catalog
            catalog_rows.append({
                "cs_sold_date_sk": date_sk,
                "cs_item_sk": item_sk,
                "cs_bill_customer_sk": cust_sk,
                "cs_quantity": quantity,
                "cs_wholesale_cost": wholesale_cost,
                "cs_list_price": unit_price,
                "cs_sales_price": unit_price,
                "cs_ext_sales_price": sales_amount,
                "cs_net_paid": sales_amount,
                "cs_net_profit": net_profit,
            })

    # Save consolidated
    df_consolidated = pd.DataFrame(consolidated_rows)
    df_consolidated = df_consolidated.sort_values(by="date")
    df_consolidated.to_csv(os.path.join(out_dir, "demo_retail_data.csv"), index=False)

    # Save fact tables
    pd.DataFrame(store_rows).to_csv(os.path.join(out_dir, "demo_store_sales.csv"), index=False)
    pd.DataFrame(web_rows).to_csv(os.path.join(out_dir, "demo_web_sales.csv"), index=False)
    pd.DataFrame(catalog_rows).to_csv(os.path.join(out_dir, "demo_catalog_sales.csv"), index=False)

    print(f"Generated {len(df_consolidated)} retail sales records.")
    print(f"Store sales: {len(store_rows)}, Web sales: {len(web_rows)}, Catalog sales: {len(catalog_rows)}")

if __name__ == "__main__":
    generate_datasets()

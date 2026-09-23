"""
High-Fidelity Synthetic Data Generator for Project FORESIGHT.
Generates realistic 2-year daily datasets for NorthBay Living conforming strictly to PRD schema contracts.
Includes intentional, realistic imperfections to validate cleaning rules CLN-01 to CLN-05.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from src.config import config
from src.logging_utils import get_logger
from src.io import ensure_dir

logger = get_logger(__name__)


def generate_sample_dataset() -> None:
    """Generates the 4 core raw CSV datasets into data/sample/."""
    np.random.seed(config.RANDOM_SEED)
    sample_dir = ensure_dir(config.DATA_SAMPLE_DIR)

    # 1. SKU Master
    categories = {
        "Home Decor": ["Vases", "Wall Art", "Candles", "Cushions"],
        "Bedding": ["Bedsheets", "Duvets", "Pillows", "Blankets"],
        "Kitchen & Dining": ["Dinnerware", "Glassware", "Cutlery", "Table Linen"],
        "Bath": ["Towels", "Bath Mats", "Dispensers", "Robes"]
    }

    sku_records = []
    sku_ids = []
    base_prices = {}
    base_costs = {}

    start_date = datetime(2024, 1, 1)
    end_date = datetime(2025, 12, 31)

    sku_idx = 1
    for cat, subcats in categories.items():
        for subcat in subcats:
            num_skus = 3 if cat in ["Home Decor", "Bedding"] else 2
            for _ in range(num_skus):
                sku_id = f"NB-{cat[:3].upper()}-{subcat[:3].upper()}-{sku_idx:03d}"
                launch_offset = np.random.randint(0, 180)
                launch_date = (start_date + timedelta(days=launch_offset)).strftime("%Y-%m-%d")

                cost = round(float(np.random.uniform(250.0, 3500.0)), 2)
                margin = np.random.uniform(1.6, 2.8)
                list_price = round(cost * margin, 2)

                sku_records.append({
                    "sku_id": sku_id,
                    "category": f"  {cat}  " if sku_idx == 3 else cat,  # Intentional whitespace anomaly for CLN-01
                    "subcategory": subcat,
                    "launch_date": launch_date,
                    "unit_cost": cost,
                    "list_price": list_price
                })
                sku_ids.append(sku_id)
                base_prices[sku_id] = list_price
                base_costs[sku_id] = cost
                sku_idx += 1

    df_sku = pd.DataFrame(sku_records)
    df_sku.to_csv(sample_dir / "sku_master.csv", index=False)
    logger.info(f"Generated sku_master.csv ({len(df_sku)} SKUs)")

    # 2. Calendar
    date_range = pd.date_range(start_date, end_date, freq="D")
    cal_records = []
    seasons = {12: "Winter", 1: "Winter", 2: "Winter",
               3: "Spring", 4: "Spring", 5: "Summer",
               6: "Summer", 7: "Monsoon", 8: "Monsoon",
               9: "Autumn", 10: "Festive", 11: "Festive"}

    festivals = {
        "2024-01-26": "Republic Day",
        "2024-03-25": "Holi",
        "2024-08-15": "Independence Day",
        "2024-10-12": "Dussehra",
        "2024-11-01": "Diwali Sale",
        "2024-12-25": "Christmas",
        "2025-01-26": "Republic Day",
        "2025-03-14": "Holi",
        "2025-08-15": "Independence Day",
        "2025-10-02": "Gandhi Jayanti",
        "2025-10-20": "Diwali Sale",
        "2025-12-25": "Christmas"
    }

    for dt in date_range:
        dt_str = dt.strftime("%Y-%m-%d")
        month = dt.month
        week = dt.isocalendar()[1]
        season = seasons.get(month, "Regular")
        is_holiday = 1 if dt.weekday() in [5, 6] or dt_str in festivals else 0
        promo_event = festivals.get(dt_str, None)

        cal_records.append({
            "date": dt_str,
            "week": week,
            "month": month,
            "season": season,
            "is_holiday": is_holiday,
            "promo_event": promo_event
        })

    df_cal = pd.DataFrame(cal_records)
    df_cal.to_csv(sample_dir / "calendar.csv", index=False)
    logger.info(f"Generated calendar.csv ({len(df_cal)} dates)")

    # 3. Daily Sales
    sales_records = []
    for dt in date_range:
        dt_str = dt.strftime("%Y-%m-%d")
        month = dt.month
        is_festive = 1.6 if month in [10, 11] else 1.0
        is_weekend = 1.3 if dt.weekday() in [5, 6] else 1.0

        for sku_id in sku_ids:
            # Active launch check
            launch_d = datetime.strptime(df_sku.loc[df_sku["sku_id"] == sku_id.strip(), "launch_date"].values[0], "%Y-%m-%d")
            if dt < launch_d:
                continue

            list_p = base_prices[sku_id.strip()]
            # 12% probability of promotion
            is_promo = 1 if np.random.rand() < 0.12 or dt_str in festivals else 0
            discount = np.random.uniform(0.10, 0.30) if is_promo else 0.0
            unit_price = round(list_p * (1.0 - discount), 2)

            # Base Poisson lambda demand
            base_lambda = np.random.uniform(1.0, 8.0)
            promo_multiplier = 2.2 if is_promo else 1.0
            daily_lambda = base_lambda * is_festive * is_weekend * promo_multiplier
            units = int(np.random.poisson(lam=daily_lambda))

            revenue = round(units * unit_price, 2)

            sales_records.append({
                "date": dt_str,
                "sku_id": sku_id,
                "units_sold": units,
                "revenue": revenue,
                "unit_price": unit_price,
                "promo_flag": is_promo
            })

    # Add intentional edge cases to test cleaning logic (CLN-02, CLN-03)
    # Add an accidental negative units sold (return)
    sales_records.append({
        "date": "2024-06-15",
        "sku_id": sku_ids[0],
        "units_sold": -3,
        "revenue": -1500.0,
        "unit_price": base_prices[sku_ids[0]],
        "promo_flag": 0
    })
    # Add duplicate daily entry
    sales_records.append(sales_records[10].copy())

    df_sales = pd.DataFrame(sales_records)
    df_sales.to_csv(sample_dir / "sales_daily.csv", index=False)
    logger.info(f"Generated sales_daily.csv ({len(df_sales)} transactions)")

    # 4. Inventory Snapshots (Latest cutoff: 2025-12-31)
    inv_records = []
    latest_date = "2025-12-31"

    for sku_id in sku_ids:
        clean_sku = sku_id.strip()
        lead_time = int(np.random.choice([7, 14, 21, 28, 35]))
        avg_weekly_demand = np.random.uniform(15, 60)

        # Diverse inventory states to populate all 4 quadrants
        state_seed = np.random.rand()
        if state_seed < 0.25:  # Stockout risk candidate (Low on-hand, high demand)
            on_hand = int(np.random.uniform(2, avg_weekly_demand * 0.5))
            on_order = int(np.random.uniform(0, 5))
        elif state_seed < 0.50:  # Overstock candidate (High on-hand)
            on_hand = int(avg_weekly_demand * np.random.uniform(16, 28))
            on_order = int(avg_weekly_demand * 4)
        elif state_seed < 0.70:  # Watch / Volatile (High demand & borderline buffer)
            on_hand = int(avg_weekly_demand * 1.5)
            on_order = int(avg_weekly_demand * 8)
        else:  # Healthy
            on_hand = int(avg_weekly_demand * 4)
            on_order = int(avg_weekly_demand * 2)

        reorder_pt = int(avg_weekly_demand * (lead_time / 7.0) * 1.5)

        inv_records.append({
            "date": latest_date,
            "sku_id": clean_sku,
            "on_hand_units": on_hand,
            "on_order_units": on_order,
            "lead_time_days": lead_time,
            "reorder_point": reorder_pt
        })

    df_inv = pd.DataFrame(inv_records)
    df_inv.to_csv(sample_dir / "inventory_snapshots.csv", index=False)
    logger.info(f"Generated inventory_snapshots.csv ({len(df_inv)} records)")


if __name__ == "__main__":
    generate_sample_dataset()

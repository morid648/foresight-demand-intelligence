# Data Quality & Ingestion Profile Report — Project FORESIGHT

**Execution Timestamp:** 2026-09-23 20:07:43  
**Target Client:** NorthBay Living  
**Panel Grain:** Weekly SKU (`ISO Week`, `sku_id`)  

---

## 1. Raw Ingestion Profile

| Dataset | Row Count | Duplicate Key Violations | Missing / Null Fields |
|---|---|---|---|
| `sales_daily` | 25,893 | 2 | 0 |
| `sku_master` | 40 | 0 | 0 |
| `calendar` | 731 | 0 | 0 |
| `inventory_snapshots` | 40 | 0 | 0 |

**Cross-Table Coverage:**
- Sales SKU in Master Coverage: **100.0%**
- Unmapped Sales SKUs: **0**
- SKUs Missing Inventory Snapshot: **0**

---

## 2. Deterministic Cleaning Audit (Rules CLN-01 to CLN-05)

| Rule ID | Transformation Target | Issue Detected | Action Taken | Rows / Records Affected |
|---|---|---|---|---|
| **CLN-01** | `sku_master`, `sales_daily`, `inventory_snapshots` | Whitespace in SKU IDs and Categories | Stripped and standardized strings | Confirmed applied |
| **CLN-02** | `sales_daily.units_sold`, `revenue` | Negative sales / returns anomalies | Clipped negative values to 0 with audit log | 1 rows |
| **CLN-03** | `sales_daily` duplicate records | Duplicate daily entries for same SKU/date | Aggregated units sold and revenue | 4 duplicates |
| **CLN-04** | All tables date fields | Inconsistent date string formats | Parsed to strict UTC/ISO datetime | All dates standardized |
| **CLN-05** | `calendar.promo_event`, `sales_daily.promo_flag` | Null promo tags | Filled with default non-promo tags (0, 'None') | Standardized |

---

## 3. Analysis-Ready Weekly Panel Summary

- **Total Weekly Observations:** 3,741 rows
- **Unique Active SKUs:** 40
- **Unique Product Categories:** 4 (Bath, Bedding, Home Decor, Kitchen & Dining)
- **Time Horizon Span:** 2024-01-01 to 2025-12-29
- **Total Historical Units Sold:** 163,890
- **Total Historical Revenue:** ₹708,094,007.77

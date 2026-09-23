"""
Financial Impact and Rupee Valuation Engine for Project FORESIGHT.
Calculates sales-at-risk and capital-locked in Indian Rupees (INR / ₹).
"""

from typing import Union
import numpy as np


def calculate_sales_at_risk_inr(
    stockout_gap_units: Union[float, int],
    unit_selling_price: Union[float, int]
) -> float:
    """Calculates potential lost revenue due to projected stockouts.
    
    Formula: Sales at Risk (₹) = max(0, stockout_gap_units) * unit_selling_price
    """
    gap = max(0.0, float(stockout_gap_units))
    price = max(0.0, float(unit_selling_price))
    return float(round(gap * price, 2))


def calculate_capital_locked_inr(
    excess_overstock_units: Union[float, int],
    unit_cost: Union[float, int]
) -> float:
    """Calculates tied-up working capital in excess overstocked inventory.
    
    Formula: Capital Locked (₹) = max(0, excess_overstock_units) * unit_cost
    """
    excess = max(0.0, float(excess_overstock_units))
    cost = max(0.0, float(unit_cost))
    return float(round(excess * cost, 2))

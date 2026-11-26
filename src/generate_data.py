"""Generate a simulated sales dataset for an industrial supplies distributor.

The data is synthetic: it is built from fixed rules and a random seed so that
anyone can recreate exactly the same file. No real company data is used.

Output: data/orders.csv
"""
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
START = "2024-07-01"
END = "2026-06-30"  # two financial years (FY25 and FY26)

CATEGORIES = {
    # category: (base unit price AUD, freight cost as share of order value)
    "Survey Stakes": (4.50, 0.09),
    "Marking Paint": (11.00, 0.07),
    "Safety Signage": (38.00, 0.05),
    "Flagging Tape": (6.50, 0.06),
    "Steel Pegs": (9.00, 0.12),
    "Site Consumables": (22.00, 0.06),
}

REGIONS = {
    # region: (share of customers, extra freight multiplier)
    "WA": (0.45, 1.00),
    "QLD": (0.20, 1.60),
    "NSW": (0.15, 1.70),
    "SA": (0.10, 1.50),
    "NT": (0.10, 2.10),
}

SECTORS = ["Mining", "Construction", "Surveying", "Agriculture"]


def build_customers(rng: np.random.Generator, n: int = 60) -> pd.DataFrame:
    regions = rng.choice(list(REGIONS), size=n, p=[v[0] for v in REGIONS.values()])
    sectors = rng.choice(SECTORS, size=n, p=[0.45, 0.30, 0.15, 0.10])
    # A few large customers and many small ones (Pareto-like order sizes)
    size_factor = rng.pareto(2.2, size=n) + 0.5
    return pd.DataFrame(
        {
            "customer_id": [f"C{i:03d}" for i in range(1, n + 1)],
            "region": regions,
            "sector": sectors,
            "size_factor": size_factor.round(3),
        }
    )


def build_orders(rng: np.random.Generator, customers: pd.DataFrame) -> pd.DataFrame:
    days = pd.date_range(START, END, freq="D")
    rows = []
    order_no = 100000
    for day in days:
        if day.weekday() >= 5:  # no weekend orders
            continue
        months_in = (day.year - 2024) * 12 + day.month - 7
        growth = 1 + 0.012 * months_in  # ~15% a year
        season = 0.75 if day.month in (12, 1) else 1.0  # Christmas shutdown
        n_orders = rng.poisson(5 * growth * season)
        for _ in range(n_orders):
            cust = customers.sample(1, weights="size_factor", random_state=rng).iloc[0]
            category = rng.choice(list(CATEGORIES))
            unit_price, freight_share = CATEGORIES[category]
            qty = int(max(1, rng.lognormal(mean=3.6, sigma=0.8) * cust.size_factor / 2))
            price = round(unit_price * rng.uniform(0.92, 1.08), 2)
            revenue = round(qty * price, 2)
            freight = round(revenue * freight_share * REGIONS[cust.region][1] * rng.uniform(0.8, 1.2), 2)
            order_no += 1
            rows.append(
                {
                    "order_id": f"SO{order_no}",
                    "order_date": day.date().isoformat(),
                    "customer_id": cust.customer_id,
                    "region": cust.region,
                    "sector": cust.sector,
                    "category": category,
                    "quantity": qty,
                    "unit_price": price,
                    "revenue": revenue,
                    "freight_cost": freight,
                }
            )
    return pd.DataFrame(rows)


def main() -> None:
    rng = np.random.default_rng(SEED)
    customers = build_customers(rng)
    orders = build_orders(rng, customers)
    out = Path(__file__).resolve().parents[1] / "data" / "orders.csv"
    out.parent.mkdir(exist_ok=True)
    orders.to_csv(out, index=False)
    print(f"Wrote {len(orders):,} orders for {orders.customer_id.nunique()} customers to {out}")


if __name__ == "__main__":
    main()

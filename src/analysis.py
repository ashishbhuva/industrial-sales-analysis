"""Sales performance analysis for a (simulated) industrial supplies distributor.

Answers five business questions:
  1. How is revenue trending month to month, and how did FY26 compare to FY25?
  2. Which product categories drive revenue and margin after freight?
  3. How concentrated is revenue in the largest customers?
  4. Which regions carry the highest freight cost as a share of revenue?
  5. Which customer sectors are growing fastest?

Run: python src/generate_data.py && python src/analysis.py
Outputs: CSV summaries in outputs/ and a printed summary.
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"


def load() -> pd.DataFrame:
    df = pd.read_csv(ROOT / "data" / "orders.csv", parse_dates=["order_date"])
    # Australian financial year: July to June, named by the year it ends
    df["fy"] = "FY" + (df.order_date.dt.year + (df.order_date.dt.month >= 7)).astype(str).str[-2:]
    df["month"] = df.order_date.dt.to_period("M").astype(str)
    df["net_after_freight"] = df.revenue - df.freight_cost
    return df


def monthly_trend(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby("month").agg(revenue=("revenue", "sum"), orders=("order_id", "count")).round(2)


def fy_summary(df: pd.DataFrame) -> pd.DataFrame:
    s = df.groupby("fy").agg(
        revenue=("revenue", "sum"),
        orders=("order_id", "count"),
        customers=("customer_id", "nunique"),
        freight=("freight_cost", "sum"),
    )
    s["avg_order_value"] = s.revenue / s.orders
    s["freight_pct"] = 100 * s.freight / s.revenue
    s["revenue_growth_pct"] = 100 * s.revenue.pct_change()
    return s.round(2)


def category_mix(df: pd.DataFrame) -> pd.DataFrame:
    c = df.groupby("category").agg(revenue=("revenue", "sum"), net=("net_after_freight", "sum"))
    c["share_pct"] = 100 * c.revenue / c.revenue.sum()
    c["freight_pct"] = 100 * (c.revenue - c.net) / c.revenue
    return c.sort_values("revenue", ascending=False).round(2)


def customer_concentration(df: pd.DataFrame) -> dict:
    by_cust = df.groupby("customer_id").revenue.sum().sort_values(ascending=False)
    total = by_cust.sum()
    return {
        "customers": len(by_cust),
        "top5_share_pct": round(100 * by_cust.head(5).sum() / total, 1),
        "top10_share_pct": round(100 * by_cust.head(10).sum() / total, 1),
        "customers_for_80pct": int((by_cust.cumsum() / total < 0.8).sum() + 1),
    }


def region_freight(df: pd.DataFrame) -> pd.DataFrame:
    r = df.groupby("region").agg(revenue=("revenue", "sum"), freight=("freight_cost", "sum"))
    r["freight_pct"] = 100 * r.freight / r.revenue
    return r.sort_values("freight_pct", ascending=False).round(2)


def sector_growth(df: pd.DataFrame) -> pd.DataFrame:
    p = df.pivot_table(index="sector", columns="fy", values="revenue", aggfunc="sum")
    p["growth_pct"] = 100 * (p["FY26"] / p["FY25"] - 1)
    return p.sort_values("growth_pct", ascending=False).round(1)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    df = load()
    results = {
        "monthly_trend": monthly_trend(df),
        "fy_summary": fy_summary(df),
        "category_mix": category_mix(df),
        "region_freight": region_freight(df),
        "sector_growth": sector_growth(df),
    }
    for name, table in results.items():
        table.to_csv(OUT / f"{name}.csv")
        print(f"\n== {name} ==\n{table.to_string()}")
    print("\n== customer_concentration ==")
    for k, v in customer_concentration(df).items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Generate sample CSVs for two tables described in sample-tables.md:

1) leads.csv
   Columns:
   - lead_id (UUID string)
   - first_name (str)
   - last_name (str)
   - email (str)
   - phone_number (str)
   - source (categorical str)
   - status (categorical str)
   - created_at (YYYY-MM-DD HH:MM:SS)
   - assigned_to (int sales representative id)
   - region (categorical str)

2) sales.csv (links back to leads via lead_id)
   Columns:
   - sale_id (UUID string)
   - lead_id (UUID string; must exist in leads.csv)
   - product_id (str like PROD-###)
   - sale_amount (decimal string with 2 decimals)
   - sale_date (YYYY-MM-DD)
   - sales_rep_id (int)
   - payment_method (categorical str)

Usage:
  python backend/scripts/generate_sample_csv.py \
	--leads 2500 \
	--sales 2500 \
	--out .

By default generates 2500 rows for each table and writes to the current
working directory as leads.csv and sales.csv.
"""

from __future__ import annotations

import argparse
import csv
import random
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable, List


# --- Simple seedable generators for realistic-ish data ---
FIRST_NAMES = [
    "Olivia",
    "Liam",
    "Emma",
    "Noah",
    "Ava",
    "Elijah",
    "Sophia",
    "Lucas",
    "Isabella",
    "Mason",
    "Mia",
    "Ethan",
    "Charlotte",
    "Amelia",
    "James",
    "Benjamin",
    "Harper",
    "Evelyn",
    "Henry",
    "Alexander",
]

LAST_NAMES = [
    "Smith",
    "Johnson",
    "Williams",
    "Brown",
    "Jones",
    "Garcia",
    "Miller",
    "Davis",
    "Rodriguez",
    "Martinez",
    "Hernandez",
    "Lopez",
    "Gonzalez",
    "Wilson",
    "Anderson",
    "Thomas",
    "Taylor",
    "Moore",
    "Jackson",
    "Martin",
]

EMAIL_DOMAINS = [
    "example.com",
    "company.com",
    "business.org",
    "mail.net",
    "corp.co",
]

SOURCES = [
    "Website",
    "Referral",
    "Trade Show",
    "Social Media",
    "Email Campaign",
    "Advertisement",
]

STATUSES = ["New", "Contacted", "Qualified", "Unqualified"]

REGIONS = ["North America", "EMEA", "APAC"]

PAYMENT_METHODS = ["Credit Card", "Bank Transfer", "Cash", "PayPal"]


def rand_phone() -> str:
    """US-style phone like (555) 123-4567 or intl-like +44 20 7946 0958."""
    if random.random() < 0.75:
        a = random.randint(200, 999)
        b = random.randint(100, 999)
        c = random.randint(1000, 9999)
        return f"({a}) {b}-{c}"
    else:
        cc = random.choice(
            ["+44", "+49", "+33", "+34", "+61", "+81"]
        )  # UK/DE/FR/ES/AU/JP
        p1 = random.randint(10, 99)
        p2 = random.randint(1000, 9999)
        p3 = random.randint(1000, 9999)
        return f"{cc} {p1} {p2} {p3}"


def rand_created_at(start_year: int = 2022, end_year: int = 2025) -> datetime:
    start_dt = datetime(start_year, 1, 1, 0, 0, 0)
    end_dt = datetime(end_year, 12, 31, 23, 59, 59)
    delta = end_dt - start_dt
    offset = random.randint(0, int(delta.total_seconds()))
    return start_dt + timedelta(seconds=offset)


def rand_sale_date(from_dt: datetime, max_days_after: int = 365) -> date:
    d = from_dt.date() + timedelta(days=random.randint(0, max_days_after))
    return d


def slugify_email_local(first: str, last: str) -> str:
    return f"{first}.{last}".lower().replace("'", "").replace(" ", "")


def rand_product_id() -> str:
    return f"PROD-{random.randint(1, 999):03d}"


@dataclass
class Lead:
    lead_id: str
    first_name: str
    last_name: str
    email: str
    phone_number: str
    source: str
    status: str
    created_at: datetime
    assigned_to: int
    region: str


@dataclass
class Sale:
    sale_id: str
    lead_id: str
    product_id: str
    sale_amount: float
    sale_date: date
    sales_rep_id: int
    payment_method: str


def generate_leads(n: int, rep_ids: List[int]) -> List[Lead]:
    leads: List[Lead] = []
    for _ in range(n):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        domain = random.choice(EMAIL_DOMAINS)
        email_local = slugify_email_local(first, last)
        # add small chance of a numeric suffix to reduce collisions
        if random.random() < 0.15:
            email_local += str(random.randint(1, 999))
        email = f"{email_local}@{domain}"
        created_at = rand_created_at()
        lead = Lead(
            lead_id=str(uuid.uuid4()),
            first_name=first,
            last_name=last,
            email=email,
            phone_number=rand_phone(),
            source=random.choice(SOURCES),
            status=random.choice(STATUSES),
            created_at=created_at,
            assigned_to=random.choice(rep_ids),
            region=random.choice(REGIONS),
        )
        leads.append(lead)
    return leads


def generate_sales(n: int, leads: List[Lead], rep_ids: List[int]) -> List[Sale]:
    if not leads:
        raise ValueError("Leads list must not be empty to generate sales")

    sales: List[Sale] = []
    # Choose unique leads for sales if possible; allow multiple sales per lead when needed
    chosen_leads = random.sample(leads, k=min(n, len(leads)))
    while len(chosen_leads) < n:
        chosen_leads.append(random.choice(leads))

    for i in range(n):
        lead = chosen_leads[i]
        # 70% chance the closing rep is the same as assigned_to, else random rep
        if random.random() < 0.7:
            sales_rep_id = lead.assigned_to
        else:
            sales_rep_id = random.choice(rep_ids)
        # sale date at or after lead.created_at
        sdate = rand_sale_date(lead.created_at)
        amount = round(random.uniform(100.0, 20000.0), 2)
        sale = Sale(
            sale_id=str(uuid.uuid4()),
            lead_id=lead.lead_id,
            product_id=rand_product_id(),
            sale_amount=amount,
            sale_date=sdate,
            sales_rep_id=sales_rep_id,
            payment_method=random.choice(PAYMENT_METHODS),
        )
        sales.append(sale)
    return sales


def write_leads_csv(leads: Iterable[Lead], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "lead_id",
                "first_name",
                "last_name",
                "email",
                "phone_number",
                "source",
                "status",
                "created_at",
                "assigned_to",
                "region",
            ]
        )
        for lead in leads:
            writer.writerow(
                [
                    lead.lead_id,
                    lead.first_name,
                    lead.last_name,
                    lead.email,
                    lead.phone_number,
                    lead.source,
                    lead.status,
                    lead.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    lead.assigned_to,
                    lead.region,
                ]
            )


def write_sales_csv(sales: Iterable[Sale], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "sale_id",
                "lead_id",
                "product_id",
                "sale_amount",
                "sale_date",
                "sales_rep_id",
                "payment_method",
            ]
        )
        for s in sales:
            writer.writerow(
                [
                    s.sale_id,
                    s.lead_id,
                    s.product_id,
                    f"{s.sale_amount:.2f}",
                    s.sale_date.strftime("%Y-%m-%d"),
                    s.sales_rep_id,
                    s.payment_method,
                ]
            )


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate sample leads and sales CSVs")
    p.add_argument(
        "--leads", type=int, default=5000, help="Number of lead rows (>=2000)"
    )
    p.add_argument(
        "--sales", type=int, default=500, help="Number of sales rows (>=2000)"
    )
    p.add_argument(
        "--out", type=str, default=".", help="Output directory for CSV files"
    )
    p.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional random seed for reproducibility",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    if args.seed is not None:
        random.seed(args.seed)
    # Ensure minimums
    n_leads = max(2000, int(args.leads))
    n_sales = max(2000, int(args.sales))

    outdir = Path(args.out).resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    # Create a pool of sales reps as integers (100–199)
    rep_ids = list(range(100, 200))

    leads = generate_leads(n_leads, rep_ids)
    sales = generate_sales(n_sales, leads, rep_ids)

    write_leads_csv(leads, outdir / "leads.csv")
    write_sales_csv(sales, outdir / "sales.csv")

    print(f"Wrote {len(leads)} rows to {outdir / 'leads.csv'}")
    print(f"Wrote {len(sales)} rows to {outdir / 'sales.csv'}")


if __name__ == "__main__":
    main()

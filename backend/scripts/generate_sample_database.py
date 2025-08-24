#!/usr/bin/env python3
"""Generate two sample SQLite databases:

- sample_sales.db (leads + sales)
- sample_conversations.db (conversations + messages)

Run:
        python3 generate_sample_database.py

Options available via --help
"""

from __future__ import annotations

import argparse
import random
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Tuple


ROOT = Path(__file__).resolve().parent.parent
SALES_DB = ROOT / "sample_sales.db"
CONV_DB = ROOT / "sample_conversations.db"


FIRST_NAMES = [
    "John",
    "Sarah",
    "Michael",
    "Emily",
    "David",
    "Lisa",
    "Robert",
    "Jennifer",
    "Christopher",
    "Amanda",
    "Alex",
    "Olivia",
    "Ethan",
    "Sophia",
    "Daniel",
    "Grace",
]

LAST_NAMES = [
    "Smith",
    "Johnson",
    "Brown",
    "Davis",
    "Wilson",
    "Anderson",
    "Taylor",
    "Martinez",
    "Garcia",
    "Rodriguez",
    "Lee",
    "Walker",
    "Hall",
    "Allen",
]

COMPANIES = [
    "TechCorp Inc",
    "InnovateCo",
    "GlobalTech Solutions",
    "Startup.io",
    "Corp Industries",
    "MidMarket Corp",
    "SmallBiz Solutions",
    "TechGiant Inc",
    "Enterprise Net",
    "NextGen Labs",
]

PRODUCTS = [
    "Basic Package",
    "Professional Suite",
    "Enterprise Package",
    "Consulting Hours",
]
LEAD_SOURCES = ["website", "referral", "cold_call", "social_media", "trade_show"]
SALE_STATUSES = ["completed", "pending", "refunded"]
PAYMENT_METHODS = ["credit_card", "bank_transfer", "invoice", "paypal"]

LOREM_WORDS = (
    "lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt"
    " ut labore et dolore magna aliqua".split()
)


def rand_name() -> Tuple[str, str]:
    return random.choice(FIRST_NAMES), random.choice(LAST_NAMES)


def rand_email(first: str, last: str, domain: str | None = None) -> str:
    if domain is None:
        domain = random.choice(["example.com", "acme.dev", "company.org", "mail.net"])
    num = "" if random.random() < 0.6 else str(random.randint(1, 99))
    user = f"{first}.{last}".lower()
    user = user.replace(" ", "")
    return f"{user}{num}@{domain}"


def rand_phone() -> str:
    return "+1-" + "".join(str(random.randint(0, 9)) for _ in range(7))


def rand_date(start: datetime, end: datetime) -> str:
    delta = end - start
    random_sec = random.randint(0, int(delta.total_seconds()))
    return (start + timedelta(seconds=random_sec)).date().isoformat()


def lorem_sentence(min_words=4, max_words=20) -> str:
    n = random.randint(min_words, max_words)
    words = [random.choice(LOREM_WORDS) for _ in range(n)]
    s = " ".join(words).capitalize() + "."
    return s


def create_sales_db(path: Path, num_leads: int, num_sales: int) -> None:
    if path.exists():
        path.unlink()

    conn = sqlite3.connect(str(path))
    cur = conn.cursor()

    cur.executescript(
        """
		CREATE TABLE leads (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			first_name TEXT NOT NULL,
			last_name TEXT NOT NULL,
			email TEXT UNIQUE NOT NULL,
			company TEXT,
			phone TEXT,
			lead_source TEXT,
			status TEXT DEFAULT 'new',
			created_date DATE NOT NULL,
			last_contact_date DATE,
			notes TEXT
		);

		CREATE TABLE sales (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			lead_id INTEGER,
			product_name TEXT NOT NULL,
			amount REAL NOT NULL,
			sale_date DATE NOT NULL,
			status TEXT DEFAULT 'pending',
			payment_method TEXT,
			salesperson TEXT,
			FOREIGN KEY (lead_id) REFERENCES leads(id)
		);
		"""
    )

    start_date = datetime(2023, 1, 1)
    end_date = datetime(2025, 12, 31)

    leads = []
    seen_emails = set()
    for _ in range(num_leads):
        first, last = rand_name()
        email = rand_email(first, last)
        # avoid exact duplicates
        i = 1
        base_email = email
        while email in seen_emails:
            i += 1
            email = base_email.replace("@", f"+{i}@")
        seen_emails.add(email)

        company = random.choice(COMPANIES)
        phone = rand_phone()
        lead_source = random.choice(LEAD_SOURCES)
        status = random.choice(["new", "contacted", "qualified", "lost"])
        created_date = rand_date(start_date, end_date)
        last_contact_date = (
            rand_date(datetime.fromisoformat(created_date), end_date)
            if random.random() < 0.7
            else None
        )
        notes = lorem_sentence(6, 25) if random.random() < 0.6 else ""

        leads.append(
            (
                first,
                last,
                email,
                company,
                phone,
                lead_source,
                status,
                created_date,
                last_contact_date,
                notes,
            )
        )

    cur.executemany(
        """
		INSERT INTO leads (first_name, last_name, email, company, phone, lead_source, status, created_date, last_contact_date, notes)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
		""",
        leads,
    )

    # Prepare sales entries. Randomly link to existing leads.
    sales = []
    salesperson_names = [
        f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        for _ in range(max(5, num_sales // 50))
    ]
    for _ in range(num_sales):
        lead_id = random.randint(1, num_leads)
        product = random.choice(PRODUCTS)
        # amount based on product
        base = {
            "Basic Package": 5000,
            "Professional Suite": 15000,
            "Enterprise Package": 30000,
            "Consulting Hours": 2000,
        }[product]
        amount = round(base * random.uniform(0.5, 1.5), 2)
        sale_date = rand_date(start_date, end_date)
        status = random.choices(SALE_STATUSES, weights=(80, 15, 5))[0]
        payment_method = random.choice(PAYMENT_METHODS)
        salesperson = random.choice(salesperson_names)

        sales.append(
            (lead_id, product, amount, sale_date, status, payment_method, salesperson)
        )

    cur.executemany(
        """
		INSERT INTO sales (lead_id, product_name, amount, sale_date, status, payment_method, salesperson)
		VALUES (?, ?, ?, ?, ?, ?, ?)
		""",
        sales,
    )

    # Indexes and a simple view
    cur.executescript(
        """
		CREATE INDEX idx_leads_email ON leads(email);
		CREATE INDEX idx_leads_status ON leads(status);
		CREATE INDEX idx_leads_created_date ON leads(created_date);
		CREATE INDEX idx_sales_sale_date ON sales(sale_date);
		CREATE INDEX idx_sales_status ON sales(status);
		CREATE INDEX idx_sales_lead_id ON sales(lead_id);

		CREATE VIEW IF NOT EXISTS sales_summary AS
		SELECT 
			s.id,
			l.first_name || ' ' || l.last_name as customer_name,
			l.company,
			s.product_name,
			s.amount,
			s.sale_date,
			s.status,
			s.salesperson
		FROM sales s
		JOIN leads l ON s.lead_id = l.id
		ORDER BY s.sale_date DESC;
		"""
    )

    conn.commit()
    conn.close()


def create_conversations_db(
    path: Path, num_conversations: int, avg_messages: int
) -> None:
    if path.exists():
        path.unlink()

    conn = sqlite3.connect(str(path))
    cur = conn.cursor()

    cur.executescript(
        """
		CREATE TABLE conversations (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			title TEXT,
			started_at DATE,
			participants TEXT,
			last_message_at DATE
		);

		CREATE TABLE messages (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			conversation_id INTEGER,
			sender TEXT,
			content TEXT,
			sent_at DATETIME,
			is_read INTEGER DEFAULT 0,
			FOREIGN KEY (conversation_id) REFERENCES conversations(id)
		);
		"""
    )

    start_date = datetime(2023, 1, 1)
    end_date = datetime(2025, 12, 31)

    conversations = []
    messages = []

    for i in range(num_conversations):
        # create a plausible title and participants
        pcount = random.randint(2, 6)
        participants = []
        for _ in range(pcount):
            first, last = rand_name()
            participants.append(f"{first} {last}")

        title = f"Conversation about {random.choice(PRODUCTS)}"
        started_at = rand_date(start_date, end_date)
        # generate messages around started_at
        last_message_time = datetime.fromisoformat(started_at) + timedelta(
            days=random.randint(0, 90)
        )

        conversations.append(
            (
                title,
                started_at,
                ", ".join(participants),
                last_message_time.date().isoformat(),
            )
        )

    cur.executemany(
        "INSERT INTO conversations (title, started_at, participants, last_message_at) VALUES (?, ?, ?, ?);",
        conversations,
    )

    # Fetch conversation ids range
    cur.execute("SELECT id, started_at FROM conversations")
    conv_rows = cur.fetchall()

    for conv_id, started_at in conv_rows:
        started = datetime.fromisoformat(started_at)
        n_messages = max(1, int(random.gauss(avg_messages, avg_messages * 0.5)))
        for _ in range(n_messages):
            sender = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
            sent_at = started + timedelta(
                days=random.randint(0, 180), seconds=random.randint(0, 86400)
            )
            content = lorem_sentence(3, 30)
            is_read = 1 if random.random() < 0.7 else 0
            messages.append(
                (conv_id, sender, content, sent_at.isoformat(sep=" "), is_read)
            )

    cur.executemany(
        "INSERT INTO messages (conversation_id, sender, content, sent_at, is_read) VALUES (?, ?, ?, ?, ?);",
        messages,
    )

    cur.executescript(
        """
		CREATE INDEX idx_conv_started ON conversations(started_at);
		CREATE INDEX idx_msg_conv ON messages(conversation_id);
		CREATE INDEX idx_msg_sent_at ON messages(sent_at);
		"""
    )

    conn.commit()
    conn.close()


def print_summary_sales_db(path: Path) -> None:
    conn = sqlite3.connect(str(path))
    cur = conn.cursor()
    print(f"\nSales DB: {path}")
    cur.execute("SELECT COUNT(*) FROM leads")
    print("Leads count:", cur.fetchone()[0])
    cur.execute("SELECT COUNT(*) FROM sales")
    print("Sales count:", cur.fetchone()[0])
    print("\nRecent sales:")
    cur.execute(
        "SELECT customer_name, product_name, amount, sale_date, status FROM sales_summary LIMIT 5;"
    )
    for row in cur.fetchall():
        print(row)
    conn.close()


def print_summary_conv_db(path: Path) -> None:
    conn = sqlite3.connect(str(path))
    cur = conn.cursor()
    print(f"\nConversations DB: {path}")
    cur.execute("SELECT COUNT(*) FROM conversations")
    print("Conversations:", cur.fetchone()[0])
    cur.execute("SELECT COUNT(*) FROM messages")
    print("Messages:", cur.fetchone()[0])
    print("\nSample messages:")
    cur.execute(
        "SELECT conversation_id, sender, content, sent_at FROM messages ORDER BY sent_at DESC LIMIT 5;"
    )
    for row in cur.fetchall():
        print(row)
    conn.close()


def parse_args():
    p = argparse.ArgumentParser(
        description="Generate sample SQLite databases for sales and conversations"
    )
    p.add_argument(
        "--leads", type=int, default=1000, help="Number of leads to generate"
    )
    p.add_argument(
        "--sales", type=int, default=800, help="Number of sales rows to generate"
    )
    p.add_argument(
        "--conversations",
        type=int,
        default=300,
        help="Number of conversations to generate",
    )
    p.add_argument(
        "--avg-messages", type=int, default=20, help="Average messages per conversation"
    )
    return p.parse_args()


def main():
    args = parse_args()

    print("Creating sample databases...")
    create_sales_db(SALES_DB, args.leads, args.sales)
    create_conversations_db(CONV_DB, args.conversations, args.avg_messages)

    print_summary_sales_db(SALES_DB)
    print_summary_conv_db(CONV_DB)

    print("\nDone. You can inspect the DBs with: sqlite3", SALES_DB, "and", CONV_DB)


if __name__ == "__main__":
    main()

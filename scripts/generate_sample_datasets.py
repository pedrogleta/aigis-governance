#!/usr/bin/env python3
"""
Script to generate sample sales data CSV files for testing and development purposes.
Generates realistic business data including customer information, sales details, UTM tracking, and more.
"""

import csv
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
import argparse
import os


class SalesDataGenerator:
    """Generates realistic sales data for testing and development."""

    def __init__(self):
        # Customer data pools
        self.first_names = [
            "James",
            "Mary",
            "John",
            "Patricia",
            "Robert",
            "Jennifer",
            "Michael",
            "Linda",
            "William",
            "Elizabeth",
            "David",
            "Barbara",
            "Richard",
            "Susan",
            "Joseph",
            "Jessica",
            "Thomas",
            "Sarah",
            "Christopher",
            "Karen",
            "Charles",
            "Nancy",
            "Daniel",
            "Lisa",
            "Matthew",
            "Betty",
            "Anthony",
            "Helen",
            "Mark",
            "Sandra",
            "Donald",
            "Donna",
            "Steven",
            "Carol",
            "Paul",
            "Ruth",
            "Andrew",
            "Sharon",
            "Joshua",
            "Michelle",
            "Kenneth",
            "Laura",
            "Kevin",
            "Emily",
            "Brian",
            "Kimberly",
            "George",
            "Deborah",
            "Edward",
            "Dorothy",
            "Ronald",
            "Lisa",
            "Timothy",
            "Nancy",
            "Jason",
            "Karen",
            "Jeffrey",
            "Betty",
            "Ryan",
            "Helen",
            "Jacob",
            "Sandra",
            "Gary",
            "Donna",
            "Nicholas",
            "Carol",
            "Eric",
            "Ruth",
            "Jonathan",
            "Julie",
            "Stephen",
            "Joyce",
            "Larry",
            "Virginia",
            "Justin",
            "Victoria",
            "Scott",
            "Kelly",
            "Brandon",
            "Lauren",
        ]

        self.last_names = [
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
            "Lee",
            "Perez",
            "Thompson",
            "White",
            "Harris",
            "Sanchez",
            "Clark",
            "Ramirez",
            "Lewis",
            "Robinson",
            "Walker",
            "Young",
            "Allen",
            "King",
            "Wright",
            "Scott",
            "Torres",
            "Nguyen",
            "Hill",
            "Flores",
            "Green",
            "Adams",
            "Nelson",
            "Baker",
            "Hall",
            "Rivera",
            "Campbell",
            "Mitchell",
            "Carter",
            "Roberts",
            "Gomez",
            "Phillips",
            "Evans",
            "Turner",
            "Diaz",
            "Parker",
            "Cruz",
            "Edwards",
            "Collins",
            "Reyes",
            "Stewart",
            "Morris",
            "Morales",
            "Murphy",
            "Cook",
            "Rogers",
            "Gutierrez",
            "Ortiz",
            "Morgan",
            "Cooper",
            "Peterson",
            "Bailey",
            "Reed",
            "Kelly",
            "Howard",
            "Ramos",
            "Kim",
            "Cox",
            "Ward",
            "Richardson",
            "Watson",
            "Brooks",
            "Chavez",
            "Wood",
            "James",
            "Bennett",
        ]

        self.companies = [
            "Acme Corp",
            "TechStart Inc",
            "Global Solutions",
            "Innovate Labs",
            "Peak Industries",
            "NextGen Systems",
            "Future Tech",
            "Digital Dynamics",
            "Smart Solutions",
            "Elite Corp",
            "Prime Technologies",
            "Advanced Systems",
            "Creative Solutions",
            "Dynamic Corp",
            "Elite Industries",
            "Global Tech",
            "Innovation Labs",
            "Peak Solutions",
            "Smart Systems",
            "Tech Elite",
            "Creative Corp",
            "Dynamic Solutions",
            "Elite Tech",
            "Global Industries",
            "Innovation Corp",
            "Peak Tech",
            "Smart Corp",
            "Tech Solutions",
            "Creative Industries",
            "Dynamic Tech",
            "Elite Systems",
        ]

        self.industries = [
            "Technology",
            "Healthcare",
            "Finance",
            "Retail",
            "Manufacturing",
            "Education",
            "Real Estate",
            "Transportation",
            "Energy",
            "Media",
            "Consulting",
            "Legal",
            "Construction",
            "Hospitality",
            "Agriculture",
            "Telecommunications",
            "Automotive",
            "Pharmaceuticals",
            "Entertainment",
            "Non-profit",
            "Government",
            "Insurance",
            "Marketing",
            "Human Resources",
            "Research",
            "Engineering",
            "Design",
            "Sales",
        ]

        self.products = [
            "Software License",
            "Cloud Service",
            "Hardware Equipment",
            "Consulting Package",
            "Training Program",
            "Support Contract",
            "Custom Development",
            "Data Analysis",
            "Security Audit",
            "Performance Review",
            "Strategic Planning",
            "Process Optimization",
            "Market Research",
            "Brand Development",
            "Digital Transformation",
            "Infrastructure Setup",
            "Compliance Review",
            "Risk Assessment",
            "Quality Assurance",
            "Project Management",
        ]

        self.sellers = [
            "Sarah Johnson",
            "Michael Chen",
            "Emily Rodriguez",
            "David Kim",
            "Lisa Thompson",
            "Robert Martinez",
            "Jennifer Lee",
            "Christopher Brown",
            "Amanda Wilson",
            "James Davis",
            "Maria Garcia",
            "Daniel Anderson",
            "Jessica Taylor",
            "Kevin White",
            "Rachel Green",
            "Andrew Clark",
            "Nicole Hall",
            "Ryan Lewis",
            "Stephanie Walker",
            "Brian Hall",
        ]

        self.utm_sources = [
            "google",
            "facebook",
            "linkedin",
            "twitter",
            "instagram",
            "youtube",
            "bing",
            "email",
            "direct",
            "referral",
            "organic",
            "paid_search",
            "social_media",
            "content_marketing",
            "affiliate",
            "partner",
            "trade_show",
            "webinar",
            "podcast",
            "blog",
            "newsletter",
            "cold_outreach",
            "warm_intro",
            "customer_referral",
        ]

        self.utm_mediums = [
            "cpc",
            "social",
            "email",
            "organic",
            "referral",
            "banner",
            "video",
            "display",
            "affiliate",
            "content",
            "newsletter",
            "webinar",
            "podcast",
            "blog",
            "cold_email",
            "warm_intro",
            "trade_show",
            "conference",
            "direct_mail",
            "telemarketing",
        ]

        self.utm_campaigns = [
            "summer_sale_2024",
            "product_launch",
            "holiday_promotion",
            "customer_retention",
            "new_feature_announcement",
            "referral_program",
            "enterprise_sales",
            "startup_focus",
            "industry_specific",
            "geographic_expansion",
            "competitive_switch",
            "upgrade_promotion",
            "cross_sell",
            "upsell",
            "win_back",
            "brand_awareness",
            "lead_generation",
        ]

        self.countries = [
            "United States",
            "Canada",
            "United Kingdom",
            "Germany",
            "France",
            "Australia",
            "Japan",
            "Brazil",
            "India",
            "China",
            "Mexico",
            "Netherlands",
            "Switzerland",
            "Sweden",
            "Norway",
            "Denmark",
            "Finland",
            "Italy",
            "Spain",
            "Portugal",
        ]

        self.states = [
            "California",
            "Texas",
            "New York",
            "Florida",
            "Illinois",
            "Pennsylvania",
            "Ohio",
            "Georgia",
            "North Carolina",
            "Michigan",
            "New Jersey",
            "Virginia",
            "Washington",
            "Arizona",
            "Massachusetts",
            "Tennessee",
            "Indiana",
            "Missouri",
            "Maryland",
            "Colorado",
            "Wisconsin",
            "Minnesota",
            "South Carolina",
            "Alabama",
            "Louisiana",
            "Kentucky",
            "Oregon",
            "Oklahoma",
            "Connecticut",
            "Utah",
        ]

    def generate_customer_data(self) -> Dict[str, Any]:
        """Generate realistic customer information."""
        first_name = random.choice(self.first_names)
        last_name = random.choice(self.last_names)
        company = random.choice(self.companies)
        industry = random.choice(self.industries)
        country = random.choice(self.countries)
        state = random.choice(self.states) if country == "United States" else ""

        # Generate realistic email
        email_domains = [
            "gmail.com",
            "yahoo.com",
            "hotmail.com",
            "outlook.com",
            "company.com",
        ]
        if random.random() < 0.7:  # 70% use company email
            domain = f"{company.lower().replace(' ', '').replace('Inc', '').replace('Corp', '')}.com"
        else:
            domain = random.choice(email_domains)

        email = f"{first_name.lower()}.{last_name.lower()}@{domain}"

        # Generate phone number
        phone = f"+1-{random.randint(200, 999)}-{random.randint(200, 999)}-{random.randint(1000, 9999)}"

        return {
            "customer_name": f"{first_name} {last_name}",
            "email": email,
            "company": company,
            "industry": industry,
            "country": country,
            "state": state,
            "phone": phone,
            "company_size": random.choice(
                ["1-10", "11-50", "51-200", "201-1000", "1000+"]
            ),
            "customer_type": random.choice(
                ["Prospect", "Lead", "Customer", "Champion", "Decision Maker"]
            ),
        }

    def generate_sale_data(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate sale-specific information."""
        # Generate sale date within last 2 years
        end_date = datetime.now()
        start_date = end_date - timedelta(days=730)
        sale_date = start_date + timedelta(days=random.randint(0, 730))

        # Generate realistic deal values
        deal_stages = [
            "Qualified",
            "Proposal",
            "Negotiation",
            "Closed Won",
            "Closed Lost",
        ]
        deal_stage = random.choice(deal_stages)

        if deal_stage == "Closed Won":
            deal_value = random.randint(1000, 50000)
            if random.random() < 0.2:  # 20% enterprise deals
                deal_value = random.randint(50000, 500000)
        else:
            deal_value = random.randint(1000, 25000)

        # Generate UTM data
        utm_source = random.choice(self.utm_sources)
        utm_medium = random.choice(self.utm_mediums)
        utm_campaign = random.choice(self.utm_campaigns)

        # Generate additional tracking data
        lead_score = random.randint(1, 100)
        days_to_close = random.randint(1, 180) if deal_stage == "Closed Won" else None

        return {
            "sale_date": sale_date.strftime("%Y-%m-%d"),
            "deal_stage": deal_stage,
            "deal_value": deal_value,
            "seller": random.choice(self.sellers),
            "product": random.choice(self.products),
            "utm_source": utm_source,
            "utm_medium": utm_medium,
            "utm_campaign": utm_campaign,
            "lead_score": lead_score,
            "days_to_close": days_to_close,
            "sales_cycle_length": random.randint(7, 365),
            "deal_type": random.choice(
                ["New Business", "Upsell", "Cross-sell", "Renewal"]
            ),
            "payment_terms": random.choice(["Net 30", "Net 60", "Net 90", "Immediate"]),
            "discount_percentage": random.randint(0, 25)
            if random.random() < 0.3
            else 0,
        }

    def generate_record(self) -> Dict[str, Any]:
        """Generate a complete sales record."""
        customer_data = self.generate_customer_data()
        sale_data = self.generate_sale_data(customer_data)

        # Combine all data
        record = {**customer_data, **sale_data}

        # Add some derived fields
        record["total_revenue"] = record["deal_value"]
        if record["discount_percentage"] > 0:
            record["discount_amount"] = round(
                record["deal_value"] * (record["discount_percentage"] / 100), 2
            )
            record["net_revenue"] = record["deal_value"] - record["discount_amount"]
        else:
            record["discount_amount"] = 0
            record["net_revenue"] = record["deal_value"]

        # Add timestamp
        record["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return record

    def generate_dataset(self, num_records: int = 1000) -> List[Dict[str, Any]]:
        """Generate a complete dataset."""
        print(f"Generating {num_records} sales records...")

        records = []
        for i in range(num_records):
            if (i + 1) % 100 == 0:
                print(f"Generated {i + 1} records...")
            records.append(self.generate_record())

        print(f"Dataset generation complete! Generated {len(records)} records.")
        return records

    def save_to_csv(self, records: List[Dict[str, Any]], filename: str):
        """Save records to CSV file."""
        if not records:
            print("No records to save.")
            return

        # Get fieldnames from first record
        fieldnames = list(records[0].keys())

        with open(filename, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)

        print(f"Data saved to {filename}")
        print(f"Total records: {len(records)}")
        print(f"Total fields: {len(fieldnames)}")


def main():
    """Main function to run the data generation script."""
    parser = argparse.ArgumentParser(description="Generate sample sales data CSV files")
    parser.add_argument(
        "--records",
        "-r",
        type=int,
        default=1000,
        help="Number of records to generate (default: 1000)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="sales_data.csv",
        help="Output filename (default: sales_data.csv)",
    )
    parser.add_argument(
        "--seed", "-s", type=int, help="Random seed for reproducible results"
    )

    args = parser.parse_args()

    # Set random seed if provided
    if args.seed is not None:
        random.seed(args.seed)
        print(f"Using random seed: {args.seed}")

    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")

    # Generate data
    generator = SalesDataGenerator()
    records = generator.generate_dataset(args.records)

    # Save to CSV
    generator.save_to_csv(records, args.output)

    # Print sample of generated data
    print("\nSample of generated data:")
    print("=" * 80)
    for i, record in enumerate(records[:3]):
        print(f"Record {i + 1}:")
        for key, value in record.items():
            print(f"  {key}: {value}")
        print()


if __name__ == "__main__":
    main()

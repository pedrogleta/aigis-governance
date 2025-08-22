#!/bin/bash

# Generate Sample SQLite Database Script
# Creates a sample database with sales and leads data including dates

# Set variables
DB_NAME="sample_sales.db"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DB_PATH="$SCRIPT_DIR/../$DB_NAME"

echo "Creating sample SQLite database: $DB_PATH"

# Remove existing database if it exists
if [ -f "$DB_PATH" ]; then
    echo "Removing existing database..."
    rm "$DB_PATH"
fi

# Create SQL script for database setup
cat > /tmp/setup_db.sql << 'EOF'
-- Create leads table
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

-- Create sales table
CREATE TABLE sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id INTEGER,
    product_name TEXT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    sale_date DATE NOT NULL,
    status TEXT DEFAULT 'pending',
    payment_method TEXT,
    salesperson TEXT,
    FOREIGN KEY (lead_id) REFERENCES leads(id)
);

-- Insert sample leads data
INSERT INTO leads (first_name, last_name, email, company, phone, lead_source, status, created_date, last_contact_date, notes) VALUES
('John', 'Smith', 'john.smith@email.com', 'TechCorp Inc', '+1-555-0101', 'website', 'qualified', '2024-01-15', '2024-01-20', 'Interested in enterprise solution'),
('Sarah', 'Johnson', 'sarah.j@techstart.com', 'TechStart LLC', '+1-555-0102', 'referral', 'new', '2024-01-18', NULL, 'Referred by existing customer'),
('Michael', 'Brown', 'mike.brown@innovate.co', 'InnovateCo', '+1-555-0103', 'cold_call', 'contacted', '2024-01-20', '2024-01-22', 'Follow up scheduled'),
('Emily', 'Davis', 'emily.davis@globaltech.com', 'GlobalTech Solutions', '+1-555-0104', 'website', 'qualified', '2024-01-22', '2024-01-25', 'Decision maker identified'),
('David', 'Wilson', 'david.wilson@startup.io', 'Startup.io', '+1-555-0105', 'social_media', 'new', '2024-01-25', NULL, 'Found through LinkedIn'),
('Lisa', 'Anderson', 'lisa.anderson@corp.com', 'Corp Industries', '+1-555-0106', 'trade_show', 'qualified', '2024-01-28', '2024-01-30', 'Met at TechExpo 2024'),
('Robert', 'Taylor', 'robert.t@enterprise.net', 'Enterprise Net', '+1-555-0107', 'website', 'contacted', '2024-02-01', '2024-02-03', 'Requested demo'),
('Jennifer', 'Martinez', 'jen.martinez@smallbiz.com', 'SmallBiz Solutions', '+1-555-0108', 'referral', 'new', '2024-02-05', NULL, 'Referred by John Smith'),
('Christopher', 'Garcia', 'chris.garcia@midmarket.com', 'MidMarket Corp', '+1-555-0109', 'cold_call', 'qualified', '2024-02-08', '2024-02-10', 'Budget approved'),
('Amanda', 'Rodriguez', 'amanda.r@techgiant.com', 'TechGiant Inc', '+1-555-0110', 'website', 'contacted', '2024-02-12', '2024-02-15', 'Technical requirements discussed');

-- Insert sample sales data
INSERT INTO sales (lead_id, product_name, amount, sale_date, status, payment_method, salesperson) VALUES
(1, 'Enterprise Package', 25000.00, '2024-01-25', 'completed', 'credit_card', 'Alex Johnson'),
(4, 'Professional Suite', 12000.00, '2024-01-30', 'completed', 'bank_transfer', 'Alex Johnson'),
(6, 'Basic Package', 5000.00, '2024-02-05', 'completed', 'credit_card', 'Sarah Williams'),
(9, 'Enterprise Package', 30000.00, '2024-02-15', 'pending', 'invoice', 'Alex Johnson'),
(7, 'Professional Suite', 15000.00, '2024-02-18', 'completed', 'credit_card', 'Sarah Williams'),
(3, 'Basic Package', 8000.00, '2024-02-20', 'completed', 'bank_transfer', 'Mike Chen'),
(2, 'Professional Suite', 18000.00, '2024-02-22', 'pending', 'invoice', 'Sarah Williams'),
(5, 'Basic Package', 6000.00, '2024-02-25', 'completed', 'credit_card', 'Mike Chen'),
(8, 'Professional Suite', 14000.00, '2024-02-28', 'completed', 'bank_transfer', 'Alex Johnson'),
(10, 'Enterprise Package', 35000.00, '2024-03-01', 'pending', 'invoice', 'Alex Johnson');

-- Create indexes for better performance
CREATE INDEX idx_leads_email ON leads(email);
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_leads_created_date ON leads(created_date);
CREATE INDEX idx_sales_sale_date ON sales(sale_date);
CREATE INDEX idx_sales_status ON sales(status);
CREATE INDEX idx_sales_lead_id ON sales(lead_id);

-- Create a view for sales summary
CREATE VIEW sales_summary AS
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
EOF

# Execute the SQL script to create the database
echo "Setting up database schema and inserting sample data..."
sqlite3 "$DB_PATH" < /tmp/setup_db.sql

# Clean up temporary file
rm /tmp/setup_db.sql

# Verify the database was created and show some sample data
if [ -f "$DB_PATH" ]; then
    echo "✅ Database created successfully!"
    echo ""
    echo "📊 Sample data summary:"
    echo "------------------------"
    
    # Show table counts
    echo "Leads count: $(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM leads;")"
    echo "Sales count: $(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM sales;")"
    echo ""
    
    # Show recent sales
    echo "🛒 Recent sales:"
    sqlite3 "$DB_PATH" "SELECT customer_name, product_name, amount, sale_date, status FROM sales_summary LIMIT 5;" | while IFS='|' read -r customer product amount date status; do
        printf "%-25s %-20s $%-10s %-12s %-12s\n" "$customer" "$product" "$amount" "$date" "$status"
    done
    
    echo ""
    echo "📈 Sales by status:"
    sqlite3 "$DB_PATH" "SELECT status, COUNT(*) as count, SUM(amount) as total FROM sales GROUP BY status;" | while IFS='|' read -r status count total; do
        printf "%-12s %-8s $%-12s\n" "$status" "$count" "$total"
    done
    
    echo ""
    echo "🗓️  Date range:"
    echo "Earliest lead: $(sqlite3 "$DB_PATH" "SELECT MIN(created_date) FROM leads;")"
    echo "Latest sale: $(sqlite3 "$DB_PATH" "SELECT MAX(sale_date) FROM sales;")"
    
    echo ""
    echo "💾 Database location: $DB_PATH"
    echo "🔍 You can explore the database using: sqlite3 $DB_PATH"
    
else
    echo "❌ Error: Failed to create database"
    exit 1
fi

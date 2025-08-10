#!/usr/bin/env python3
"""
Simple Flask backend for testing the React frontend.
This simulates the AI Agent system responses.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid
import time
import json

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend development

# Simulate agent responses
MOCK_RESPONSES = {
    "sales": {
        "content": "I've analyzed your sales data from BigQuery. Here are the key insights:\n\n• Total sales in Q4: $2.4M\n• Top performing product: Product A ($450K)\n• Sales growth: +15% vs Q3\n• Peak sales day: December 15th",
        "plots": ["sales_trends_q4.png", "product_performance.png"],
        "code": """# Sales Analysis Code
import pandas as pd
import matplotlib.pyplot as plt

# Query sales data from BigQuery
query = '''
SELECT 
    date,
    product_name,
    sales_amount,
    region
FROM sales_data 
WHERE date >= '2024-10-01'
ORDER BY date
'''

df = pd.read_gbq(query, project_id='your-project')
print(f"Total sales: ${df['sales_amount'].sum():,.0f}")
print(f"Average daily sales: ${df.groupby('date')['sales_amount'].sum().mean():,.0f}")""",
    },
    "revenue": {
        "content": "Revenue analysis completed! Here's what I found in your BigQuery dataset:\n\n• Monthly recurring revenue: $180K\n• Customer lifetime value: $2,400\n• Churn rate: 3.2%\n• Revenue per customer: $150/month",
        "plots": ["revenue_trends.png", "customer_lifetime_value.png"],
        "code": """# Revenue Analysis
import pandas as pd
import numpy as np

# Calculate key metrics
revenue_data = pd.read_gbq('''
    SELECT 
        customer_id,
        subscription_date,
        monthly_revenue,
        churn_date
    FROM customer_subscriptions
    WHERE subscription_date >= '2023-01-01'
''')

# Calculate MRR
current_mrr = revenue_data[revenue_data['churn_date'].isna()]['monthly_revenue'].sum()
print(f"Current MRR: ${current_mrr:,.0f}")""",
    },
    "customers": {
        "content": "Customer analysis from your BigQuery dataset reveals:\n\n• Total active customers: 1,247\n• New customers this month: 89\n• Customer satisfaction score: 4.6/5\n• Top customer segment: Enterprise (45%)",
        "plots": ["customer_growth.png", "satisfaction_scores.png"],
        "code": """# Customer Analysis
import pandas as pd
import seaborn as sns

# Get customer data
customers = pd.read_gbq('''
    SELECT 
        customer_id,
        segment,
        satisfaction_score,
        signup_date,
        total_spend
    FROM customers 
    WHERE status = 'active'
''')

print(f"Total customers: {len(customers)}")
print(f"Average satisfaction: {customers['satisfaction_score'].mean():.1f}/5")
print(f"Top segment: {customers['segment'].mode().iloc[0]}")""",
    },
}


@app.route("/health")
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "aigis-governance-backend"})


@app.route("/api/health/bigquery")
def bigquery_health():
    """BigQuery connection health check"""
    return jsonify(
        {"status": "connected", "database": "BigQuery", "connection": "active"}
    )


@app.route("/api/chat", methods=["POST"])
def chat():
    """Main chat endpoint that simulates AI agent responses"""
    try:
        data = request.get_json()
        message = data.get("message", "").lower()
        session_id = data.get("sessionId") or str(uuid.uuid4())

        # Simulate processing time
        time.sleep(1.5)

        # Generate response based on keywords
        response_content = (
            "I've analyzed your BigQuery dataset. Here are some insights..."
        )
        response_plots = []
        response_code = ""

        if any(keyword in message for keyword in ["sales", "revenue", "money"]):
            if "sales" in message:
                response = MOCK_RESPONSES["sales"]
            elif "revenue" in message:
                response = MOCK_RESPONSES["revenue"]
            else:
                response = MOCK_RESPONSES["sales"]

            response_content = response["content"]
            response_plots = response["plots"]
            response_code = response["code"]

        elif any(keyword in message for keyword in ["customer", "user", "client"]):
            response = MOCK_RESPONSES["customers"]
            response_content = response["content"]
            response_plots = response["plots"]
            response_code = response["code"]

        elif "plot" in message or "chart" in message or "visualization" in message:
            response_content = "I'll create some visualizations for you based on your BigQuery data. Here are the plots I generated:"
            response_plots = ["sample_chart_1.png", "data_visualization.png"]
            response_code = """# Visualization Code
import matplotlib.pyplot as plt
import seaborn as sns

# Create sample visualization
plt.figure(figsize=(10, 6))
plt.title('Sample Data Visualization')
plt.xlabel('X Axis')
plt.ylabel('Y Axis')
plt.grid(True, alpha=0.3)
plt.show()"""

        else:
            response_content = f"I understand you're asking about: '{message}'. Let me query your BigQuery dataset to find relevant information. This might take a moment as I analyze the data structure and generate insights."

        return jsonify(
            {
                "content": response_content,
                "plots": response_plots,
                "code": response_code,
                "sessionId": session_id,
            }
        )

    except Exception as e:
        return jsonify(
            {
                "error": f"An error occurred: {str(e)}",
                "content": "Sorry, I encountered an error while processing your request. Please try again.",
                "sessionId": session_id
                if "session_id" in locals()
                else str(uuid.uuid4()),
            }
        ), 500


@app.route("/")
def index():
    """Root endpoint"""
    return jsonify(
        {
            "service": "Aigis Governance Backend",
            "version": "1.0.0",
            "endpoints": ["/health", "/api/health/bigquery", "/api/chat"],
        }
    )


if __name__ == "__main__":
    print("🚀 Starting Aigis Governance Backend...")
    print("📊 This is a mock backend for testing the React frontend")
    print("🔗 Frontend should connect to: http://localhost:5000")
    print("🌐 API endpoints available at: http://localhost:5000/api/*")
    print("\nTo test the full system:")
    print("1. Keep this backend running")
    print("2. Start the React frontend: cd frontend && npm run dev")
    print("3. Open http://localhost:5173 in your browser")
    print("\nPress Ctrl+C to stop the backend")

    app.run(debug=True, host="0.0.0.0", port=5000)

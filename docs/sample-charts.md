# Sample Charts

## Charts from the Leads Table

- **Lead Source Breakdown (Pie Chart or Bar Chart)**
    - **Purpose:** Understand which channels are most effective at generating leads.
    - **X-Axis / Segments:** source
    - **Y-Axis / Values:** Count of lead_id
    - **Insight:** Helps allocate marketing budget to the most successful channels.

- **Lead Status Funnel (Funnel Chart)**
    - **Purpose:** Visualize the conversion process from a new lead to a qualified one.
    - **Stages:** New, Contacted, Qualified, Unqualified
    - **Values:** Count of lead_id in each status.
    - **Insight:** Identifies bottlenecks in the sales process. For example, if many leads are stuck in the "Contacted" stage, it might indicate a need for better follow-up strategies.

- **Leads Generated Over Time (Line Chart)**
    - **Purpose:** Track lead generation trends.
    - **X-Axis:** created_at (grouped by day, week, or month)
    - **Y-Axis:** Count of lead_id
    - **Insight:** Shows seasonality or the impact of marketing campaigns on lead generation.

## Charts from the Sales Table

- **Sales Performance Over Time (Line or Bar Chart)**
    - **Purpose:** Monitor revenue trends.
    - **X-Axis:** sale_date (grouped by day, week, or month)
    - **Y-Axis:** Sum of sale_amount
    - **Insight:** Provides a clear view of revenue growth and helps in forecasting.

- **Top Sales Representatives (Bar Chart)**
    - **Purpose:** Identify top-performing sales team members.
    - **X-Axis:** sales_rep_id
    - **Y-Axis:** Sum of sale_amount or Count of sale_id
    - **Insight:** Useful for performance reviews, commissions, and identifying best practices.

## Chart Combining Leads and Sales (JOIN)

- **Lead-to-Sale Conversion Rate by Source (Bar Chart)**
    - **Purpose:** Determine the quality of leads from different sources.
    - **How it works:** Join the leads table with the sales table on `leads.lead_id = sales.lead_id`.
    - **Calculation:**
        - For each source in the leads table, count the total number of leads.
        - For each source, count the number of leads that have a corresponding entry in the sales table (i.e., they converted).
        - Calculate the conversion rate: `(Number of Sales / Total Leads) * 100` for each source.
    - **X-Axis:** source (from the leads table)
    - **Y-Axis:** Conversion Rate (%)
    - **SQL Logic:**
        ```sql
        SELECT
                l.source,
                COUNT(l.lead_id) AS total_leads,
                COUNT(s.sale_id) AS total_sales,
                (COUNT(s.sale_id) * 100.0 / COUNT(l.lead_id)) AS conversion_rate
        FROM
                leads l
        LEFT JOIN
                sales s ON l.lead_id = s.lead_id
        GROUP BY
                l.source
        ORDER BY
                conversion_rate DESC;
        ```
    - **Insight:** Shows which channels produce not just the most leads, but the leads that are most likely to become paying customers. For example, "Referral" might have fewer total leads than "Website" but a much higher conversion rate, making it a very valuable channel.

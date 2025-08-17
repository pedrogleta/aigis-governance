# User Input: The user enters the query in main.py.

# Agent Receives Input: The agent in agent.py gets the query.

# Agent Reasoning (ReAct):

# Thought: "The user wants a plot. To make a plot, I first need data. The data seems to be about 'sales in the last 7 days'. I should query the database for this."

# Action: Use the nl_to_sql_tool.

# NL-to-SQL Tool:

# The tool gets the schema context.

# It generates a SQL query like: SELECT date, sales FROM sales_table WHERE date >= DATE('now', '-7 days');

# It executes the query and gets the data (e.g., a list of dates and sales figures).

# Agent Reasoning (ReAct):

# Thought: "I have the data now. The user asked for a 'bar plot'. I need to use the plotting tool to visualize this data."

# Action: Use the plotting_tool, passing it the retrieved data and the original query "make a bar plot of sales in the last 7 days".

# Plotting Tool:

# It calls the LLM with a prompt like:

# You are a Python data visualization expert. Given the following data and user request, write Python code using Matplotlib to generate a bar plot. Save the plot to a file named 'plot.png'.

# User Request: "make a bar plot of sales in the last 7 days"
# Data: [( '2023-10-20', 500), ('2023-10-21', 750), ...]

# Your Python code:

# The LLM generates the Matplotlib code.

# The tool executes the code, which saves plot.png.

# The tool returns the file path "plot.png".

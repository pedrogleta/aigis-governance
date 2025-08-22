LangChain Project: DB Queries & Plot Generation
This document outlines a project structure for a Python application using LangChain to interact with a database, answer natural language questions, and generate plots.
1. Project Philosophy
The core idea is to create a modular and scalable architecture. We'll use specific "tools" for each distinct task:
Schema & Sample Data Tool: To understand the database structure.
NL-to-SQL Tool: To query the database based on natural language.
NL-to-Python/Plotting Tool: To generate visualizations from query results.
These tools will be orchestrated by a LangChain "agent" that intelligently decides which tool to use based on the user's request.
2. Directory Structure
Here’s a recommended layout for your project:
/langchain-db-plotter
|
|-- /app
|   |-- __init__.py
|   |-- main.py             # Entry point for the application (e.g., a Streamlit or Flask app)
|   |-- agent.py            # Defines the main LangChain agent and tool orchestration
|   |-- chains.py           # Contains custom LangChain chains if needed
|
|-- /core
|   |-- __init__.py
|   |-- config.py           # Database connections, API keys, settings
|   |-- database.py         # Functions to connect to the database
|
|-- /tools
|   |-- __init__.py
|   |-- db_schema_tool.py   # Tool to get table schemas and sample rows
|   |-- nl_to_sql_tool.py   # Tool for converting natural language to SQL
|   |-- plotting_tool.py    # Tool for generating plots from data
|
|-- /prompts
|   |-- __init__.py
|   |-- system_prompts.py   # Stores prompt templates for the LLMs
|
|-- /notebooks
|   |-- 01_database_connection_test.ipynb
|   |-- 02_tool_testing.ipynb
|
|-- requirements.txt        # Project dependencies
|-- .env                    # Environment variables (API keys, DB credentials)
|-- README.md


3. Component Breakdown
/app
main.py: This is where you'll build the user interface. It could be a simple command-line interface, or a web app using a framework like Streamlit, Flask, or FastAPI. It will take user input and pass it to the agent.
agent.py: The brain of the operation. It will initialize the LLM and the tools. It uses a ReAct (Reasoning and Acting) framework to decide which tool to use. For example:
If the user asks "what data do you have?", it will select the db_schema_tool.
If the user asks "who is the top seller?", it will use the nl_to_sql_tool.
If the user asks "plot sales by region", it will first use nl_to_sql_tool to get the data and then pass the data and the original query to the plotting_tool.
/core
config.py: Manages all configuration. Using a library like pydantic for settings management is a good practice. It will load variables from the .env file.
database.py: Contains helper functions to establish and manage the database connection (e.g., using SQLAlchemy). This keeps your database logic separate and reusable.
/tools
db_schema_tool.py:
Functionality: Connects to the database, inspects the schema (table names, column names, types), and fetches a few sample rows from each table.
Output: A formatted string that describes the database structure, which is then passed to the LLM as context.
nl_to_sql_tool.py:
Functionality: This will likely use a pre-built LangChain chain like create_sql_query_chain. It takes the user's question and the database schema (from the first tool) to generate a SQL query.
Execution: It then executes the SQL query against the database and returns the result.
plotting_tool.py:
Functionality: This is a more complex tool. It will receive the data from the nl_to_sql_tool and the original user prompt. It will then feed this into another LLM call with a specific prompt designed to generate Python code (using a library like Matplotlib or Plotly).
Execution: It will execute the generated Python code (safely, using exec()) to save the plot as an image file (e.g., plot.png).
Output: The path to the generated image file, which can then be displayed in the UI.
/prompts
system_prompts.py: Storing your prompts here makes them easy to manage and version. You'll have prompts for:
The main agent's system message.
The prompt for the NL-to-SQL conversion.
A specific prompt for the plotting tool, instructing the LLM to write Python code for visualization.
4. Workflow Example: "make a bar plot of sales in the last 7 days"
User Input: The user enters the query in main.py.
Agent Receives Input: The agent in agent.py gets the query.
Agent Reasoning (ReAct):
Thought: "The user wants a plot. To make a plot, I first need data. The data seems to be about 'sales in the last 7 days'. I should query the database for this."
Action: Use the nl_to_sql_tool.
NL-to-SQL Tool:
The tool gets the schema context.
It generates a SQL query like: SELECT date, sales FROM sales_table WHERE date >= DATE('now', '-7 days');
It executes the query and gets the data (e.g., a list of dates and sales figures).
Agent Reasoning (ReAct):
Thought: "I have the data now. The user asked for a 'bar plot'. I need to use the plotting tool to visualize this data."
Action: Use the plotting_tool, passing it the retrieved data and the original query "make a bar plot of sales in the last 7 days".
Plotting Tool:
It calls the LLM with a prompt like:
You are a Python data visualization expert. Given the following data and user request, write Python code using Matplotlib to generate a bar plot. Save the plot to a file named 'plot.png'.

User Request: "make a bar plot of sales in the last 7 days"
Data: [( '2023-10-20', 500), ('2023-10-21', 750), ...]

Your Python code:


The LLM generates the Matplotlib code.
The tool executes the code, which saves plot.png.
The tool returns the file path "plot.png".
Final Output: The agent returns the file path to main.py, which then displays the image to the user.
This structure provides a clear separation of concerns and makes your project easier to debug, maintain, and extend.

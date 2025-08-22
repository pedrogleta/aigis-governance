from langchain_core.tools import tool



@tool
def ask_database(query: str):
    """Consults database based on natural language query"""

    # @@TODO get db_schema from state


@tool
def ask_analyst(query: str):
    """Asks for Data Analyst to build a plot with data you provide"""


tools = [ask_database, ask_analyst]

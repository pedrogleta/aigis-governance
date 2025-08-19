from langgraph.prebuilt import create_react_agent
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition

model = init_chat_model("deepseek-chat", model_provider="deepseek", temperature=0)
prompt = "You are a helpful assistant"


def get_weather(city: str) -> str:
    """Get weather from a given city."""
    return f"It's always sunny in {city}"


agent = create_react_agent(model=model, tools=[get_weather], prompt=prompt)
tools = [get_weather]

# model_with_tools = model.bind_tools(tools, parallel_tool_calls=False)

builder = StateGraph(MessagesState)

builder.add_node("tools", ToolNode(tools))

checkpoointer = InMemorySaver()


# agent.invoke({"topic": "computers"})

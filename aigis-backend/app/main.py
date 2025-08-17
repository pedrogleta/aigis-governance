from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_deepseek import ChatDeepSeek
import os
import uvicorn
from fastapi import FastAPI

load_dotenv(override=True)

app = FastAPI()

model = init_chat_model("deepseek-chat", model_provider="deepseek")


@app.get("/")
async def hello_world():
    prompt = ChatPromptTemplate.from_template("Tell em a short joke about {topic}")
    model = ChatDeepSeek(model="deepseek-chat")

    chain = prompt | model

    response = ""
    async for chunk in chain.astream({"topic": "computers"}):
        print(chunk.content, end="", flush=True)
        if isinstance(chunk.content, str):
            response += chunk.content
        else:
            response += str(chunk.content)

    return {"message": response}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

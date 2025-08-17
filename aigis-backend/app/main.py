from dotenv import load_dotenv
from .agent import agent

import uvicorn
from fastapi import FastAPI

load_dotenv(override=True)

app = FastAPI()


@app.get("/")
async def hello_world():
    response = agent.invoke(
        {"messages": [{"role": "user", "content": "What is the weather in sf?"}]}
    )

    return {"message": response}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

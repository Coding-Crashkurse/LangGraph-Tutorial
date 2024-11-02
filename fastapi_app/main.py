from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from langchain.schema import HumanMessage, AIMessage
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()
from agent import app as agent_app

app = FastAPI()


class ChatRequest(BaseModel):
    message: str
    chat_history: Optional[List[dict]] = None


@app.post("/chat")
async def chat(request: ChatRequest):
    user_message = request.message

    chat_history = []
    if request.chat_history:
        for msg in request.chat_history:
            if msg.get("role") == "human":
                chat_history.append(HumanMessage(content=msg["content"]))
            elif msg.get("role") == "assistant":
                chat_history.append(AIMessage(content=msg["content"]))

    chat_history.append(HumanMessage(content=user_message))

    input_data = {"messages": chat_history}
    result = await agent_app.ainvoke(input_data)

    messages = result.get("messages", [])
    response_text = None

    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and msg.content:
            response_text = msg.content
            break

    if response_text is None:
        response_text = "I'm sorry, I couldn't process your request."

    return JSONResponse(content={"response": response_text})

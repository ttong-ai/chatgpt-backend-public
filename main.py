from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from agent.core import get_chat_response
from agent.interfaces import ChatContext

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Default root endpoint
@app.get("/")
async def root():
    return {"message": "Hello world"}


@app.options("/chat")
async def chat_options():
    response = JSONResponse(content={})
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


@app.post("/chat")
async def chat(context: ChatContext):
    if not context.instructions:
        context.instructions = ""
    response, metadata = get_chat_response(
        context.message, context.context, context.instructions, context.metadata
    )
    return {"message": context.message, "response": response, "metadata": metadata}

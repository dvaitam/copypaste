from fastapi import FastAPI, Request
import httpx
from openai import OpenAI

client = OpenAI()


app = FastAPI()
TARGET_URL = "https://api.openai.com"

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy(request: Request, path: str):
  body = await request.json()
  print(body)
  response =  client.responses.create(model=body["model"],instructions=body["instructions"], input=body["input"] )
  print(response.json())
  return response.json()

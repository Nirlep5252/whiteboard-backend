import os
import jwt
from typing import Union
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from icecream import ic

load_dotenv()
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("auth")
async def auth(request: Request, call_next):
    bearer = request.headers.get("Authorization")
    if not bearer:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    token = bearer.split(" ")[1]

    public_key = os.environ.get("KEYCLOAK_PUBLIC_KEY")
    public_key = f"-----BEGIN PUBLIC KEY-----\n{public_key}\n-----END PUBLIC KEY-----"

    try:
        decoded = jwt.decode(
            token, public_key, algorithms=["RS256"], audience="account"
        )
        ic(decoded)
        request.state.auth = decoded
    except jwt.exceptions.PyJWTError:
        return JSONResponse(status_code=401, content={"message": "Invalid token"})

    return await call_next(request)


@app.get("/user")
def hello(request: Request):
    return {
        "email": request.state.auth["email"],
        "email_verified": request.state.auth["email_verified"],
        "name": request.state.auth["name"],
        "preferred_username": request.state.auth["preferred_username"],
    }


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}

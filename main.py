import os
import jwt
import databases
import sqlalchemy
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from icecream import ic

load_dotenv()

database_url = os.environ.get("DATABASE_URL")
if not database_url:
    print("ERROR: DATABASE_URL not set")
    exit(1)
database = databases.Database(database_url)

metadata = sqlalchemy.MetaData()

whiteboards = sqlalchemy.Table(
    "whiteboards",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("name", sqlalchemy.String),
    sqlalchemy.Column("owner", sqlalchemy.String),
    sqlalchemy.Column("created_at", sqlalchemy.DateTime),
)

engine = sqlalchemy.create_engine(database_url)
metadata.create_all(engine)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    print("connected to db")
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    print("disconnected from db")
    await database.disconnect()


@app.middleware("auth")
async def auth(request: Request, call_next):
    bearer = request.headers.get("Authorization")
    if not bearer:
        return JSONResponse(
            status_code=401, content={"message": "Missing Authorization header"}
        )
    token = bearer.split(" ")[1]

    public_key = os.environ.get("KEYCLOAK_PUBLIC_KEY")
    public_key = f"-----BEGIN PUBLIC KEY-----\n{public_key}\n-----END PUBLIC KEY-----"

    try:
        decoded = jwt.decode(
            token, public_key, algorithms=["RS256"], audience="account"
        )
        # ic(decoded)
        request.state.auth = decoded
    except jwt.exceptions.PyJWTError:
        return JSONResponse(status_code=401, content={"message": "Invalid token"})

    return await call_next(request)


@app.get("/user")
async def hello(request: Request):
    return {
        "email": request.state.auth["email"],
        "email_verified": request.state.auth["email_verified"],
        "name": request.state.auth["name"],
        "preferred_username": request.state.auth["preferred_username"],
    }


@app.get("/whiteboards")
async def get_whiteboards(request: Request):
    username = request.state.auth["preferred_username"]
    query = whiteboards.select().where(whiteboards.c.owner == username)
    return await database.fetch_all(query)


@app.post("/whiteboards/{name}")
async def create_whiteboard(request: Request, name: str):
    username = request.state.auth["preferred_username"]
    ic(name)
    if len(name) == 0:
        return JSONResponse(
            status_code=400, content={"message": "Name cannot be empty"}
        )
    query = whiteboards.insert().values(name=name, owner=username)
    return await database.execute(query)


@app.post("/whiteboards/{id}/delete")
async def delete_whiteboard(request: Request, id: int):
    ic(id)
    username = request.state.auth["preferred_username"]
    query = whiteboards.delete().where(
        whiteboards.c.id == id and whiteboards.c.owner == username
    )
    return await database.execute(query)

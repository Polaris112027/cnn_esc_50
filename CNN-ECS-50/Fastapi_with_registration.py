from fastapi import FastAPI, File, UploadFile, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from sqlalchemy import create_engine, Column, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import uvicorn
import subprocess
import os
import random
import string

DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    email = Column(String, primary_key=True, index=True)
    nick = Column(String)
    hashed_password = Column(String)

Base.metadata.create_all(bind=engine)


app = FastAPI()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(db, email: str):
    return db.query(User).filter(User.email == email).first()

def authenticate_user(db, email: str, password: str):
    user = get_user(db, email)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def generate_random_path(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    random_path1 = generate_random_path()
    response = RedirectResponse(url=f"/{random_path1}", status_code=status.HTTP_302_FOUND)
    return response

@app.post("/signup/")
async def signup(email: str = Form(...), nick: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = get_user(db, email)
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(password)
    new_user = User(email=email, nick=nick, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"msg": "User created successfully"}

@app.get("/", response_class=HTMLResponse)
async def main():
    content = """
    <html>
        <head>
            <title>Sign Up or Log In</title>
        </head>
        <body>
            <h1>Sign Up</h1>
            <form action="/signup/" method="post">
                <input name="email" type="email" placeholder="Email" required>
                <input name="nick" type="text" placeholder="Nick" required>
                <input name="password" type="password" placeholder="Password" required>
                <input type="submit" value="Sign Up">
            </form>
            <h1>Log In</h1>
            <form action="/token" method="post">
                <input name="username" type="email" placeholder="Email" required>
                <input name="password" type="password" placeholder="Password" required>
                <input type="submit" value="Log In">
            </form>
        </body>
    </html>
    """
    return content

@app.get("/{random_path1}", response_class=HTMLResponse)
async def upload_page():
    random_path2 = generate_random_path()
    content = """
    <html>
        <head>
            <title>Upload WAV File</title>
        </head>
        <body>
            <h1>Upload WAV File for Sound Classification</h1>
            <form action="/"""+f"{random_path2}"+"""/" enctype="multipart/form-data" method="post">
                <input name="file" type="file" accept=".wav">
                <input type="submit" value="Upload">
            </form>
        </body>
    </html>
    """
    return content

@app.post("/{random_path2}/")
async def upload_file(file: UploadFile = File(...)):
    os.makedirs("wav", exist_ok=True)
    file_location = f"wav/{file.filename}"
    with open(file_location, "wb") as buffer:
        buffer.write(await file.read())

    process_result = subprocess.run(["python", "Sound_classification.py", file.filename], capture_output=True)
    result = process_result.stdout.decode()

    return {"filename": file.filename, "result": result}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

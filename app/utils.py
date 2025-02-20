import time
from passlib.context import CryptContext
from jose import JWTError, jwt
from itsdangerous import URLSafeTimedSerializer
import datetime as dt
from sqlalchemy import Select
from fastapi import Depends,HTTPException,status
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from app import models, schemas
from settings import setting
from app.helper import JWTBearer
from fastapi_mail import FastMail,MessageSchema,MessageType,ConnectionConfig

conf = ConnectionConfig(
    MAIL_USERNAME = setting.MAIL_USERNAME,
    MAIL_FROM = setting.MAIL_FROM,
    MAIL_PASSWORD = setting.MAIL_PASSWORD,
    MAIL_PORT = setting.MAIL_PORT,
    MAIL_SERVER = setting.MAIL_SERVER,
    MAIL_FROM_NAME = setting.MAIL_FROM_NAME,
    MAIL_STARTTLS= True,
    MAIL_SSL_TLS= False,
    USE_CREDENTIALS= True,
    VALIDATE_CERTS= True
)

serializer = URLSafeTimedSerializer(
    secret_key=setting.SECRET_KEY,
    salt='Email configuration'
)
pwd_context = CryptContext(schemes=["bcrypt"],deprecated="auto")

    

def hash(password):
    return pwd_context.hash(password)

def verify_password(password,hashed_password):
    return pwd_context.verify(password,hashed_password)


oauth2_scheme = JWTBearer()

def create_token(_id: int, expiry_time: int) -> str:
    print("expiry_time", expiry_time)
    expire = dt.datetime.now() + dt.timedelta(seconds=expiry_time)
    payload = {"id": _id, "expires": expire.timestamp()}
    return jwt.encode(payload, setting.SECRET_KEY, setting.ALGORITHM)


def create_access_token(id: int):
    return create_token(id, setting.ACCESS_TOKEN_EXPIRE_MINUTES)


def create_refresh_token(id: int):
    return create_token(id, setting.REFRESH_TOKEN_EXPIRE_MINUTES)

async def verify_token(token: str) -> int:
    try:
        data = jwt.decode(token, setting.SECRET_KEY, setting.ALGORITHM)
        expire = data.get("expires")
        if expire is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No access token supplied",
            )
       
        if dt.datetime.now().timestamp() > expire:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Token expired!"
            )
        return data["id"]
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token"
        )
    
async def authenticate(
    access_token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
):
    if access_token is None:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user_id = await verify_token(access_token)

    try:
        statement = Select(models.User).where(models.User.id == user_id)
        results  = await db.execute(statement)
        user = results.scalars().one()
        return user
    except Exception as err:
        print(err)
        raise HTTPException(
            status_code=401, detail="failed to authenticate user"
        )
    

async def sendMail(email:str, subject:str, body:str):
    message = MessageSchema(
        subject=subject,
        body=body,
        recipients=[email],
        subtype=MessageType.html,
    )

    fm = FastMail(conf)
    await fm.send_message(message)
    return {'success':True}

def create_url_safe_token(data: dict):
    token = serializer.dumps(data)
    return token
def decode_url_safe_token(token: str):
    try:
        data = serializer.loads(token)
        expire = data.get("expires")
       
        if  expire is not None and dt.datetime.now().timestamp() > expire:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Token expired!"
            )
        return data
    except Exception as e:
        print("Error decoding token", e)
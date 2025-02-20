from fastapi import APIRouter, HTTPException, Request, Response,BackgroundTasks
from fastapi.responses import RedirectResponse
import httpx
from app import schemas,utils,models
from fastapi import Depends,status
from database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Select
from typing import List
from app.users.service import UserService
from settings import setting
import datetime as dt
from app.oauth import oauth,OAuthError



router = APIRouter(tags=["Authentication"], prefix="/auth")
UsersService = UserService()

@router.post("/register",status_code=status.HTTP_201_CREATED,response_model=schemas.UserOut)
async def create_user(user:schemas.User_create, bg:BackgroundTasks, db:AsyncSession = Depends(get_db)):
    token = utils.create_url_safe_token({"email":user.email})
    link = f'{setting.DOMAIN}/auth/verification?token={token}'
    body = f"<p>click on the link here {link} to verify your email </P>"
    new_user = await UsersService.create_user(user,db)
    bg.add_task(utils.sendMail,user.email,subject="Email Verification",body=body)
    return new_user

@router.post("/login", response_model=schemas.UserOut)
async def login(credentials: schemas.User_create, response:Response, db:AsyncSession = Depends(get_db)):
    user = await UsersService.get_user(db,credentials.email)
    if not user:
        raise HTTPException(
            detail="Invalid credentials.",
            status_code=status.HTTP_403_FORBIDDEN,
        )
    # Verify user's password
    if not utils.verify_password(credentials.password, user.password):
        raise HTTPException(
            detail="Invalid credentials.",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    access_token = utils.create_access_token(user.id)
    refresh_token = utils.create_refresh_token(user.id)
    user.refresh_token = refresh_token
    await db.commit()
    response.set_cookie(key='refresh_token', value=refresh_token,httponly=True,expires=86400, max_age=86400)
    return {**user.__dict__, 'access_token': access_token}

@router.get('/refresh',response_model=schemas.UserOut)
async def refresh(req:Request, db:AsyncSession = Depends(get_db)):
    token = req.cookies.get("refresh_token")
    if not token:
        raise HTTPException(
            detail="No refresh token found",
            status_code=status.HTTP_403_FORBIDDEN,
        )
    user = await UsersService.get_user_byRefresh(db, token)
    if not user:
        raise HTTPException(
            detail="Invalid token.",
            status_code=status.HTTP_403_FORBIDDEN,
        )
    userId = await utils.verify_token(token)
    access_token = await utils.create_access_token(userId)
    return {**user.__dict__, 'access_token': access_token}

@router.get('/verification')
async def verify_email(token:str, db:AsyncSession = Depends(get_db)):
    data = utils.decode_url_safe_token(token)
    await UsersService.update_user({'emailVerified':True},db,data.get('email'))
    return {"message":"email verification successful"}

@router.post('/new-password')
async def send_password_reset_mail(payload:schemas.EmailSchema, bg:BackgroundTasks, db:AsyncSession = Depends(get_db)):
    user = await UsersService.get_user(db,payload.email)
    if not user:
        raise HTTPException(
            detail="you dont have the permission",
            status_code=status.HTTP_401_UNAUTHORIZED,
            )
    expire = dt.datetime.now() + dt.timedelta(seconds=setting.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = utils.create_url_safe_token({"email": payload.email, "expires" : expire.timestamp()})
    link = f'{setting.DOMAIN}/auth/reset-password?token={token}'
    body = f"<p>click on the link here {link} to reset your password </P>"
    bg.add_task(utils.sendMail,user.email,subject="Reset Your Password",body=body)
    return {"message":"password reset link sent successfully"}

@router.post('/password-reset')
async def send_password_reset_mail(payload:schemas.Password_reset_schema, db:AsyncSession = Depends(get_db)):
    data = utils.decode_url_safe_token(payload.token)
    email = data.get("email")
    user = await UsersService.get_user(db,email)
    if not user:
        raise HTTPException(
            detail="you dont have the permission",
            status_code=status.HTTP_401_UNAUTHORIZED,
            )
    await UsersService.update_user({"password": payload.password},db, email)
    return {"message": "password reset successful"}

@router.get("/google")
async def google(req: Request):
    url = req.url_for("auth")
    print(url)
    return await oauth.google.authorize_redirect(req, url)

@router.get("/google-auth")
async def auth(req: Request, db: AsyncSession = Depends(get_db)):
    try:
        token = await oauth.google.authorize_access_token(req)
        user_ = token.get('userinfo')
        print(user_)
        provider = "google"
        email = user_.get('email')
        user_data = {
            'name': user_.get('name'),
            'email': email,
            'image': user_.get('picture'),
            'emailVerified': user_.get('email_verified'),
            'provider': provider,
        }
        existing_user = await UsersService.get_user(db,email)
        if existing_user and existing_user.provider == provider: 
            access_token = utils.create_access_token(existing_user.id)
            refresh_token = utils.create_refresh_token(existing_user.id)
            await UsersService.update_user({"refresh_token": refresh_token},db,existing_user.email)
            res = RedirectResponse(url=setting.DOMAIN)
            res.set_cookie(key='refresh_token', value=refresh_token,httponly=True,expires=86400, max_age=86400)
            return res
        if existing_user and existing_user.provider != provider :
            res = RedirectResponse(url=f'{setting.DOMAIN}?oauth_error=Email already in use with another provider')
            return res
        user =  await UsersService.create_user_oauth(user_data,db)
        access_token = utils.create_access_token(user.id)
        refresh_token = utils.create_refresh_token(user.id)
        await UsersService.update_user({"refresh_token": refresh_token},db,user.email)
        res = RedirectResponse(url=setting.DOMAIN)
        res.set_cookie(key='refresh_token', value=refresh_token,httponly=True,expires=86400, max_age=86400)
        return res
        
    except OAuthError :
        raise HTTPException(status_code=401, detail="Invalid authorization request")
    

@router.get("/github")
async def google():
    return RedirectResponse(f'https://github.com/login/oauth/authorize?client_id={setting.GITHUB_CLIENT_ID}',status_code=302)

@router.get("/github_auth")
async def github_auth(code:str, db:AsyncSession = Depends(get_db)):
    params = {
        'client_id':setting.GITHUB_CLIENT_ID,
        'client_secret':setting.GITHUB_CLIENT_SECRET,
        'code':code
    }
    headers = {'Accept': 'application/json'}
    async with httpx.AsyncClient() as client:
        response = await client.post(url='https://github.com/login/oauth/access_token',params=params,headers=headers)
    response_json = response.json()
    print(response_json)
    access_token = response_json['access_token']
    async with httpx.AsyncClient() as client:
        headers.update({'Authorization': f'Bearer {access_token}'})
        res = await client.get(url='https://api.github.com/user',headers=headers)
    user_info = res.json()
    provider = "github"
    email = user_info.get('email')
    user_data = {
        'name': user_info.get('name'),
        'email': email,
        'image': user_info.get('avatar_url'),
        'emailVerified': True,
        'provider': provider,
    }
    
    existing_user = await UsersService.get_user(db,email)
    if existing_user and existing_user.provider == provider: 
        access_token = utils.create_access_token(existing_user.id)
        refresh_token = utils.create_refresh_token(existing_user.id)
        await UsersService.update_user({"refresh_token": refresh_token},db,existing_user.email)
        res = RedirectResponse(url=setting.DOMAIN)
        res.set_cookie(key='refresh_token', value=refresh_token,httponly=True,expires=86400, max_age=86400)
        return res
    if existing_user and existing_user.provider != provider :
        res = RedirectResponse(url=f'{setting.DOMAIN}?oauth_error=Email already in use with another provider')
        return res
    user =  await UsersService.create_user_oauth(user_data,db)
    access_token = utils.create_access_token(user.id)
    refresh_token = utils.create_refresh_token(user.id)
    await UsersService.update_user({"refresh_token": refresh_token},db,user.email)
    res = RedirectResponse(url=setting.DOMAIN)
    res.set_cookie(key='refresh_token', value=refresh_token,httponly=True,expires=86400, max_age=86400)
    return res
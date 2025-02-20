from fastapi import HTTPException,status
from sqlalchemy import select,desc
from sqlalchemy.ext.asyncio import AsyncSession
from app import schemas, utils
from app.models import User

class UserService:
    async def get_all_users(self, session:AsyncSession):
        statement = select(User).order_by(desc(User.created_at))
        result = await session.execute(statement)
        return result.scalars().all()
    async def create_user_oauth(self,data:dict,session:AsyncSession):
        existing_user = await self.get_user(session,data['email'])
        if existing_user:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")
        new_user = User(**data)
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        return new_user
    
    async def get_user(self, session:AsyncSession,userEmail:str):
        statement = select(User).where(User.email == userEmail)
        result = await session.execute(statement)
        return result.scalars().first()
    
    async def get_user_byRefresh(self, session:AsyncSession,token:str):
        statement = select(User).where(User.refresh_token == token)
        result = await session.execute(statement)
        return result.scalars().first()

    async def create_user(self,data:schemas.User_create,session:AsyncSession):
        existing_user = await self.get_user(session,data.email)
        if existing_user:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")
        new_user = User(**data.model_dump())
        new_user.password = utils.hash(new_user.password)
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        return new_user
    
    async def update_user(self,update_data:dict,session:AsyncSession,userEmail:str):
        user_to_update = await self.get_user(session,userEmail)
        if user_to_update is not None:
            for k, v in update_data.items():
                setattr(user_to_update,k,v)
            await session.commit()
            return user_to_update
        else:
            return None
        
    async def delete_user(self, session, userEmail:str):
        user_to_delete = await self.get_user(session, userEmail)
        if user_to_delete is not None:
            await session.delete(user_to_delete)
            await session.commit()
            return {}
        else:
            return None
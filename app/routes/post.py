from fastapi import APIRouter,Depends
from app import utils,schemas,models

router = APIRouter(tags=["Posts"])

@router.get('/posts')
async def post(user:schemas.UserOut=Depends(utils.authenticate)):
    print(user.__dict__)
    return {"message":"retrieved posts"}
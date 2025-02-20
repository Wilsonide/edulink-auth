from sqlalchemy import TIMESTAMP, Integer, String,Boolean
from database import Base
from sqlalchemy.sql.expression import text
from sqlalchemy.orm import Mapped, mapped_column,relationship
from datetime import datetime

__allow__unmapped = True

class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String, nullable=False,)
    password: Mapped[str] = mapped_column(String, server_default='')
    provider: Mapped[str] = mapped_column(String, server_default= '')
    emailVerified: Mapped[bool] = mapped_column(Boolean,server_default='f')
    refresh_token: Mapped[str] = mapped_column(String,server_default='')
    image: Mapped[str] = mapped_column(String, server_default='')
    role: Mapped[str] = mapped_column(String, server_default=text('USER'))
    is_two_factor_enabled :Mapped[bool] = mapped_column(Boolean,server_default='f')
    created_at:Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True),server_default=text('now()'),nullable=False)
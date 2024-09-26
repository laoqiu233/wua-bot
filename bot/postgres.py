from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from bot.models import Wua


class Base(DeclarativeBase):
    pass


class WuaEntity(Base):
    __tablename__ = "wuas"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    size: Mapped[int]
    wu_size: Mapped[int]
    a_size: Mapped[int]
    author: Mapped[str]
    chat: Mapped[str]


def get_async_session(url: str) -> async_sessionmaker[AsyncSession]:
    engine = create_async_engine(url)
    return async_sessionmaker(engine)


class WuaDao:
    def __init__(self, async_session: async_sessionmaker[AsyncSession]):
        self.async_session = async_session

    async def get_all_wuas_in_chat(self, chat: str, author: str | None = None) -> list[Wua]:
        stmt = select(WuaEntity).where(WuaEntity.chat == chat)

        if author is not None:
            stmt = stmt.where(WuaEntity.author == author)

        async with self.async_session() as session:
            result = await session.scalars(stmt)
            wuas = [Wua.model_validate(entity) for entity in result.all()]
            wuas.sort(key=lambda x: x.size, reverse=True)
            return wuas
    
    async def put_wua(self, wua: Wua):
        async with self.async_session() as session:
            entity = WuaEntity(
                id=wua.id,
                size=wua.size,
                wu_size=wua.wu_size,
                a_size=wua.a_size,
                author=wua.author,
                chat=wua.chat,
            )
            session.add(entity)
            await session.commit()

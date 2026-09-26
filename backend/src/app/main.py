from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db
from .routers.anti_procrastination import router as anti_procrastination_router
from .routers.but_rebuttal import router as but_rebuttal_router
from .routers.daily_plan import router as daily_plan_router
from .routers.journal import router as journal_router
from .routers.thought_counter import router as thought_counter_router
from .routers.tools import router as tools_router
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动时建表 + 幂等写入种子数据（单用户 jong / 11 条扭曲选项）。"""
    init_db()
    yield

app = FastAPI(lifespan=lifespan)

# CORS：开发期允许 Next.js dev server (localhost:3100) 的跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3100",
        "http://127.0.0.1:3100",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(journal_router)
app.include_router(tools_router)
app.include_router(thought_counter_router)
app.include_router(daily_plan_router)
app.include_router(anti_procrastination_router)
app.include_router(but_rebuttal_router)



from fastapi import FastAPI, Depends, HTTPException, status, Path, Body, Cookie, Form
from pydantic import BaseModel, Field
from typing import Annotated, List, Union

# 假設這是你原有的驗證模組
from .google_oauth import verify_google_id_token
from .auth_utils import create_access_token, get_current_user_email

app = FastAPI(title="資工系整合專案：認證與 Item 管理")

# --- 1. 定義資料模型 (Data Models) ---

class TokenRequest(BaseModel):
    id_token: str

class Item(BaseModel):
    name: str
    description: Union[str, None] = Field(
        default=None, title="The description of the item", max_length=300
    )
    price: float = Field(gt=0, description="The price must be greater than zero")
    tax: Union[float, None] = None
    tags: List[str] = []

# --- 2. 認證相關路由 (Authentication) ---

@app.post("/auth/google", summary="Google OAuth 登入")
async def google_auth(request: TokenRequest):
    user_info = verify_google_id_token(request.id_token)
    user_email = user_info.get("email")
    if not user_email:
        raise HTTPException(status_code=400, detail="Google 帳號未提供 Email")

    access_token = create_access_token(data={"sub": user_email})
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": user_info
    }

# 保留你原本的表單登入 (可作為備用)
@app.post("/login")
async def login(
    username: Annotated[str, Form()],
    password: Annotated[str, Form()] # 已修正 atr -> str
):
    return {"username": username}

# --- 3. 受保護的 Item 路由 (CRUD + JWT 驗證) ---

@app.get("/items/", response_model=Union[dict, List[Item]])
async def read_items(
    ads_id: Annotated[Union[str, None], Cookie()] = None,
    current_user: str = Depends(get_current_user_email) # 加上驗證
):
    """取得所有項目，必須登入才能存取"""
    return {"ads_id": ads_id, "user": current_user, "items": []}

@app.post("/items/", response_model=Item)
async def create_item(
    item: Item, 
    current_user: str = Depends(get_current_user_email) # 加上驗證
):
    """新增項目，必須登入才能存取"""
    return item

@app.put("/items/{item_id}")
async def update_item(
    item_id: Annotated[int, Path(title="The ID of the item to update", ge=0)],
    item: Annotated[Item, Body(embed=True)],
    current_user: str = Depends(get_current_user_email) # 加上驗證
):
    """更新項目，必須登入才能存取"""
    return {"item_id": item_id, "item": item, "updated_by": current_user}

# --- 4. 公開路由 ---

@app.get("/")
async def root():
    return {"message": "Hello World! FastAPI Backend is running."}
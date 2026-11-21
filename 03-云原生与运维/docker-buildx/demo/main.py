rom fastapi import FastAPI
from pydantic import BaseModel

# 创建 FastAPI 实例
app = FastAPI()


# 定义一个数据模型，用于 POST 请求参数
class Item(BaseModel):
    name: str
    price: float
    count: int = 1


# 基础 GET 接口
@app.get("/")
def read_root():
    return {"message": "Hello FastAPI"}


# GET 带参数
@app.get("/hello/{username}")
def say_hello(username: str):
    return {"hello": username}


# POST 接口
@app.post("/items/")
def create_item(item: Item):
    total = item.price * item.count
    return {
        "name": item.name,
        "unit_price": item.price,
        "count": item.count,
        "total_price": total
    }

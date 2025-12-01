from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import json
import os
import logging
import time
from multiprocessing import Queue
from os import getenv
from fastapi import Request
from prometheus_fastapi_instrumentator import Instrumentator

from pydantic.v1 import Field
from influxdb_client import InfluxDBClient, Point, WritePrecision

from logging_loki import LokiQueueHandler

influx_url = "http://influxdb:8086"
influx_token = "mytoken"
influx_org = "myorg"
influx_bucket = "mybucket"


app = FastAPI()

Instrumentator().instrument(app).expose(app, endpoint="/metrics")

client = InfluxDBClient(url=influx_url, token=influx_token, org=influx_org)
write_api = client.write_api()

def write_metric():
    point = Point("fastapi_metric").field("value", 1)
    write_api.write(bucket=influx_bucket, org=influx_org, record=point)

loki_logs_handler = LokiQueueHandler(
    Queue(-1),
    url=getenv("LOKI_ENDPOINT"),
    tags={"application": "fastapi"},
    version="1",
)

# Custom access logger (ignore Uvicorn's default logging)
custom_logger = logging.getLogger("custom.access")
custom_logger.setLevel(logging.INFO)

# Add Loki handler (assuming `loki_logs_handler` is correctly configured)
custom_logger.addHandler(loki_logs_handler)

async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time  # Compute response time

    log_message = (
        f'{request.client.host} - "{request.method} {request.url.path} HTTP/1.1" {response.status_code} {duration:.3f}s'
    )

    # **Only log if duration exists**
    if duration:
        custom_logger.info(log_message)

    return response

# To-Do 항목 모델
class TodoItem(BaseModel):
    id: int
    title: str
    description: str
    status: str
    completed: bool
    created_at: str
    updated_at: str

class Tag(BaseModel):
    id: int
    name: str

class TodoItemCreate(BaseModel):
    id: int
    title: str
    description: str
    status: str
    completed: bool
    created_at: str
    updated_at: str
    tag_ids: list[int] = Field(default_factory=list)

class TodoItemResponse(BaseModel):
    id: int
    title: str
    description: str
    status: str
    completed: bool
    created_at: str
    updated_at: str
    tags: list[Tag] = Field(default_factory=list)

# JSON 파일 경로
TODO_FILE = "todo.json"
TAG_FILE = "tag.json"
TODO_TAG_FILE = "todo_tag.json"

# JSON 파일에서 To-Do 항목 로드
def load_todos():
    if os.path.exists(TODO_FILE):
        with open(TODO_FILE, "r") as file:
            return json.load(file)
    return []

# JSON 파일에 To-Do 항목 저장
def save_todos(todos):
    with open(TODO_FILE, "w") as file:
        json.dump(todos, file, indent=4)

# To-Do 목록 조회
@app.get("/todos", response_model=list[TodoItemResponse])
def get_todos():
    todos = load_todos()
    tags = load_tags()
    result = []
    for todo in todos:
        tag_ids = todo.get("tag_ids", [])
        todo_tags = [tag for tag in tags if tag["id"] in tag_ids]
        result.append(TodoItemResponse(**todo, tags=todo_tags))
    result.sort(key=lambda x: x.created_at, reverse=True)
    return result

@app.get("/todos/tags/{tag_id}", response_model=list[TodoItemResponse])
def get_todos_by_tag(tag_id: int):
    todos = load_todos()
    tags = load_tags()
    result = []
    for todo in todos:
        tag_ids = todo.get("tag_ids", [])
        if tag_id in tag_ids:
            todo_tags = [tag for tag in tags if tag["id"] in tag_ids]
            result.append(TodoItemResponse(**todo, tags=todo_tags))
    result.sort(key=lambda x: x.created_at, reverse=True)
    return result

# 신규 To-Do 항목 추가
@app.post("/todos", response_model=TodoItemResponse)
def create_todo(todo: TodoItemCreate):
    todos = load_todos()
    todo_dict = todo.model_dump()
    todos.append(todo_dict)
    save_todos(todos)
    tags = load_tags()
    todo_tags = [tag for tag in tags if tag["id"] in todo.tag_ids]
    return TodoItemResponse(**todo_dict, tags=todo_tags)

# To-Do 항목 수정
@app.put("/todos/{todo_id}", response_model=TodoItem)
def update_todo(todo_id: int, updated_todo: TodoItem):
    todos = load_todos()
    for todo in todos:
        if todo["id"] == todo_id:
            todo.update(updated_todo.dict())
            save_todos(todos)
            return updated_todo
    raise HTTPException(status_code=404, detail="To-Do item not found")

# To-Do 항목 삭제
@app.delete("/todos/{todo_id}", response_model=dict)
def delete_todo(todo_id: int):
    todos = load_todos()
    todos = [todo for todo in todos if todo["id"] != todo_id]
    save_todos(todos)
    return {"message": "To-Do item deleted"}

# HTML 파일 서빙
@app.get("/", response_class=HTMLResponse)
def read_root():
    with open("templates/index.html", "r") as file:
        content = file.read()
    return HTMLResponse(content=content)


def load_tags():
    if os.path.exists(TAG_FILE):
        with open(TAG_FILE, "r") as file:
            return json.load(file)
    return []

# JSON 파일에 To-Do 항목 저장
def save_tags(tags):
    with open(TAG_FILE, "w") as file:
        json.dump(tags, file, indent=4)

# To-Do 목록 조회
@app.get("/tags", response_model=list[Tag])
def get_tags():
    tags = load_tags()
    tags.sort(key=lambda x: x["id"], reverse=True)
    return tags

# 신규 To-Do 항목 추가
@app.post("/tags", response_model=Tag)
def create_tag(tag: Tag):
    tags = load_tags()
    tags.append(tag.model_dump())
    save_tags(tags)
    return tag

# To-Do 항목 수정
@app.put("/tags/{tag_id}", response_model=Tag)
def update_tag(tag_id: int, updated_tag: Tag):
    tags = load_tags()
    for tag in tags:
        if tag["id"] == tag_id:
            tag.update(updated_tag.dict())
            save_tags(tag)
            return tag
    raise HTTPException(status_code=404, detail="Tag not found")

# To-Do 항목 삭제
@app.delete("/tags/{tag_id}", response_model=dict)
def delete_tag(tag_id: int):
    tags = load_tags()
    tag = [tag for tag in tags if tag["id"] != tag_id]
    save_tags(tag)
    return {"message": "Tag deleted"}

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List, Optional
import jwt
from datetime import datetime, timedelta
import heapq
app = FastAPI()
SECRET_KEY = "1@Uditnayak"  
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
task_queue = []  
class User(BaseModel):
    username: str
    password: str
class Token(BaseModel):
    access_token: str
    token_type: str
class TokenData(BaseModel):
    username: str
class TaskBase(BaseModel):
    title: str
    description: str
    status: str
    priority: str
class TaskCreate(TaskBase):
    pass
class Task(TaskBase):
    id: int
    created_at: datetime
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
users = {"testuser": {"password": "1@TESTPASS"}}
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
def authenticate_user(username, password):
    if username in users and users[username]["password"] == password:
        return {"username": username}
    return None
def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("username")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        token_data = TokenData(username=username)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return token_data
tasks = {}
task_id_counter = 1
def get_priority_value(priority: str) -> int:
    if priority == "high":
        return 3
    elif priority == "medium":
        return 2
    elif priority == "low":
        return 1
    else:
        return 0
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"username": user["username"]}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}
@app.post("/tasks/", response_model=Task)
async def create_task(task: TaskCreate, current_user: TokenData = Depends(get_current_user)):
    global task_id_counter
    new_task = Task(id=task_id_counter, created_at=datetime.utcnow(), **task.dict())
    tasks[new_task.id] = new_task
    task_id_counter += 1

    priority_value = get_priority_value(new_task.priority)
    heapq.heappush(task_queue, (priority_value, new_task.created_at, new_task.id))
    return new_task
@app.get("/tasks/", response_model=List[Task])
async def get_tasks(
    current_user: TokenData = Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
    priority: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
):
    start = (page - 1) * limit
    end = start + limit

    filtered_tasks = list(tasks.values())
    if priority:
        filtered_tasks = [task for task in filtered_tasks if task.priority == priority]
    if status:
        filtered_tasks = [task for task in filtered_tasks if task.status == status]
    paginated_tasks = filtered_tasks[start:end]
    return paginated_tasks
@app.get("/tasks/{task_id}", response_model=Task)
async def get_task(task_id: int, current_user: TokenData = Depends(get_current_user)):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks[task_id]
@app.put("/tasks/{task_id}", response_model=Task)
async def update_task(task_id: int, updated_task: TaskCreate, current_user: TokenData = Depends(get_current_user)):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    tasks[task_id] = Task(id=task_id, created_at=tasks[task_id].created_at, **updated_task.dict())
    return tasks[task_id]
@app.delete("/tasks/{task_id}", response_model=dict)
async def delete_task(task_id: int, current_user: TokenData = Depends(get_current_user)):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    del tasks[task_id]
    return {"message": "Task deleted"}
@app.get("/scheduled_tasks/", response_model=List[Task])
async def get_scheduled_tasks(current_user: TokenData = Depends(get_current_user)):
    scheduled_task_ids = [task[2] for task in sorted(task_queue)]
    scheduled_tasks = [tasks[task_id] for task_id in scheduled_task_ids if task_id in tasks]
    return scheduled_tasks

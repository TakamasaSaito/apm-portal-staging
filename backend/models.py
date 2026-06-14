from pydantic import BaseModel
from typing import Optional

class EnvironmentCreate(BaseModel):
    application_id: str
    env_type: str
    location: Optional[str] = None
    ip: Optional[str] = None
    host: Optional[str] = None
    os: Optional[str] = None
    middleware: Optional[str] = None
    cpu_mem: Optional[str] = None
    storage: Optional[str] = None

class EnvironmentUpdate(BaseModel):
    env_type: Optional[str] = None
    location: Optional[str] = None
    ip: Optional[str] = None
    host: Optional[str] = None
    os: Optional[str] = None
    middleware: Optional[str] = None
    cpu_mem: Optional[str] = None
    storage: Optional[str] = None

class RequestCreate(BaseModel):
    type: str
    application_id: Optional[str] = None
    applicant_user_id: int
    reason: str
    # register
    app_name: Optional[str] = None
    dept: Optional[str] = None
    biz_owner: Optional[str] = None
    new_status: Optional[str] = None
    start_plan: Optional[str] = None
    # update
    upd_status: Optional[str] = None
    upd_biz_owner: Optional[str] = None
    upd_end_plan: Optional[str] = None
    upd_start_actual: Optional[str] = None
    # retire
    end_plan: Optional[str] = None
    app_category: Optional[str] = None

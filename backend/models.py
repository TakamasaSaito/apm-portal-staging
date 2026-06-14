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
    application_id: Optional[str] = None
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


class ApplicationUpdate(BaseModel):
    application_name: Optional[str] = None
    department_name: Optional[str] = None
    status: Optional[str] = None
    vendor: Optional[str] = None
    business_owner: Optional[str] = None
    system_owner: Optional[str] = None
    ops_manager: Optional[str] = None
    dev_manager: Optional[str] = None
    start_plan: Optional[str] = None
    start_actual: Optional[str] = None
    end_plan: Optional[str] = None
    end_actual: Optional[str] = None
    app_category: Optional[str] = None


class ConfigurationItemCreate(BaseModel):
    ci_name: str
    ci_type: Optional[str] = None
    environment_id: int
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    bmc_ip: Optional[str] = None
    os: Optional[str] = None
    os_version: Optional[str] = None
    cpu: Optional[str] = None
    memory: Optional[str] = None
    storage: Optional[str] = None
    vendor: Optional[str] = None
    model: Optional[str] = None
    status: Optional[str] = "active"
    note: Optional[str] = None


class ConfigurationItemUpdate(BaseModel):
    ci_name: Optional[str] = None
    ci_type: Optional[str] = None
    environment_id: Optional[int] = None
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    bmc_ip: Optional[str] = None
    os: Optional[str] = None
    os_version: Optional[str] = None
    cpu: Optional[str] = None
    memory: Optional[str] = None
    storage: Optional[str] = None
    vendor: Optional[str] = None
    model: Optional[str] = None
    status: Optional[str] = None
    note: Optional[str] = None

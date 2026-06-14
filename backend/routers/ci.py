from fastapi import APIRouter, Depends, HTTPException
import aiosqlite
from ..database import get_db
from ..models import ConfigurationItemCreate, ConfigurationItemUpdate
from .auth import get_current_user

router = APIRouter(prefix="/api/ci", tags=["ci"])


@router.get("")
async def list_ci(
    environment_id: int = 0,
    db: aiosqlite.Connection = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    query = """
        SELECT c.*, e.env_type, e.application_id,
               a.application_name
        FROM configuration_item c
        LEFT JOIN environment e ON c.environment_id = e.environment_id
        LEFT JOIN application a ON e.application_id = a.application_id
        WHERE 1=1
    """
    params = []
    if environment_id:
        query += " AND c.environment_id = ?"
        params.append(environment_id)
    query += " ORDER BY c.ci_id"
    async with db.execute(query, params) as cur:
        return [dict(row) for row in await cur.fetchall()]


@router.get("/{ci_id}")
async def get_ci(
    ci_id: int,
    db: aiosqlite.Connection = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    async with db.execute(
        """
        SELECT c.*, e.env_type, e.application_id,
               a.application_name
        FROM configuration_item c
        LEFT JOIN environment e ON c.environment_id = e.environment_id
        LEFT JOIN application a ON e.application_id = a.application_id
        WHERE c.ci_id = ?
        """,
        [ci_id],
    ) as cur:
        row = await cur.fetchone()
    if row is None:
        raise HTTPException(404, "CI not found")
    return dict(row)


@router.post("", status_code=201)
async def create_ci(
    data: ConfigurationItemCreate,
    db: aiosqlite.Connection = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    async with db.execute(
        """
        INSERT INTO configuration_item
            (ci_name, ci_type, environment_id, hostname, ip_address, bmc_ip,
             os, os_version, cpu, memory, storage, vendor, model, status, note)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [data.ci_name, data.ci_type, data.environment_id, data.hostname,
         data.ip_address, data.bmc_ip, data.os, data.os_version,
         data.cpu, data.memory, data.storage, data.vendor, data.model,
         data.status or "active", data.note],
    ) as cur:
        ci_id = cur.lastrowid
    await db.commit()
    return {"ci_id": ci_id}


@router.put("/{ci_id}")
async def update_ci(
    ci_id: int,
    data: ConfigurationItemUpdate,
    db: aiosqlite.Connection = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(400, "No fields to update")
    sets = ", ".join(f"{k} = ?" for k in updates)
    await db.execute(
        f"UPDATE configuration_item SET {sets} WHERE ci_id = ?",
        [*updates.values(), ci_id],
    )
    await db.commit()
    return {"status": "updated"}


@router.delete("/{ci_id}", status_code=204)
async def delete_ci(
    ci_id: int,
    db: aiosqlite.Connection = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    async with db.execute(
        "SELECT ci_id FROM configuration_item WHERE ci_id = ?", [ci_id]
    ) as cur:
        if not await cur.fetchone():
            raise HTTPException(404, "CI not found")
    await db.execute("DELETE FROM configuration_item WHERE ci_id = ?", [ci_id])
    await db.commit()

from fastapi import APIRouter, Depends, HTTPException
import aiosqlite
from ..database import get_db
from ..models import EnvironmentCreate, EnvironmentUpdate

router = APIRouter(prefix="/api")

_JOIN = """
    SELECT e.*, a.application_name
    FROM environment e
    LEFT JOIN application a ON e.application_id = a.application_id
"""


@router.get("/environments")
async def list_environments(q: str = "", db: aiosqlite.Connection = Depends(get_db)):
    query = _JOIN + " WHERE 1=1"
    params = []
    if q:
        query += (
            " AND (e.application_id LIKE ? OR a.application_name LIKE ?"
            " OR e.ip LIKE ? OR e.env_type LIKE ?)"
        )
        params += [f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%"]
    query += " ORDER BY e.application_id, e.environment_id"
    async with db.execute(query, params) as cur:
        return [dict(row) for row in await cur.fetchall()]


@router.post("/environments", status_code=201)
async def create_environment(
    data: EnvironmentCreate, db: aiosqlite.Connection = Depends(get_db)
):
    async with db.execute(
        """
        INSERT INTO environment
            (application_id, env_type, location, ip, host, os, middleware, cpu_mem, storage)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            data.application_id, data.env_type, data.location, data.ip,
            data.host, data.os, data.middleware, data.cpu_mem, data.storage,
        ],
    ) as cur:
        env_id = cur.lastrowid
    await db.commit()
    async with db.execute(_JOIN + " WHERE e.environment_id = ?", [env_id]) as cur:
        return dict(await cur.fetchone())


@router.put("/environments/{env_id}")
async def update_environment(
    env_id: int, data: EnvironmentUpdate, db: aiosqlite.Connection = Depends(get_db)
):
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(400, "No fields to update")
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    await db.execute(
        f"UPDATE environment SET {set_clause} WHERE environment_id = ?",
        [*updates.values(), env_id],
    )
    await db.commit()
    async with db.execute(_JOIN + " WHERE e.environment_id = ?", [env_id]) as cur:
        return dict(await cur.fetchone())


@router.delete("/environments/{env_id}", status_code=204)
async def delete_environment(env_id: int, db: aiosqlite.Connection = Depends(get_db)):
    await db.execute("DELETE FROM environment WHERE environment_id = ?", [env_id])
    await db.commit()

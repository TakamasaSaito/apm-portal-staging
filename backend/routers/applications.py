from fastapi import APIRouter, Depends, HTTPException
import aiosqlite
from ..database import get_db
from ..models import ApplicationUpdate
from .auth import get_current_user

router = APIRouter(prefix="/api")


@router.get("/applications")
async def list_applications(
    q: str = "",
    status: str = "",
    dept: str = "",
    db: aiosqlite.Connection = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    query = """
        SELECT a.*, d.department_name
        FROM application a
        LEFT JOIN department d ON a.owner_department_id = d.department_id
        WHERE 1=1
    """
    params = []
    if status:
        query += " AND a.status = ?"
        params.append(status)
    if dept:
        query += " AND d.department_name = ?"
        params.append(dept)
    if q:
        query += " AND (a.application_name LIKE ? OR a.application_id LIKE ? OR d.department_name LIKE ?)"
        params += [f"%{q}%", f"%{q}%", f"%{q}%"]
    query += " ORDER BY a.application_id"

    async with db.execute(query, params) as cur:
        apps = [dict(row) for row in await cur.fetchall()]

    for app in apps:
        async with db.execute(
            "SELECT env_type FROM environment WHERE application_id = ?",
            [app["application_id"]],
        ) as cur:
            app["env_types"] = [row["env_type"] for row in await cur.fetchall()]

    return apps


@router.get("/applications/{app_id}")
async def get_application(
    app_id: str,
    db: aiosqlite.Connection = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    async with db.execute(
        """
        SELECT a.*, d.department_name
        FROM application a
        LEFT JOIN department d ON a.owner_department_id = d.department_id
        WHERE a.application_id = ?
        """,
        [app_id],
    ) as cur:
        row = await cur.fetchone()
    if row is None:
        from fastapi import HTTPException
        raise HTTPException(404, "Application not found")
    app = dict(row)

    async with db.execute(
        "SELECT * FROM environment WHERE application_id = ? ORDER BY environment_id",
        [app_id],
    ) as cur:
        app["environments"] = [dict(r) for r in await cur.fetchall()]

    return app


@router.put("/applications/{app_id}")
async def update_application(
    app_id: str,
    data: ApplicationUpdate,
    db: aiosqlite.Connection = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    async with db.execute(
        "SELECT application_id FROM application WHERE application_id = ?", [app_id]
    ) as cur:
        if not await cur.fetchone():
            raise HTTPException(404, "Application not found")

    updates: dict = {}
    if data.application_name is not None:
        updates["application_name"] = data.application_name
    if data.status is not None:
        updates["status"] = data.status
    if data.vendor is not None:
        updates["vendor"] = data.vendor
    if data.business_owner is not None:
        updates["business_owner"] = data.business_owner
    if data.system_owner is not None:
        updates["system_owner"] = data.system_owner
    if data.ops_manager is not None:
        updates["ops_manager"] = data.ops_manager
    if data.dev_manager is not None:
        updates["dev_manager"] = data.dev_manager
    if data.start_plan is not None:
        updates["start_plan"] = data.start_plan or None
    if data.start_actual is not None:
        updates["start_actual"] = data.start_actual or None
    if data.end_plan is not None:
        updates["end_plan"] = data.end_plan or None
    if data.end_actual is not None:
        updates["end_actual"] = data.end_actual or None
    if data.app_category is not None:
        updates["app_category"] = data.app_category or None

    if data.department_name is not None:
        async with db.execute(
            "SELECT department_id FROM department WHERE department_name = ?",
            [data.department_name],
        ) as cur:
            row = await cur.fetchone()
        if row:
            updates["owner_department_id"] = row["department_id"]

    if updates:
        sets = ", ".join(f"{k} = ?" for k in updates)
        await db.execute(
            f"UPDATE application SET {sets} WHERE application_id = ?",
            [*updates.values(), app_id],
        )
        await db.commit()
    return {"status": "updated"}


@router.get("/stats")
async def get_stats(
    db: aiosqlite.Connection = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    async with db.execute(
        "SELECT COUNT(*) AS c FROM application WHERE status = 'running'"
    ) as cur:
        running = (await cur.fetchone())["c"]
    async with db.execute(
        "SELECT COUNT(*) AS c FROM application WHERE status IN ('dev','plan','order')"
    ) as cur:
        dev = (await cur.fetchone())["c"]
    async with db.execute(
        "SELECT COUNT(*) AS c FROM apm_request WHERE status = 'pending'"
    ) as cur:
        pending = (await cur.fetchone())["c"]
    async with db.execute("SELECT COUNT(*) AS c FROM environment") as cur:
        env_count = (await cur.fetchone())["c"]
    return {"running": running, "dev": dev, "pending": pending, "env_count": env_count}


@router.get("/departments")
async def list_departments(
    db: aiosqlite.Connection = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    async with db.execute(
        "SELECT * FROM department ORDER BY department_id"
    ) as cur:
        return [dict(row) for row in await cur.fetchall()]

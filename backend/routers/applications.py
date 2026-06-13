from fastapi import APIRouter, Depends
import aiosqlite
from ..database import get_db

router = APIRouter(prefix="/api")


@router.get("/applications")
async def list_applications(
    q: str = "",
    status: str = "",
    dept: str = "",
    db: aiosqlite.Connection = Depends(get_db),
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
async def get_application(app_id: str, db: aiosqlite.Connection = Depends(get_db)):
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


@router.get("/stats")
async def get_stats(db: aiosqlite.Connection = Depends(get_db)):
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
async def list_departments(db: aiosqlite.Connection = Depends(get_db)):
    async with db.execute(
        "SELECT * FROM department ORDER BY department_id"
    ) as cur:
        return [dict(row) for row in await cur.fetchall()]

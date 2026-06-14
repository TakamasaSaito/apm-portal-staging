from fastapi import APIRouter, Depends
import aiosqlite
from datetime import date, timedelta
from ..database import get_db
from .auth import get_current_user

router = APIRouter(prefix="/api/dashboard")


@router.get("/summary")
async def get_summary(
    db: aiosqlite.Connection = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    today = date.today().isoformat()
    in_12m = (date.today() + timedelta(days=365)).isoformat()

    async with db.execute(
        "SELECT status, COUNT(*) as cnt FROM application GROUP BY status"
    ) as cur:
        status_counts = {row["status"]: row["cnt"] for row in await cur.fetchall()}

    async with db.execute(
        """SELECT COALESCE(app_category, '未設定') as category, COUNT(*) as cnt
           FROM application GROUP BY app_category ORDER BY cnt DESC"""
    ) as cur:
        category_counts = [
            {"category": row["category"], "count": row["cnt"]}
            for row in await cur.fetchall()
        ]

    async with db.execute(
        """SELECT d.department_name, COUNT(*) as cnt
           FROM application a
           JOIN department d ON a.owner_department_id = d.department_id
           GROUP BY d.department_name ORDER BY cnt DESC"""
    ) as cur:
        dept_counts = [
            {"dept": row["department_name"], "count": row["cnt"]}
            for row in await cur.fetchall()
        ]

    async with db.execute(
        """SELECT a.application_id, a.application_name, a.status, a.end_plan,
                  a.business_owner, d.department_name
           FROM application a
           LEFT JOIN department d ON a.owner_department_id = d.department_id
           WHERE a.end_plan BETWEEN ? AND ? AND a.status != 'retire'
           ORDER BY a.end_plan""",
        [today, in_12m],
    ) as cur:
        retiring_soon = [dict(row) for row in await cur.fetchall()]

    async with db.execute(
        "SELECT COUNT(*) as cnt FROM apm_request WHERE status = 'pending'"
    ) as cur:
        pending = (await cur.fetchone())["cnt"]

    async with db.execute("SELECT COUNT(*) as cnt FROM environment") as cur:
        env_count = (await cur.fetchone())["cnt"]

    async with db.execute("SELECT COUNT(*) as cnt FROM configuration_item") as cur:
        ci_count = (await cur.fetchone())["cnt"]

    return {
        "status_counts": status_counts,
        "category_counts": category_counts,
        "dept_counts": dept_counts,
        "retiring_soon": retiring_soon,
        "pending_requests": pending,
        "env_count": env_count,
        "ci_count": ci_count,
    }


@router.get("/bubble")
async def get_bubble(
    db: aiosqlite.Connection = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    async with db.execute(
        """SELECT a.application_id, a.application_name, a.status,
                  a.portfolio_area, a.annual_cost_million, a.is_infrastructure,
                  a.migration_target_id, a.app_category, a.vendor,
                  d.department_name
           FROM application a
           LEFT JOIN department d ON a.owner_department_id = d.department_id
           WHERE a.portfolio_area IS NOT NULL
           ORDER BY a.portfolio_area, a.annual_cost_million DESC"""
    ) as cur:
        apps = [dict(row) for row in await cur.fetchall()]

    async with db.execute(
        """SELECT dependency_id, app_id, depends_on_app_id, dependency_type, note
           FROM application_dependency"""
    ) as cur:
        deps = [dict(row) for row in await cur.fetchall()]

    return {"apps": apps, "dependencies": deps}

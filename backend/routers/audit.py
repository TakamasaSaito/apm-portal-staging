import json
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
import aiosqlite
from ..database import get_db
from .audit_utils import write_audit_log  # noqa: F401 – re-export for other routers
from .auth import get_current_user

router = APIRouter(prefix="/api", tags=["audit"])


@router.get("/audit-logs")
async def list_audit_logs(
    limit: int = 50,
    offset: int = 0,
    action: str = "",
    target_table: str = "",
    db: aiosqlite.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user.get("role") != "admin":
        raise HTTPException(403, "Admin only")

    count_q = "SELECT COUNT(*) AS c FROM audit_log WHERE 1=1"
    query = """
        SELECT al.audit_log_id, u.user_name, al.action, al.target_table,
               al.target_id, al.before_value, al.after_value, al.ip_address, al.created_at
        FROM audit_log al
        LEFT JOIN user u ON al.user_id = u.user_id
        WHERE 1=1
    """
    params = []

    if action:
        query += " AND al.action = ?"
        count_q += " AND action = ?"
        params.append(action)
    if target_table:
        query += " AND al.target_table = ?"
        count_q += " AND target_table = ?"
        params.append(target_table)

    query += " ORDER BY al.created_at DESC LIMIT ? OFFSET ?"

    async with db.execute(count_q, params) as cur:
        total = (await cur.fetchone())["c"]

    async with db.execute(query, params + [limit, offset]) as cur:
        rows = [dict(r) for r in await cur.fetchall()]

    for row in rows:
        for field in ("before_value", "after_value"):
            if row[field] and isinstance(row[field], str):
                try:
                    row[field] = json.loads(row[field])
                except Exception:
                    pass

    return {"total": total, "items": rows}

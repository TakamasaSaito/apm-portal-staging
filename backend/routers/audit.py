import json
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
import aiosqlite
from ..database import get_db
from .auth import get_current_user

router = APIRouter(prefix="/api", tags=["audit"])


async def write_audit_log(
    db: aiosqlite.Connection,
    user_id: Optional[int],
    action: str,
    target_table: str = None,
    target_id: str = None,
    before_value: dict = None,
    after_value: dict = None,
    ip_address: str = None,
):
    await db.execute(
        """INSERT INTO audit_log
           (user_id, action, target_table, target_id, before_value, after_value, ip_address, created_at)
           VALUES (?,?,?,?,?,?,?,?)""",
        [
            user_id, action, target_table, target_id,
            json.dumps(before_value, ensure_ascii=False) if before_value else None,
            json.dumps(after_value, ensure_ascii=False) if after_value else None,
            ip_address,
            datetime.now().isoformat()
        ]
    )
    await db.commit()


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

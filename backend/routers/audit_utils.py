import json
from datetime import datetime
from typing import Optional
import aiosqlite


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

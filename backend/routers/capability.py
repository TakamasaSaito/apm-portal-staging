from fastapi import APIRouter, Depends, HTTPException
import aiosqlite
from ..database import get_db
from ..models import CapabilityCreate, CapabilityUpdate
from .auth import get_current_user

router = APIRouter(prefix="/api/capabilities", tags=["capabilities"])


async def _get_realizes_id(db: aiosqlite.Connection) -> int:
    async with db.execute(
        "SELECT relation_type_id FROM relation_type WHERE type_name = 'realizes'"
    ) as cur:
        row = await cur.fetchone()
    if not row:
        raise HTTPException(500, "relation_type 'realizes' not found")
    return row[0]


@router.get("/matrix")
async def get_capability_matrix(
    db: aiosqlite.Connection = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    async with db.execute(
        "SELECT * FROM business_capability ORDER BY level, sort_order, capability_id"
    ) as cur:
        caps = [dict(r) for r in await cur.fetchall()]

    realizes_id = await _get_realizes_id(db)

    async with db.execute(
        """SELECT r.parent_id AS capability_id,
                  COUNT(*) AS app_count,
                  GROUP_CONCAT(a.application_name, '||') AS app_names
           FROM cmdb_rel_ci r
           JOIN application a ON a.application_id = r.child_id
           WHERE r.parent_table = 'business_capability'
             AND r.child_table  = 'application'
             AND r.relation_type_id = ?
           GROUP BY r.parent_id""",
        [realizes_id],
    ) as cur:
        link_rows = {r["capability_id"]: dict(r) for r in await cur.fetchall()}

    result = []
    for cap in caps:
        cid = cap["capability_id"]
        link = link_rows.get(cid, {})
        app_names_raw = link.get("app_names") or ""
        app_names = [n for n in app_names_raw.split("||") if n] if app_names_raw else []
        result.append({
            **cap,
            "app_count": link.get("app_count", 0),
            "app_names": app_names,
        })
    return result


@router.get("")
async def list_capabilities(
    db: aiosqlite.Connection = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    async with db.execute(
        "SELECT * FROM business_capability ORDER BY level, sort_order, capability_id"
    ) as cur:
        rows = [dict(r) for r in await cur.fetchall()]

    by_id = {r["capability_id"]: {**r, "children": []} for r in rows}
    tree = []
    for r in rows:
        if r["parent_id"] and r["parent_id"] in by_id:
            by_id[r["parent_id"]]["children"].append(by_id[r["capability_id"]])
        else:
            tree.append(by_id[r["capability_id"]])
    return tree


@router.post("", status_code=201)
async def create_capability(
    payload: CapabilityCreate,
    db: aiosqlite.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user.get("role") != "admin":
        raise HTTPException(403, "Admin only")

    await db.execute(
        """INSERT INTO business_capability
               (capability_id, capability_name, parent_id, level, scope, sort_order)
           VALUES (?, ?, ?, ?, ?, ?)""",
        [payload.capability_id, payload.capability_name, payload.parent_id,
         payload.level, payload.scope, payload.sort_order],
    )
    await db.commit()

    async with db.execute(
        "SELECT * FROM business_capability WHERE capability_id = ?", [payload.capability_id]
    ) as cur:
        return dict(await cur.fetchone())


@router.put("/{capability_id}")
async def update_capability(
    capability_id: str,
    payload: CapabilityUpdate,
    db: aiosqlite.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user.get("role") != "admin":
        raise HTTPException(403, "Admin only")

    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(400, "No fields to update")

    sets = ", ".join(f"{k} = ?" for k in updates)
    await db.execute(
        f"UPDATE business_capability SET {sets} WHERE capability_id = ?",
        [*updates.values(), capability_id],
    )
    await db.commit()

    async with db.execute(
        "SELECT * FROM business_capability WHERE capability_id = ?", [capability_id]
    ) as cur:
        row = await cur.fetchone()
    if not row:
        raise HTTPException(404, "Capability not found")
    return dict(row)


@router.delete("/{capability_id}", status_code=204)
async def delete_capability(
    capability_id: str,
    db: aiosqlite.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user.get("role") != "admin":
        raise HTTPException(403, "Admin only")

    realizes_id = await _get_realizes_id(db)
    await db.execute(
        """DELETE FROM cmdb_rel_ci
           WHERE parent_table = 'business_capability'
             AND parent_id = ?
             AND relation_type_id = ?""",
        [capability_id, realizes_id],
    )
    await db.execute(
        "DELETE FROM business_capability WHERE capability_id = ?", [capability_id]
    )
    await db.commit()


@router.get("/{capability_id}/applications")
async def list_capability_applications(
    capability_id: str,
    db: aiosqlite.Connection = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    realizes_id = await _get_realizes_id(db)
    async with db.execute(
        """SELECT a.*, r.rel_id, r.note AS link_note
           FROM cmdb_rel_ci r
           JOIN application a ON a.application_id = r.child_id
           WHERE r.parent_table = 'business_capability'
             AND r.parent_id    = ?
             AND r.child_table  = 'application'
             AND r.relation_type_id = ?
           ORDER BY a.application_name""",
        [capability_id, realizes_id],
    ) as cur:
        return [dict(r) for r in await cur.fetchall()]


@router.post("/{capability_id}/applications", status_code=201)
async def link_application(
    capability_id: str,
    payload: dict,
    db: aiosqlite.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user.get("role") != "admin":
        raise HTTPException(403, "Admin only")

    app_id = payload.get("application_id")
    if not app_id:
        raise HTTPException(400, "application_id is required")

    async with db.execute(
        "SELECT 1 FROM application WHERE application_id = ?", [app_id]
    ) as cur:
        if not await cur.fetchone():
            raise HTTPException(404, "Application not found")

    async with db.execute(
        "SELECT 1 FROM business_capability WHERE capability_id = ?", [capability_id]
    ) as cur:
        if not await cur.fetchone():
            raise HTTPException(404, "Capability not found")

    realizes_id = await _get_realizes_id(db)

    async with db.execute(
        """SELECT rel_id FROM cmdb_rel_ci
           WHERE parent_table = 'business_capability'
             AND parent_id    = ?
             AND child_table  = 'application'
             AND child_id     = ?
             AND relation_type_id = ?""",
        [capability_id, app_id, realizes_id],
    ) as cur:
        if await cur.fetchone():
            raise HTTPException(409, "Already linked")

    async with db.execute(
        """INSERT INTO cmdb_rel_ci
               (parent_table, parent_id, child_table, child_id, relation_type_id)
           VALUES ('business_capability', ?, 'application', ?, ?)""",
        [capability_id, app_id, realizes_id],
    ) as cur:
        rel_id = cur.lastrowid
    await db.commit()

    return {"rel_id": rel_id, "capability_id": capability_id, "application_id": app_id}


@router.delete("/{capability_id}/applications/{app_id}", status_code=204)
async def unlink_application(
    capability_id: str,
    app_id: str,
    db: aiosqlite.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user.get("role") != "admin":
        raise HTTPException(403, "Admin only")

    realizes_id = await _get_realizes_id(db)
    await db.execute(
        """DELETE FROM cmdb_rel_ci
           WHERE parent_table = 'business_capability'
             AND parent_id    = ?
             AND child_table  = 'application'
             AND child_id     = ?
             AND relation_type_id = ?""",
        [capability_id, app_id, realizes_id],
    )
    await db.commit()

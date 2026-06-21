"""
Demand Workbench 表示用: 全20件デマンドに score と priority を設定する。

バブルチャート座標:
  X軸 (Risk)  = score / 10
  Y軸 (Value) = priority mapping: 1→8, 2→6, 3→4, 4→2

4象限に均等分散（各5件）:
  Resource    (上左: Low Risk, High Value)  x<5, y>5  → priority 1-2, score<50
  Consider    (上右: High Risk, High Value) x>5, y>5  → priority 1-2, score>50
  Consider    (下左: Low Risk, Low Value)   x<5, y<5  → priority 3-4, score<50
  Re-evaluate (下右: High Risk, Low Value)  x>5, y<5  → priority 3-4, score>50

priority 分布: 1-最重要 × 5, 2-高 × 5, 3-中 × 5, 4-低 × 5
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "apm.db")

# (demand_id, score, priority)
UPDATES = [
    # ─── Q1: Resource（上左: Low Risk, High Value） ───────────────────
    # x = score/10 < 5,  y = value > 5  →  priority=1 or 2, score < 50
    ("DMND1001003", 30, "1 - 最重要"),   # x=3.0, y=8
    ("DMND1001005", 40, "2 - 高"),        # x=4.0, y=6
    ("DMND1001009", 35, "2 - 高"),        # x=3.5, y=6
    ("DMND1001012", 20, "1 - 最重要"),   # x=2.0, y=8
    ("DMND1001017", 45, "2 - 高"),        # x=4.5, y=6

    # ─── Q2: Consider（上右: High Risk, High Value） ─────────────────
    # x = score/10 > 5,  y = value > 5  →  priority=1 or 2, score > 50
    ("DMND1001001", 75, "2 - 高"),        # x=7.5, y=6
    ("DMND1001002", 60, "2 - 高"),        # x=6.0, y=6
    ("DMND1001004", 85, "1 - 最重要"),   # x=8.5, y=8
    ("DMND1001007", 70, "1 - 最重要"),   # x=7.0, y=8
    ("DMND1001013", 90, "1 - 最重要"),   # x=9.0, y=8

    # ─── Q3: Consider（下左: Low Risk, Low Value） ────────────────────
    # x = score/10 < 5,  y = value < 5  →  priority=3 or 4, score < 50
    ("DMND1001008", 25, "3 - 中"),        # x=2.5, y=4
    ("DMND1001010", 40, "3 - 中"),        # x=4.0, y=4
    ("DMND1001015", 15, "4 - 低"),        # x=1.5, y=2
    ("DMND1001016", 20, "4 - 低"),        # x=2.0, y=2
    ("DMND1001020", 35, "4 - 低"),        # x=3.5, y=2

    # ─── Q4: Re-evaluate（下右: High Risk, Low Value） ───────────────
    # x = score/10 > 5,  y = value < 5  →  priority=3 or 4, score > 50
    ("DMND1001006", 65, "3 - 中"),        # x=6.5, y=4
    ("DMND1001011", 80, "3 - 中"),        # x=8.0, y=4
    ("DMND1001014", 55, "4 - 低"),        # x=5.5, y=2
    ("DMND1001018", 70, "4 - 低"),        # x=7.0, y=2
    ("DMND1001019", 85, "3 - 中"),        # x=8.5, y=4
]

PRIORITY_VALUE_MAP = {"1 - 最重要": 8, "2 - 高": 6, "3 - 中": 4, "4 - 低": 2}


def main():
    if not os.path.exists(DB_PATH):
        print(f"[ERROR] DB not found: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    updated = 0
    for demand_id, score, priority in UPDATES:
        cur.execute(
            "UPDATE demand SET score=?, priority=?, updated_at=CURRENT_TIMESTAMP WHERE demand_id=?",
            [score, priority, demand_id],
        )
        if cur.rowcount:
            x = score / 10
            y = PRIORITY_VALUE_MAP.get(priority, "-")
            quadrant = (
                "Resource    (上左)" if x < 5 and y > 5 else
                "Consider    (上右)" if x > 5 and y > 5 else
                "Consider    (下左)" if x < 5 and y < 5 else
                "Re-evaluate (下右)"
            )
            print(f"  {demand_id}: score={score:3d}  x={x:.1f}  priority={priority}  y={y}  → {quadrant}")
            updated += 1
        else:
            print(f"  [SKIP] {demand_id}: not found in DB")

    conn.commit()
    conn.close()

    print(f"\n✅  {updated} / {len(UPDATES)} 件を更新しました")

    # 象限ごとの件数サマリー
    q = {"Resource (上左)": 0, "Consider (上右)": 0, "Consider (下左)": 0, "Re-evaluate (下右)": 0}
    for _, score, priority in UPDATES:
        x = score / 10
        y = PRIORITY_VALUE_MAP.get(priority, 0)
        if   x < 5 and y > 5: q["Resource (上左)"] += 1
        elif x > 5 and y > 5: q["Consider (上右)"] += 1
        elif x < 5 and y < 5: q["Consider (下左)"] += 1
        else:                  q["Re-evaluate (下右)"] += 1
    print("\n象限別件数:")
    for label, count in q.items():
        print(f"  {label}: {count} 件")

    p = {}
    for _, _, priority in UPDATES:
        p[priority] = p.get(priority, 0) + 1
    print("\nPriority分布:")
    for label in ["1 - 最重要", "2 - 高", "3 - 中", "4 - 低"]:
        print(f"  {label}: {p.get(label, 0)} 件")


if __name__ == "__main__":
    main()

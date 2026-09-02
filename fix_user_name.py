"""
سكربت فحص وتعديل أسماء المستخدمين في قاعدة بيانات المشروع.
يتصل مباشرة بـ PostgreSQL ويتجاوز مشكلة ترميز Windows-1252.
"""
import sys
import psycopg2
from psycopg2 import sql

CONNECTION_STRING = "host=localhost port=5432 dbname=smartgasstationsimpledb user=postgres password=12345"


def get_connection():
    return psycopg2.connect(CONNECTION_STRING)


def inspect():
    """عرض جميع الأسماء المخزنة."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT "Id", "Name", "Email", "Role", "Status" FROM users ORDER BY "Id"')
            rows = cur.fetchall()
            print("=" * 80)
            print(f"إجمالي المستخدمين: {len(rows)}")
            print("=" * 80)
            for row in rows:
                print(f"  Id={row[0]:<3} | Name={row[1]!r:<25} | Email={row[2]!r:<25} | Role={row[3]} | Status={row[4]}")
            print("=" * 80)

            # بحث تقني: أي اسم يحتوي على "يدر" أو "haid" أو "hidr"
            cur.execute(
                '''
                SELECT "Id", "Name", "Email" FROM users
                WHERE "Name" LIKE %(p1)s
                   OR "Name" LIKE %(p2)s
                   OR "Name" ILIKE %(p3)s
                   OR "Name" ILIKE %(p4)s
                ''',
                {"p1": "%يدر%", "p2": "%حيدر%", "p3": "%haid%", "p4": "%hider%"},
            )
            matches = cur.fetchall()
            print()
            print(f"السجلات التي تحتوي على 'يدر' / 'حيدر' / 'haid' / 'hider': {len(matches)}")
            for row in matches:
                print(f"  Id={row[0]:<3} | Name={row[1]!r:<30} | Email={row[2]!r}")


def fix(old_substring: str, new_substring: str, dry_run: bool = True):
    """استبدال جزء من الاسم في كل السجلات المطابقة."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                'SELECT "Id", "Name" FROM users WHERE "Name" LIKE %(pat)s',
                {"pat": f"%{old_substring}%"},
            )
            before = cur.fetchall()
            print()
            print("=" * 80)
            print(f"البحث عن '{old_substring}' → '{new_substring}'")
            print(f"عدد السجلات المطابقة: {len(before)}")
            print("=" * 80)
            for row in before:
                print(f"  Id={row[0]:<3} | Name={row[1]!r}")

            if not before:
                print("لا توجد سجلات للتعديل.")
                return

            if dry_run:
                print()
                print("[DRY-RUN] لم يُنفَّذ أي تعديل. مرّر dry_run=False للتنفيذ الفعلي.")
                return

            cur.execute(
                '''
                UPDATE users
                SET "Name" = REPLACE("Name", %(old)s, %(new)s)
                WHERE "Name" LIKE %(pat)s
                RETURNING "Id", "Name"
                ''',
                {"old": old_substring, "new": new_substring, "pat": f"%{old_substring}%"},
            )
            updated = cur.fetchall()
            conn.commit()
            print()
            print(f"تم تعديل {len(updated)} سجل:")
            for row in updated:
                print(f"  Id={row[0]:<3} | Name={row[1]!r}")


if __name__ == "__main__":
    args = sys.argv[1:]
    apply = "--apply" in args
    inspect()
    print()
    # المحاولة الأولى: "هيدر" → "حيدر"
    fix("هيدر", "حيدر", dry_run=not apply)
-- ============================================================
-- فحص جميع أسماء المستخدمين لمعرفة الشكل الحقيقي للاسم المخزّن
-- ============================================================

-- عرض كل الأسماء الموجودة في جدول users
SELECT "Id", "Name", "Email", "Role", "Status"
FROM users
ORDER BY "Id";

-- البحث عن أي اسم يحتوي على أحرف مشابهة بأي طريقة
SELECT "Id", "Name", "Email"
FROM users
WHERE "Name" LIKE '%يدر%'
   OR "Name" LIKE '%حيدر%'
   OR "Name" LIKE '%haid%'
   OR "Name" LIKE '%Hayd%'
   OR "Name" LIKE '%Heyd%'
   OR "Name" ILIKE '%ali%';
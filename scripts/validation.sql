-- =====================================================================
-- Milestone 5 — Data Population (DML) & Validation
-- Project: PC Build Recommendation System (Web-Based)
-- Group:   Umer Daraz, Habib, Kashif
--
-- This file contains:
--   (A) At least one UPDATE with a WHERE condition
--   (B) At least one DELETE with a WHERE condition
--   (C) COUNT(*) on every table
--   (D) NULL check on key columns
--   (E) JOIN-based foreign key integrity check
--
-- Run this AFTER schema.sql and load_data.sql have completed successfully.
-- Take a screenshot of each result set; you'll need them for the PDF.
-- =====================================================================

USE pc_build_db;

-- =====================================================================
-- (A) UPDATE operations with WHERE
-- =====================================================================

-- A1. A user changed their email address.
--     Update the email for user_id = 10 to a new address.
UPDATE User
SET    email = 'updated.email@example.com'
WHERE  user_id = 10;

-- Verify the change
SELECT user_id, full_name, email, role
FROM   User
WHERE  user_id = 10;


-- A2. A component price was revised by the admin.
--     Increase the price of all Corsair RAM kits by 10%.
UPDATE Component
SET    price = ROUND(price * 1.10, 2)
WHERE  component_type = 'RAM'
   AND brand = 'Corsair';

-- Verify the change
SELECT component_id, component_name, brand, price
FROM   Component
WHERE  component_type = 'RAM'
   AND brand = 'Corsair';


-- =====================================================================
-- (B) DELETE operations with WHERE
-- =====================================================================

-- B1. Remove a specific build request and (via ON DELETE CASCADE)
--     its dependent Recommended_Build and Build_Component rows.
--     We delete request_id = 80 (the last request).
DELETE FROM Build_Request
WHERE  request_id = 80;

-- Verify the deletion cascaded correctly
SELECT 'Build_Request rows for request 80'      AS check_name, COUNT(*) AS remaining FROM Build_Request     WHERE request_id = 80
UNION ALL
SELECT 'Recommended_Build rows for request 80',                COUNT(*)            FROM Recommended_Build WHERE request_id = 80;
-- Both should return 0.


-- B2. Discontinue a hardware component that is not currently used in any build.
--     We pick a safe component_id that has zero references in Build_Component
--     so the FK constraint does not block the delete.
--     (We use a subquery to find such a component dynamically.)

-- First, show which components are unused (for the screenshot)
SELECT c.component_id, c.component_name, c.component_type, c.brand
FROM   Component c
LEFT JOIN Build_Component bc ON bc.component_id = c.component_id
WHERE  bc.component_id IS NULL;

-- Now delete one of them (the first unused one)
DELETE FROM Component
WHERE  component_id = (
    SELECT component_id FROM (
        SELECT c.component_id
        FROM   Component c
        LEFT JOIN Build_Component bc ON bc.component_id = c.component_id
        WHERE  bc.component_id IS NULL
        ORDER BY c.component_id
        LIMIT 1
    ) AS x
);


-- =====================================================================
-- (C) COUNT(*) for every table
-- =====================================================================

SELECT 'User'              AS table_name, COUNT(*) AS row_count FROM User
UNION ALL
SELECT 'Component',                       COUNT(*)             FROM Component
UNION ALL
SELECT 'Build_Request',                   COUNT(*)             FROM Build_Request
UNION ALL
SELECT 'Recommended_Build',               COUNT(*)             FROM Recommended_Build
UNION ALL
SELECT 'Build_Component',                 COUNT(*)             FROM Build_Component;

-- Expected after the DML above:
--   User              = 60
--   Component         = 65   (was 66, we discontinued 1 unused component in B2)
--   Build_Request     = 79   (was 80, we deleted request 80 in B1)
--   Recommended_Build = 104 or 105 (cascade from B1 removed request 80's builds)
--   Build_Component   = depends on how many components were in request 80's builds


-- =====================================================================
-- (D) NULL check on key columns
--     Every PK, every FK, and every NOT NULL column must show 0 NULLs.
-- =====================================================================

-- User
SELECT 'User.user_id'   AS column_name, COUNT(*) AS null_count FROM User WHERE user_id  IS NULL
UNION ALL SELECT 'User.full_name',  COUNT(*) FROM User WHERE full_name IS NULL
UNION ALL SELECT 'User.email',      COUNT(*) FROM User WHERE email     IS NULL
UNION ALL SELECT 'User.password',   COUNT(*) FROM User WHERE password  IS NULL
UNION ALL SELECT 'User.role',       COUNT(*) FROM User WHERE role      IS NULL

-- Build_Request
UNION ALL SELECT 'Build_Request.request_id',   COUNT(*) FROM Build_Request WHERE request_id   IS NULL
UNION ALL SELECT 'Build_Request.budget',       COUNT(*) FROM Build_Request WHERE budget       IS NULL
UNION ALL SELECT 'Build_Request.purpose',      COUNT(*) FROM Build_Request WHERE purpose      IS NULL
UNION ALL SELECT 'Build_Request.request_date', COUNT(*) FROM Build_Request WHERE request_date IS NULL
UNION ALL SELECT 'Build_Request.user_id (FK)', COUNT(*) FROM Build_Request WHERE user_id      IS NULL

-- Component
UNION ALL SELECT 'Component.component_id',   COUNT(*) FROM Component WHERE component_id   IS NULL
UNION ALL SELECT 'Component.component_name', COUNT(*) FROM Component WHERE component_name IS NULL
UNION ALL SELECT 'Component.component_type', COUNT(*) FROM Component WHERE component_type IS NULL
UNION ALL SELECT 'Component.brand',          COUNT(*) FROM Component WHERE brand          IS NULL
UNION ALL SELECT 'Component.price',          COUNT(*) FROM Component WHERE price          IS NULL

-- Recommended_Build
UNION ALL SELECT 'Recommended_Build.build_id',            COUNT(*) FROM Recommended_Build WHERE build_id            IS NULL
UNION ALL SELECT 'Recommended_Build.total_cost',          COUNT(*) FROM Recommended_Build WHERE total_cost          IS NULL
UNION ALL SELECT 'Recommended_Build.recommendation_date', COUNT(*) FROM Recommended_Build WHERE recommendation_date IS NULL
UNION ALL SELECT 'Recommended_Build.request_id (FK)',     COUNT(*) FROM Recommended_Build WHERE request_id          IS NULL

-- Build_Component
UNION ALL SELECT 'Build_Component.build_component_id', COUNT(*) FROM Build_Component WHERE build_component_id IS NULL
UNION ALL SELECT 'Build_Component.quantity',           COUNT(*) FROM Build_Component WHERE quantity           IS NULL
UNION ALL SELECT 'Build_Component.build_id (FK)',      COUNT(*) FROM Build_Component WHERE build_id           IS NULL
UNION ALL SELECT 'Build_Component.component_id (FK)',  COUNT(*) FROM Build_Component WHERE component_id       IS NULL;

-- Expected: every row shows null_count = 0.


-- =====================================================================
-- (E) JOIN-based foreign key integrity check
--     Each query below returns rows in the CHILD table that have no
--     matching parent row. All four queries should return 0 rows.
-- =====================================================================

-- E1. Build_Request.user_id must reference an existing User
SELECT br.request_id, br.user_id AS orphan_user_id
FROM   Build_Request br
LEFT JOIN User u ON u.user_id = br.user_id
WHERE  u.user_id IS NULL;
-- Expected: 0 rows.

-- E2. Recommended_Build.request_id must reference an existing Build_Request
SELECT rb.build_id, rb.request_id AS orphan_request_id
FROM   Recommended_Build rb
LEFT JOIN Build_Request br ON br.request_id = rb.request_id
WHERE  br.request_id IS NULL;
-- Expected: 0 rows.

-- E3. Build_Component.build_id must reference an existing Recommended_Build
SELECT bc.build_component_id, bc.build_id AS orphan_build_id
FROM   Build_Component bc
LEFT JOIN Recommended_Build rb ON rb.build_id = bc.build_id
WHERE  rb.build_id IS NULL;
-- Expected: 0 rows.

-- E4. Build_Component.component_id must reference an existing Component
SELECT bc.build_component_id, bc.component_id AS orphan_component_id
FROM   Build_Component bc
LEFT JOIN Component c ON c.component_id = bc.component_id
WHERE  c.component_id IS NULL;
-- Expected: 0 rows.


-- =====================================================================
-- BONUS — a single combined "all clear" check that returns ONE row
--         showing every integrity rule passes (good for a clean screenshot).
-- =====================================================================
SELECT
    (SELECT COUNT(*) FROM Build_Request     br LEFT JOIN User              u  ON u.user_id      = br.user_id      WHERE u.user_id      IS NULL) AS orphan_user_in_request,
    (SELECT COUNT(*) FROM Recommended_Build rb LEFT JOIN Build_Request     br ON br.request_id  = rb.request_id   WHERE br.request_id  IS NULL) AS orphan_request_in_build,
    (SELECT COUNT(*) FROM Build_Component   bc LEFT JOIN Recommended_Build rb ON rb.build_id    = bc.build_id     WHERE rb.build_id    IS NULL) AS orphan_build_in_bc,
    (SELECT COUNT(*) FROM Build_Component   bc LEFT JOIN Component         c  ON c.component_id = bc.component_id WHERE c.component_id IS NULL) AS orphan_component_in_bc;
-- Expected: every column = 0.

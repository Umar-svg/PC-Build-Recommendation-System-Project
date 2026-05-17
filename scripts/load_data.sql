-- =====================================================================
-- Milestone 5 — Data Import
-- Project: PC Build Recommendation System (Web-Based)
-- Group:   Umer Daraz, Habib, Kashif
-- =====================================================================

USE pc_build_db;

-- Speed up the import + avoid order-of-load issues for the children below
SET FOREIGN_KEY_CHECKS = 0;
SET UNIQUE_CHECKS      = 0;

-- ---------------------------------------------------------------------
-- 1. User  (60 rows)
-- ---------------------------------------------------------------------
LOAD DATA LOCAL INFILE 'D:/Database_lab_project/milestone_no_3/User.csv'
INTO TABLE User
FIELDS TERMINATED BY ','
       OPTIONALLY ENCLOSED BY '"'
LINES  TERMINATED BY '\r\n'
IGNORE 1 LINES
(user_id, full_name, email, password, role);

-- ---------------------------------------------------------------------
-- 2. Component  (66 rows)
-- ---------------------------------------------------------------------
LOAD DATA LOCAL INFILE 'D:/Database_lab_project/milestone_no_3/Component.csv'
INTO TABLE Component
FIELDS TERMINATED BY ','
       OPTIONALLY ENCLOSED BY '"'
LINES  TERMINATED BY '\r\n'
IGNORE 1 LINES
(component_id, component_name, component_type, brand, price,
 specifications, compatibility_info);

-- ---------------------------------------------------------------------
-- 3. Build_Request  (80 rows)  -- depends on User
-- ---------------------------------------------------------------------
LOAD DATA LOCAL INFILE 'D:/Database_lab_project/milestone_no_3/Build_Request.csv'
INTO TABLE Build_Request
FIELDS TERMINATED BY ','
       OPTIONALLY ENCLOSED BY '"'
LINES  TERMINATED BY '\r\n'
IGNORE 1 LINES
(request_id, budget, purpose, request_date, user_id);

-- ---------------------------------------------------------------------
-- 4. Recommended_Build  (106 rows)  -- depends on Build_Request
-- ---------------------------------------------------------------------
LOAD DATA LOCAL INFILE 'D:/Database_lab_project/milestone_no_3/Recommended_Build.csv'
INTO TABLE Recommended_Build
FIELDS TERMINATED BY ','
       OPTIONALLY ENCLOSED BY '"'
LINES  TERMINATED BY '\r\n'
IGNORE 1 LINES
(build_id, total_cost, recommendation_date, request_id);

-- ---------------------------------------------------------------------
-- 5. Build_Component  (848 rows)  -- depends on Recommended_Build AND Component
-- ---------------------------------------------------------------------
LOAD DATA LOCAL INFILE 'D:/Database_lab_project/milestone_no_3/Build_Component.csv'
INTO TABLE Build_Component
FIELDS TERMINATED BY ','
       OPTIONALLY ENCLOSED BY '"'
LINES  TERMINATED BY '\r\n'
IGNORE 1 LINES
(build_component_id, quantity, build_id, component_id);

-- Re-enable checks
SET FOREIGN_KEY_CHECKS = 1;
SET UNIQUE_CHECKS      = 1;

-- =====================================================================
-- VERIFICATION QUERIES — run these to confirm everything loaded correctly.
-- Expected output is shown next to each query.
-- =====================================================================

-- Row counts (must match exactly)
SELECT 'User'              AS table_name, COUNT(*) AS rows_loaded FROM User              -- 60
UNION ALL SELECT 'Component',              COUNT(*) FROM Component                       -- 66
UNION ALL SELECT 'Build_Request',          COUNT(*) FROM Build_Request                   -- 80
UNION ALL SELECT 'Recommended_Build',      COUNT(*) FROM Recommended_Build               -- 106
UNION ALL SELECT 'Build_Component',        COUNT(*) FROM Build_Component;                -- 848

-- Spot check: total_cost should equal SUM(price*qty) for every build.
-- Expected: 0 rows returned (no mismatches).
SELECT rb.build_id,
       rb.total_cost  AS declared,
       ROUND(SUM(c.price * bc.quantity), 2) AS computed
FROM Recommended_Build rb
JOIN Build_Component bc ON bc.build_id = rb.build_id
JOIN Component       c  ON c.component_id = bc.component_id
GROUP BY rb.build_id, rb.total_cost
HAVING ABS(rb.total_cost - ROUND(SUM(c.price * bc.quantity), 2)) > 0.01;

-- Roles breakdown — should be 5 admin + 55 user
SELECT role, COUNT(*) FROM User GROUP BY role;

-- Sample join: show one full build with all its components
SELECT rb.build_id, br.purpose, br.budget, rb.total_cost,
       c.component_type, c.component_name, c.brand, c.price, bc.quantity
FROM   Recommended_Build rb
JOIN   Build_Request     br ON br.request_id = rb.request_id
JOIN   Build_Component   bc ON bc.build_id   = rb.build_id
JOIN   Component         c  ON c.component_id = bc.component_id
WHERE  rb.build_id = 1
ORDER BY c.component_type;

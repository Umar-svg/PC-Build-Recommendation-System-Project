-- ============================================================================
-- Project   : PC Build Recommendation System (Web-Based)
-- Milestone : 4 — Database Setup (DDL)


-- ============================================================================
-- This script creates the finalized normalized schema from Milestone 2:
--   User, Build_Request, Component, Recommended_Build, Build_Component
-- Drop order is the reverse of create order to respect foreign-key dependencies.
-- ============================================================================

DROP DATABASE IF EXISTS pc_build_db;
CREATE DATABASE pc_build_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;
USE pc_build_db;

-- ----------------------------------------------------------------------------
-- 1. User
-- ----------------------------------------------------------------------------
CREATE TABLE User (
    user_id     INT             NOT NULL AUTO_INCREMENT,
    full_name   VARCHAR(50)     NOT NULL,
    email       VARCHAR(45)     NOT NULL,
    password    VARCHAR(255)    NOT NULL,
    role        VARCHAR(20)     NOT NULL DEFAULT 'user',
    PRIMARY KEY (user_id),
    UNIQUE KEY uq_user_email (email),
    CONSTRAINT chk_user_role CHECK (role IN ('admin', 'user'))
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 2. Build_Request
-- ----------------------------------------------------------------------------
CREATE TABLE Build_Request (
    request_id      INT             NOT NULL AUTO_INCREMENT,
    budget          DECIMAL(10,2)   NOT NULL,
    purpose         VARCHAR(45)     NOT NULL,
    request_date    DATE            NOT NULL,
    user_id         INT             NOT NULL,
    PRIMARY KEY (request_id),
    CONSTRAINT fk_request_user
        FOREIGN KEY (user_id) REFERENCES User(user_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT chk_request_budget CHECK (budget > 0)
) ENGINE=InnoDB;

CREATE INDEX idx_request_user      ON Build_Request(user_id);
CREATE INDEX idx_request_purpose   ON Build_Request(purpose);
CREATE INDEX idx_request_date      ON Build_Request(request_date);

-- ----------------------------------------------------------------------------
-- 3. Component
-- ----------------------------------------------------------------------------
CREATE TABLE Component (
    component_id        INT             NOT NULL AUTO_INCREMENT,
    component_name      VARCHAR(100)    NOT NULL,
    component_type      VARCHAR(45)     NOT NULL,
    brand               VARCHAR(30)     NOT NULL,
    price               DECIMAL(10,2)   NOT NULL,
    specifications      TEXT            NULL,
    compatibility_info  TEXT            NULL,
    PRIMARY KEY (component_id),
    CONSTRAINT chk_component_price CHECK (price >= 0)
) ENGINE=InnoDB;

CREATE INDEX idx_component_type    ON Component(component_type);
CREATE INDEX idx_component_brand   ON Component(brand);
CREATE INDEX idx_component_price   ON Component(price);

-- ----------------------------------------------------------------------------
-- 4. Recommended_Build
-- ----------------------------------------------------------------------------
CREATE TABLE Recommended_Build (
    build_id            INT             NOT NULL AUTO_INCREMENT,
    total_cost          DECIMAL(10,2)   NOT NULL,
    recommendation_date DATE            NOT NULL,
    request_id          INT             NOT NULL,
    PRIMARY KEY (build_id),
    CONSTRAINT fk_build_request
        FOREIGN KEY (request_id) REFERENCES Build_Request(request_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT chk_build_total_cost CHECK (total_cost >= 0)
) ENGINE=InnoDB;

CREATE INDEX idx_build_request     ON Recommended_Build(request_id);
CREATE INDEX idx_build_date        ON Recommended_Build(recommendation_date);

-- ----------------------------------------------------------------------------
-- 5. Build_Component (junction table)
-- ----------------------------------------------------------------------------
CREATE TABLE Build_Component (
    build_component_id  INT     NOT NULL AUTO_INCREMENT,
    quantity            INT     NOT NULL DEFAULT 1,
    build_id            INT     NOT NULL,
    component_id        INT     NOT NULL,
    PRIMARY KEY (build_component_id),
    CONSTRAINT fk_bc_build
        FOREIGN KEY (build_id) REFERENCES Recommended_Build(build_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_bc_component
        FOREIGN KEY (component_id) REFERENCES Component(component_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    CONSTRAINT uq_bc_build_component UNIQUE (build_id, component_id),
    CONSTRAINT chk_bc_quantity CHECK (quantity > 0)
) ENGINE=InnoDB;

CREATE INDEX idx_bc_build          ON Build_Component(build_id);
CREATE INDEX idx_bc_component      ON Build_Component(component_id);

select* from Build_Component;
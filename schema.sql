-- ============================================================
-- CampusLink: Campus Lost & Found Portal
-- Database Schema (MySQL)
-- ============================================================

CREATE DATABASE IF NOT EXISTS campuslink;
USE campuslink;

-- ============================================================
-- TABLE 1: Users
-- Stores registered students/staff who can post or claim items.
-- ============================================================
CREATE TABLE Users (
    user_id       INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(100)        NOT NULL,
    roll_number   VARCHAR(20)         UNIQUE NOT NULL,
    email         VARCHAR(150)        UNIQUE NOT NULL,
    password_hash VARCHAR(255)        NOT NULL,
    dept          VARCHAR(100)        NOT NULL,
    role          ENUM('student', 'admin') DEFAULT 'student',
    created_at    TIMESTAMP           DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- TABLE 2: Categories
-- Lookup table for item categories (Electronics, Keys, etc.)
-- ============================================================
CREATE TABLE Categories (
    category_id   INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(100) UNIQUE NOT NULL,
    description   VARCHAR(255)
);

-- Seed default categories
INSERT INTO Categories (category_name, description) VALUES
    ('Electronics',  'Phones, laptops, earbuds, chargers, etc.'),
    ('Documents',    'ID cards, marksheets, notebooks, etc.'),
    ('Keys',         'House keys, bike keys, locker keys, etc.'),
    ('Clothing',     'Jackets, bags, scarves, caps, etc.'),
    ('Accessories',  'Watches, spectacles, wallets, jewelry, etc.'),
    ('Sports',       'Sports equipment and gear'),
    ('Stationery',   'Pens, calculators, drawing instruments, etc.'),
    ('Other',        'Anything that does not fit above categories');

-- ============================================================
-- TABLE 3: Items
-- Core table for every lost/found item posted on the portal.
-- FK -> Users (posted by), Categories (item type)
-- ============================================================
CREATE TABLE Items (
    item_id      INT AUTO_INCREMENT PRIMARY KEY,
    title        VARCHAR(150)                    NOT NULL,
    description  TEXT,
    type           ENUM('LOST', 'FOUND')           NOT NULL,
    location       VARCHAR(200),
    image_url      VARCHAR(500),
    status         ENUM('ACTIVE', 'REMOVED', 'RESOLVED')      DEFAULT 'ACTIVE',
    is_in_custody  BOOLEAN                         DEFAULT FALSE,
    user_id        INT                             NOT NULL,
    category_id  INT                             NOT NULL,
    posted_at    TIMESTAMP                       DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP                       DEFAULT CURRENT_TIMESTAMP
                                                 ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_items_user
        FOREIGN KEY (user_id)
        REFERENCES Users (user_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_items_category
        FOREIGN KEY (category_id)
        REFERENCES Categories (category_id)
        ON DELETE RESTRICT,

    -- Full-text index to power the keyword matching engine
    FULLTEXT idx_item_search (title, description)
);

-- ============================================================
-- TABLE 4: Claims
-- Records when a user claims ownership of a Found item.
-- FK -> Items (claimed item), Users (person claiming)
-- ============================================================
CREATE TABLE Claims (
    claim_id          INT AUTO_INCREMENT PRIMARY KEY,
    item_id           INT                                     NOT NULL,
    claimer_id        INT                                     NOT NULL,
    proof_description   TEXT,
    handoff_instructions TEXT,
    status              ENUM('PENDING', 'AWAITING_COLLECTION', 'APPROVED', 'REJECTED') DEFAULT 'PENDING',
    created_at          TIMESTAMP                               DEFAULT CURRENT_TIMESTAMP,
    resolved_at         TIMESTAMP                               NULL,

    CONSTRAINT fk_claims_item
        FOREIGN KEY (item_id)
        REFERENCES Items (item_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_claims_claimer
        FOREIGN KEY (claimer_id)
        REFERENCES Users (user_id)
        ON DELETE CASCADE,

    -- One active claim per user per item
    UNIQUE KEY uq_claim_per_user (item_id, claimer_id)
);

-- ============================================================
-- TABLE 5: Activity_Logs
-- Audit trail for all significant actions on items.
-- FK -> Items (which item was acted upon)
-- ============================================================
CREATE TABLE Activity_Logs (
    log_id       INT AUTO_INCREMENT PRIMARY KEY,
    item_id      INT          NOT NULL,
    action_taken VARCHAR(255) NOT NULL,
    performed_by INT,                       -- NULL = system action
    timestamp    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_logs_item
        FOREIGN KEY (item_id)
        REFERENCES Items (item_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_logs_user
        FOREIGN KEY (performed_by)
        REFERENCES Users (user_id)
        ON DELETE SET NULL
);

-- ============================================================
-- Useful Views
-- ============================================================

-- View: Active lost items with category and poster info
CREATE OR REPLACE VIEW v_active_lost_items AS
SELECT
    i.item_id,
    i.title,
    i.description,
    i.location,
    i.image_url,
    i.posted_at,
    c.category_name,
    u.name        AS posted_by,
    u.roll_number AS roll_no
FROM Items i
JOIN Categories c ON i.category_id = c.category_id
JOIN Users u      ON i.user_id     = u.user_id
WHERE i.type = 'LOST' AND i.status = 'ACTIVE';

-- View: Active found items with category and finder info
CREATE OR REPLACE VIEW v_active_found_items AS
SELECT
    i.item_id,
    i.title,
    i.description,
    i.location,
    i.image_url,
    i.posted_at,
    c.category_name,
    u.name        AS found_by,
    u.roll_number AS roll_no
FROM Items i
JOIN Categories c ON i.category_id = c.category_id
JOIN Users u      ON i.user_id     = u.user_id
WHERE i.type = 'FOUND' AND i.status = 'ACTIVE';

-- View: Claims with full item & user details (for admin dashboard)
CREATE OR REPLACE VIEW v_claim_details AS
SELECT
    cl.claim_id,
    cl.status        AS claim_status,
    cl.proof_description,
    cl.created_at    AS claimed_at,
    i.title          AS item_title,
    i.type           AS item_type,
    i.location,
    u_claimer.name   AS claimer_name,
    u_claimer.email  AS claimer_email,
    u_poster.name    AS poster_name
FROM Claims cl
JOIN Items i          ON cl.item_id   = i.item_id
JOIN Users u_claimer  ON cl.claimer_id = u_claimer.user_id
JOIN Users u_poster   ON i.user_id    = u_poster.user_id;

-- ============================================================
-- Stored Procedure: Keyword + Category Matching Engine
-- Finds FOUND items that match a LOST item's category/keywords
-- ============================================================
DELIMITER $$

CREATE PROCEDURE sp_match_lost_item(IN p_item_id INT)
BEGIN
    DECLARE v_category INT;
    DECLARE v_title    VARCHAR(150);

    SELECT category_id, title
    INTO   v_category, v_title
    FROM   Items
    WHERE  item_id = p_item_id AND type = 'LOST';

    SELECT
        i.item_id,
        i.title,
        i.description,
        i.location,
        i.image_url,
        i.posted_at,
        u.name AS found_by,
        MATCH(i.title, i.description) AGAINST (v_title IN NATURAL LANGUAGE MODE) AS relevance_score
    FROM   Items i
    JOIN   Users u ON i.user_id = u.user_id
    WHERE  i.type        = 'FOUND'
      AND  i.status      = 'ACTIVE'
      AND  i.category_id = v_category
    HAVING relevance_score > 0
        OR i.category_id = v_category   -- fallback: same category even without keyword match
    ORDER BY relevance_score DESC
    LIMIT 10;
END$$

DELIMITER ;

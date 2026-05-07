# 🎓 CampusLink — Campus Lost & Found Portal

> A DBMS project built with **FastAPI**, **MySQL**, and **React + Tailwind CSS**.  
> Helps university students report lost items, post found items, and claim them back.

---

## 📁 Project Structure

```
DBMS project/
├── schema.sql              ← MySQL schema: 5 tables + views + stored procedure
├── README.md               ← You are here
└── backend/
    ├── requirements.txt    ← Python dependencies
    ├── .env.example        ← Copy to .env and fill in your DB credentials
    └── app/
        ├── main.py         ← FastAPI entry point
        ├── database.py     ← SQLAlchemy engine & session
        ├── models.py       ← ORM models (5 tables)
        ├── schemas.py      ← Pydantic request/response shapes
        ├── auth.py         ← JWT helpers & auth dependencies
        └── routers/
            ├── auth.py        ← /api/auth/*
            ├── items.py       ← /api/items/*
            ├── claims.py      ← /api/claims/*
            ├── categories.py  ← /api/categories/*
            └── logs.py        ← /api/logs/*
```

---

## 🗄️ Database Architecture — 5 Tables

### Entity-Relationship Overview

```
Users ──────< Items >────── Categories
               │
               └──────< Claims >────── Users (claimer)
               │
               └──────< Activity_Logs
```

### Table-by-Table Breakdown

#### 1. `Users`
Stores every registered student/staff member.

| Column        | Type         | Notes                          |
|---------------|--------------|--------------------------------|
| user_id       | INT (PK)     | Auto-incremented primary key   |
| name          | VARCHAR(100) | Full name                      |
| roll_number   | VARCHAR(20)  | Unique university roll number  |
| email         | VARCHAR(150) | Unique login email             |
| password_hash | VARCHAR(255) | bcrypt hash — never plain text |
| dept          | VARCHAR(100) | Department (e.g., CSE, ECE)    |
| role          | ENUM         | `student` or `admin`           |

#### 2. `Categories`
Lookup table pre-seeded with 8 categories (Electronics, Documents, Keys, etc.).

| Column        | Type         | Notes                    |
|---------------|--------------|--------------------------|
| category_id   | INT (PK)     | Auto-incremented          |
| category_name | VARCHAR(100) | Unique category label     |
| description   | VARCHAR(255) | Short description         |

#### 3. `Items` ⬅️ Core Table
Every lost or found item lives here.

| Column      | Type         | Notes                                   |
|-------------|--------------|------------------------------------------|
| item_id     | INT (PK)     | Auto-incremented                         |
| title       | VARCHAR(150) | Short title, e.g., "Blue Boat Earbuds"  |
| description | TEXT         | Detailed description                     |
| type        | ENUM         | `LOST` or `FOUND`                        |
| location    | VARCHAR(200) | Where it was lost/found                  |
| image_url   | VARCHAR(500) | Path to uploaded image                   |
| status      | ENUM         | `ACTIVE` (default) or `RESOLVED`         |
| user_id     | INT (FK)     | → `Users.user_id` — who posted this      |
| category_id | INT (FK)     | → `Categories.category_id`               |

**Full-text index** on `(title, description)` powers the matching engine.

#### 4. `Claims`
Records when a student claims ownership of a **Found** item.

| Column            | Type    | Notes                                          |
|-------------------|---------|------------------------------------------------|
| claim_id          | INT (PK)| Auto-incremented                               |
| item_id           | INT (FK)| → `Items.item_id`                              |
| claimer_id        | INT (FK)| → `Users.user_id` — who is claiming            |
| proof_description | TEXT    | Description of proof of ownership              |
| status            | ENUM    | `PENDING` → `APPROVED` or `REJECTED`           |
| resolved_at       | DATETIME| Set when claim is approved/rejected            |

**Unique constraint** on `(item_id, claimer_id)` prevents duplicate claims.

#### 5. `Activity_Logs`
Immutable audit trail. Every key action writes a row here automatically.

| Column       | Type         | Notes                              |
|--------------|--------------|------------------------------------|
| log_id       | INT (PK)     | Auto-incremented                   |
| item_id      | INT (FK)     | → `Items.item_id`                  |
| action_taken | VARCHAR(255) | Human-readable description         |
| performed_by | INT (FK)     | → `Users.user_id` (NULL = system)  |
| timestamp    | DATETIME     | Auto-set on insert                 |

---

## 🔄 Data Flow — How the 5 Tables Work Together

```
1. REGISTER / LOGIN
   User registers → row inserted into Users
   User logs in → JWT issued (contains user_id)

2. POST AN ITEM
   Authenticated user fills the form →
   Row inserted into Items (user_id FK, category_id FK)
   Row inserted into Activity_Logs ("Item posted as LOST by Alice")

3. MATCHING ENGINE
   System queries Items WHERE type='FOUND' AND category_id = <same>
   Ranks results by keyword overlap with the lost item's title
   Returns top-10 FOUND items as suggestions

4. SUBMIT A CLAIM
   Another user sees a FOUND item and clicks "This is mine" →
   Row inserted into Claims (item_id FK, claimer_id FK, status=PENDING)
   Row inserted into Activity_Logs ("Claim submitted by Bob")

5. APPROVE / REJECT CLAIM
   Item poster or admin changes claim status →
   Claims.status updated to APPROVED or REJECTED
   If APPROVED → Items.status updated to RESOLVED
   Row inserted into Activity_Logs ("Claim approved. Item returned to Bob.")
```

### Visual Flow Diagram

```
[User] ──registers──► [Users table]
                              │
                    logs in, gets JWT
                              │
                              ▼
[User] ──posts item──► [Items table] ──► [Activity_Logs]
                              │
                    matching engine reads
                              │
                              ▼
[Other User] ──claims──► [Claims table] ──► [Activity_Logs]
                              │
                    finder approves
                              │
                              ▼
              Items.status = RESOLVED ──► [Activity_Logs]
```

---

## 🚀 Getting Started

### 1. Database Setup

```bash
# Log in to MySQL
mysql -u root -p

# Run the schema
source /path/to/DBMS\ project/schema.sql
```

### 2. Backend Setup

```bash
cd "DBMS project/backend"

# Copy and edit environment variables
cp .env.example .env
# Edit .env: set DB_PASSWORD and SECRET_KEY

# Create a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn app.main:app --reload
```

The API will be available at **http://localhost:8000**  
Interactive docs: **http://localhost:8000/docs**

### 3. Frontend Setup (React + Tailwind)

```bash
cd "DBMS project/frontend"   # (to be created)
npm install
npm run dev
```

---

## 🔑 API Endpoints Quick Reference

| Method | Endpoint                          | Auth? | Description                    |
|--------|-----------------------------------|-------|--------------------------------|
| POST   | /api/auth/register                | ❌    | Register new user              |
| POST   | /api/auth/login                   | ❌    | Login, get JWT                 |
| GET    | /api/auth/me                      | ✅    | Current user info              |
| GET    | /api/items                        | ❌    | List items (filter supported)  |
| POST   | /api/items                        | ✅    | Post a lost/found item         |
| GET    | /api/items/{id}                   | ❌    | Get item details               |
| PATCH  | /api/items/{id}                   | ✅    | Update own item                |
| DELETE | /api/items/{id}                   | ✅    | Delete own item                |
| POST   | /api/items/upload                 | ✅    | Upload image → returns URL     |
| GET    | /api/items/{id}/match             | ❌    | Matching engine suggestions    |
| POST   | /api/claims                       | ✅    | Submit a claim                 |
| GET    | /api/claims/my                    | ✅    | My submitted claims            |
| GET    | /api/claims/received              | ✅    | Claims on items I posted       |
| PATCH  | /api/claims/{id}/status           | ✅    | Approve / reject a claim       |
| GET    | /api/categories                   | ❌    | List all categories            |
| GET    | /api/logs/item/{id}               | ✅    | Audit trail for an item        |
| GET    | /api/logs/recent                  | 🔐    | Recent logs (admin only)       |

---

## 🛠️ Tech Stack

| Layer     | Technology                  |
|-----------|-----------------------------|
| Frontend  | React + Tailwind CSS (Vite) |
| Backend   | Python + FastAPI            |
| Database  | MySQL 8+                    |
| Auth      | JWT (python-jose + bcrypt)  |
| ORM       | SQLAlchemy 2.0              |

---

## 👥 Team

| Name | Role |
|------|------|
|      | Frontend Developer |
|      | Backend Developer  |
|      | Database Designer  |

---

*Built as a DBMS course project.*

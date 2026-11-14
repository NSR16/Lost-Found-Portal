CampusLink --- Campus Lost & Found Portal
A DBMS project built with FastAPI, MySQL, and React +
Tailwind CSS.

CampusLink helps university students report lost items, post found
items, discover potential matches, and submit claims to recover their
belongings.

✨ Key Features
- Student authentication: Register and sign in using university
  account details.
- Lost and found listings: Create posts for lost or found items,
  including descriptions, categories, locations, and images.
- Browse and search: View recent listings, filter by item type and
  category, and search titles and descriptions.
- Potential item matching: Find active found-item listings in the
  same category as a lost item, ranked by keyword overlap.
- Claim management: Submit ownership details, review claims
  received on your listings, and approve or reject claims.
- Dashboard: View reported items, submitted and received claims,
  and summary statistics.
- Activity tracking: Maintain an audit trail of significant item
  and claim actions.
- Role-based access: Support student and admin roles, with
  authorization enforced by the backend.
🛠️ Tech Stack
  Layer            Technology
  Frontend         React + Vite
UI               Tailwind CSS + daisyUI
HTTP client      Axios
Backend          Python + FastAPI
Database         MySQL 8+
Authentication   JWT (python-jose) + bcrypt
ORM              SQLAlchemy 2.0
📁 Project Structure
DBMS project/
├── schema.sql              # MySQL schema, seed data, views, and matching procedure
├── README.md
├── frontend/
│   ├── package.json        # Vite scripts and React dependencies
│   ├── index.html
│   └── src/
│       ├── App.jsx         # Authentication, dashboard, feed, and claim state
│       ├── api.js          # Axios client for the FastAPI server
│       └── components/     # Auth, navigation, item cards, forms, and tables
└── backend/
    ├── requirements.txt
    ├── .env.example        # Copy to .env and configure locally
    ├── uploads/            # Uploaded item images
    └── app/
        ├── main.py         # FastAPI entry point and router registration
        ├── database.py     # SQLAlchemy engine and session
        ├── models.py       # ORM models
        ├── schemas.py      # Pydantic request/response schemas
        ├── auth.py         # Password hashing and JWT dependencies
        └── routers/
            ├── auth.py
            ├── items.py
            ├── claims.py
            ├── categories.py
            └── logs.py
🗄️ Database Architecture --- 5 Tables
CampusLink uses five main relational tables to manage users, item
listings, categories, claims, and activity history.
Entity-Relationship Overview
Users ──────< Items >────── Categories
               │
               ├──────< Claims >────── Users (claimer)
               │
               └──────< Activity_Logs
Table-by-Table Breakdown
1. Users
Stores every registered student or staff member.
  Column                  Type                    Notes
  user_id               INT (PK)                Auto-incremented
primary key

  name                  VARCHAR(100)            Full name

  roll_number           VARCHAR(20)             Unique university roll
number

  email                 VARCHAR(150)            Unique login email

  password_hash         VARCHAR(255)            bcrypt hash; passwords
are not stored in plain
text

  dept                  VARCHAR(100)            Department (e.g., CSE,
ECE)

  role                  ENUM                    student or admin
created_at            TIMESTAMP               Account creation time
2. Categories
Lookup table pre-seeded with eight categories, such as Electronics,
Documents, and Keys.

  Column            Type           Notes
  category_id     INT (PK)       Auto-incremented primary key
category_name   VARCHAR(100)   Unique category label
description     VARCHAR(255)   Short description
3. Items --- Core Table
Stores every lost or found item listing.
  Column                  Type                    Notes
  item_id               INT (PK)                Auto-incremented primary
key

  title                 VARCHAR(150)            Short title, e.g., "Blue
Boat Earbuds"

  description           TEXT                    Detailed item description

  type                  ENUM                    LOST or FOUND

  location              VARCHAR(200)            Where the item was lost or
found

  image_url             VARCHAR(500)            Path to the uploaded image

  status                ENUM                    ACTIVE (default),
REMOVED, or RESOLVED

  is_in_custody         BOOLEAN                 Whether the finder
currently holds the item

  user_id               INT (FK)                References
Users.user_id;
identifies the poster

  category_id           INT (FK)                References
Categories.category_id

  posted_at             TIMESTAMP               Posting time
updated_at            TIMESTAMP               Last update time
A full-text index on (title, description) supports text-based item
searching and matching.
4. Claims
Records when a user responds to a lost or found item.
  Column                   Type                    Notes
  claim_id               INT (PK)                Auto-incremented primary
key

  item_id                INT (FK)                References
Items.item_id

  claimer_id             INT (FK)                References
Users.user_id;
identifies the claimant

  proof_description      TEXT                    Description of proof of
ownership

  handoff_instructions   TEXT                    Optional collection
details

  status                 ENUM                    Schema includes
PENDING,
APPROVED, and
REJECTED

  created_at             TIMESTAMP               Claim submission time
resolved_at            DATETIME                Set when the claim is
approved or rejected
A unique constraint on (item_id, claimer_id) prevents the same user
from submitting duplicate claims for the same item.

Implementation note: The current Python API model uses PENDING,
APPROVED, and REJECTED claim statuses. The SQL schema also includes
AWAITING_COLLECTION.
5. Activity_Logs
Maintains an audit trail of significant item and claim actions.
  Column                  Type                    Notes
  log_id                INT (PK)                Auto-incremented
primary key

  item_id               INT (FK)                References
Items.item_id

  action_taken          VARCHAR(255)            Human-readable action
description

  performed_by          INT (FK)                References
Users.user_id; NULL
represents a system
action
timestamp             DATETIME                Automatically set on
insert
🔄 How the Application Works
1. Registration and Login
- A user registers and their account details are stored in Users.
- On successful login, the backend issues a JWT containing the user's
  ID.
2. Posting an Item
- An authenticated user submits a lost-item or found-item form.
- The item is stored in Items, linked to its poster and category
  through foreign keys.
- An entry is added to Activity_Logs to record the action.
3. Browsing and Matching
- Users browse recent active lost and found listings.
- Listings can be filtered by type and searched by title or
  description.
- For a lost item, the matching endpoint can return up to 10 active
  found-item listings from the same category, ranked by keyword
  overlap.
4. Submitting a Claim
- A user responds to a listing and provides details or proof related
  to the item.
- A record is inserted into Claims with an initial status of
  PENDING.
- The action is recorded in Activity_Logs.
5. Approving or Rejecting a Claim
- The item's poster or an admin changes the claim status.
- The claim is updated to APPROVED or REJECTED.
- When a claim is approved, the associated item's status is updated to
  RESOLVED.
- The action is recorded in Activity_Logs.
Matching Mechanism
The matching endpoint suggests potentially relevant found-item listings
for a lost item:
1. It uses the lost item's category to identify relevant found-item
   listings.
2. It considers active FOUND listings in that category.
3. It ranks the candidate listings by keyword overlap.
4. It returns up to 10 matching suggestions.
This is a keyword-based matching mechanism; a suggested match should be
treated as a lead for the user to verify, not as confirmation that two
listings refer to the same physical item.
🚀 Getting Started
Prerequisites
Make sure the following are installed and available:
- Python
- Node.js and npm
- MySQL 8+
- Git (if cloning the repository)
1. Database Setup
From the repository root, run the SQL script to create the database
objects, seed categories, and set up the views and matching procedure.

Windows PowerShell:
cmd /c "mysql -u root -p < schema.sql"
macOS/Linux or Git Bash:
mysql -u root -p < schema.sql
Enter your MySQL password when prompted.

The backend also calls SQLAlchemy create_all() at startup to create
missing ORM tables. It does not migrate existing tables or create
the views and stored procedure defined in schema.sql.

Schema alignment note: The ORM model uses an Items.is_deleted
column for soft deletion, but the current schema.sql does not define
it. Since create_all() does not alter an existing table, add the
column to an already-created database before using the item endpoints:
ALTER TABLE Items
ADD COLUMN is_deleted BOOLEAN NOT NULL DEFAULT FALSE;
If the schema is updated to include this column before initial database
setup, this manual alteration is not needed.
2. Backend Setup
Open a terminal and navigate to the backend directory:
cd backend
Create a local environment file from the example:
cp .env.example .env
On Windows PowerShell, you can also copy it with:
Copy-Item .env.example .env
Edit .env and configure the database connection and secret key:
DB_HOST=localhost
DB_PORT=3306
DB_NAME=your_database_name
DB_USER=your_mysql_username
DB_PASSWORD=your_mysql_password
SECRET_KEY=replace_with_a_long_random_secret
Use the variable names and any additional settings defined in your
actual .env.example. Keep .env local and do not commit real
credentials.

Create and activate a virtual environment:
python -m venv .venv
Windows PowerShell:
.\.venv\Scripts\Activate.ps1
macOS/Linux:
source .venv/bin/activate
Install dependencies and start the backend:
pip install -r requirements.txt
uvicorn app.main:app --reload
The API will be available at:
- API base URL: http://localhost:8000
- Interactive API documentation: http://localhost:8000/docs
3. Frontend Setup
Open another terminal and navigate to the frontend directory:
cd frontend
npm install
npm run dev
Open the Vite URL printed in the terminal, normally
http://localhost:5173.

The frontend's Axios client calls http://localhost:8000. The FastAPI
CORS configuration allows the Vite localhost origins.

Useful frontend commands:
npm run build   # Create the production bundle in frontend/dist
npm run lint    # Run ESLint
🔑 API Endpoints Quick Reference
  Method            Endpoint                    Auth?             Description
  POST              /api/auth/register        No                Register a new
user

  POST              /api/auth/login           No                Log in and
receive a JWT

  GET               /api/auth/me              Yes               Get the current
user's
information

  GET               /api/items                No                List recent
items; supports
type, category,
status, and
search filters

  GET               /api/items/my             Yes               List the
signed-in user's
items

  POST              /api/items                Yes               Post a lost or
found item

  GET               /api/items/{id}           No                Get item details

  PATCH             /api/items/{id}           Yes               Update an item

  PATCH             /api/items/{id}/delete    Yes               Soft-delete an
item

  DELETE            /api/items/{id}           Yes               Permanently
delete an item

  GET               /api/items/{id}/match     No                Suggest active
found items for a
lost item

  POST              /api/claims               Yes               Respond to a lost
or found item

  GET               /api/claims/my            Yes               List claims
submitted by the
current user

  GET               /api/claims/received      Yes               List claims on
the current
user's items

  PATCH             /api/claims/{id}/status   Yes               Update a claim's
status

  GET               /api/categories           No                List all
categories

  GET               /api/categories/{id}      No                Get a category

  GET               /api/logs/item/{id}       Yes               View an item's
audit trail (item
owner or admin)
GET               /api/logs/recent          Admin             View recent
activity logs
(admin only)
🧭 Frontend Functionality
- Register and sign in with university account details.
- Browse recent lost and found items, filter by type, and search
  titles and descriptions.
- Report a lost or found item with its category, location, image, and
  custody status.
- Use a responsive dashboard with a left navigation sidebar, search
  bar, item feed, and statistics.
- View submitted claims, reported items, and claims received on your
  listings.
- Prevent users from claiming their own listings in the UI; ownership
  is cross-referenced against the authenticated user's item list.
- Receive toast notifications for report, claim, and claim-management
  actions.
The backend remains authoritative for authentication, authorization, and
ownership checks. Frontend checks are for user experience and do not
replace server-side validation.
Built as a DBMS course project.
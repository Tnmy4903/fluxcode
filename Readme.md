# 🚀 FluxCode Backend (FastAPI + MongoDB)

This is the backend API for the **FluxCode Startup Website** system.
It provides all the server-side functionality including authentication, project handling, blog management, invoice generation, uploads, email alerts, and newsletter broadcasting.

---

## 📦 Tech Stack
- **Framework:** FastAPI
- **Database:** MongoDB (Atlas)
- **Auth:** JWT (custom with roles: `admin`, `client`)
- **Email Service:** Mailgun
- **PDF Generation:** ReportLab
- **File Uploads:** Local disk storage (served via endpoint)
- **Async DB Driver:** Motor

---

## 🧩 Project Structure
```
backend/
├── app/
│   ├── api/                 # All route handlers
│   ├── db/                  # DB connection, models, schemas
│   ├── services/            # Email + PDF generation utilities
│   ├── uploads/             # Uploaded files
│   ├── config.py            # Env configuration
│   └── main.py              # FastAPI app entry point
├── .env                     # Environment variables
├── requirements.txt         # Dependencies
```

---

## ⚙️ Features
### ✅ Auth (JWT)
- `POST /api/auth/signup` — Register new user (client role)
- `POST /api/auth/login` — Login to receive JWT token

### 🧑‍💼 Admin
- `GET /api/admin/dashboard` — Auth check
- `GET /api/admin/projects` — List all projects
- `PATCH /api/admin/projects/{id}/status` — Update status
- `PATCH /api/admin/projects/{id}/budget` — Update budget
- `POST /api/admin/projects/{id}/invoice` — Generate invoice PDF
- `GET /api/admin/uploads` — List uploaded files
- `DELETE /api/admin/uploads/{id}` — Delete uploaded file
- `GET /api/admin/summary` — Platform summary stats
- `POST /api/admin/invoices/{id}/send` — Send invoice to client via Mailgun

### 🧑‍💻 Client
- `POST /api/projects/` — Submit new project
- `GET /api/projects/` — View own projects
- `POST /api/uploads/` — Upload file to project
- `GET /api/uploads/{filename}` — (Admin) View uploaded file

### 📚 Blogs (Public Read, Admin Write)
- `POST /api/blogs/` — Admin create blog
- `GET /api/blogs/` — Public fetch all blogs
- `GET /api/blogs/{slug}` — View blog + increment views
- `DELETE /api/blogs/{id}` — Admin delete blog

### 🧾 Invoices
- `GET /api/invoices/{project_id}` — Client view invoice
- `PATCH /api/invoices/{invoice_id}` — Admin update paid/unpaid

### 📬 Contact / Newsletter
- `POST /api/public/contact` — Submit contact form (sends alert to admin)
- `POST /api/public/newsletter` — Subscribe to newsletter
- `POST /api/newsletter/send` — Admin broadcasts newsletter (optional attachment)

---

## 📁 Environment Variables (`.env`)
Create a `.env` file in the backend root:
```
MONGO_URI=<your_mongodb_atlas_uri>
JWT_SECRET=<your_jwt_secret>
ACCESS_TOKEN_EXPIRE_MINUTES=1440
MAILGUN_API_KEY=<your_mailgun_api_key>
MAILGUN_DOMAIN=<your_mailgun_domain>
ALERT_RECEIVER_EMAIL=<your_admin_email>
```

---

## 🧪 Testing Setup
- ✅ Use Postman to test all routes with JWT
- ✅ Use MongoDB Compass to view database collections

---

## ▶️ Run Backend (First Time)
### 1. Clone and Navigate
```bash
git clone <repo-url>
cd backend
```

### 2. Create Virtual Environment (Optional but Recommended)
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file and paste all values as shown above.

### 5. Run the Server
```bash
uvicorn app.main:app --reload
```

Server will run at: `http://localhost:8000`

---

## 📂 File Uploads Path
Uploaded files are saved in:
```
app/uploads/
```
Accessible via:
```
GET /api/uploads/{filename}
```

---

## 📌 Notes
- JWT tokens must be passed via `Authorization: Bearer <token>` in headers.
- All protected routes verify roles (`admin` vs `client`).
- Mailgun is used for sending contact alerts, invoices, and newsletters.
- ReportLab is used to generate invoice PDFs server-side.

---

## 📮 Contact
If you face any issues, raise an issue or contact the admin email set in `.env` → `ALERT_RECEIVER_EMAIL`.

---

## ✅ Status
**Backend API is Production-Ready ✅**

---



# 🎓 Student Result Management System

A web-based **Student Result Management System** developed using **Python Flask, SQLite, SQLAlchemy, HTML, CSS, and Bootstrap**. The system provides separate access for administrators and teachers to manage students, subjects, marks, and academic results efficiently.

## 🌐 Live Demo

**Live Website:** https://student-result-system-1x4h.onrender.com

---

## 🚀 Features

### 🔐 Authentication

* Admin login
* Teacher login
* Session-based authentication
* Role-based access control
* Secure password handling

### 👨‍🎓 Student Management

* Add students
* Update student information
* Delete students
* View student details
* Search and manage student records

### 📚 Subject Management

* Add subjects
* Update subjects
* Delete subjects
* Manage subject information

### 📝 Result Management

* Enter student marks
* Update marks
* Calculate total marks
* Calculate percentage
* Calculate grades
* View complete student results

### 📄 Result PDF

* Generate student result reports
* Download/print result documents
* Professional result format

### 📊 Dashboard

* Student statistics
* Subject statistics
* Result overview
* Easy-to-use management interface

---

## 🛠️ Tech Stack

| Technology | Usage                     |
| ---------- | ------------------------- |
| Python     | Programming Language      |
| Flask      | Backend Web Framework     |
| SQLAlchemy | ORM / Database Management |
| SQLite     | Database                  |
| HTML5      | Structure                 |
| CSS3       | Styling                   |
| Bootstrap  | Responsive UI             |
| Jinja2     | Template Engine           |
| ReportLab  | PDF Generation            |
| Gunicorn   | Production Server         |
| Render     | Deployment                |

---

## 📁 Project Structure

```text
student-result-management-system/
│
├── app.py
├── config.py
├── run.py
├── requirements.txt
├── student_results.db
│
├── static/
│   ├── css/
│   ├── js/
│   ├── images/
│   └── uploads/
│
├── templates/
│   ├── admin/
│   ├── teacher/
│   ├── auth/
│   └── ...
│
└── README.md
```

---

## ⚙️ Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/student-result-management-system.git
```

### 2. Navigate to the Project

```bash
cd student-result-management-system
```

### 3. Create Virtual Environment

```bash
python -m venv venv
```

### 4. Activate Virtual Environment

**Windows:**

```bash
venv\Scripts\activate
```

**Linux/macOS:**

```bash
source venv/bin/activate
```

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

### 6. Run the Application

```bash
python run.py
```

The application will be available at:

```text
http://127.0.0.1:5000
```

---

## 🔑 Demo Credentials

### Admin

```text
Username: admin
Password: admin123
```

### Teacher

```text
Username: teacher
Password: teacher123
```

> ⚠️ These credentials are provided only for demonstration/testing purposes. Change the default credentials before using the application in a production environment.

---

## ☁️ Deployment

This project is deployed using **Render**.

### Build Command

```bash
pip install -r requirements.txt
```

### Start Command

```bash
gunicorn app:app
```

### Live Application

https://student-result-system-1x4h.onrender.com

---

## 🔄 Automatic Deployment

The project is connected to GitHub and Render.

After making changes in VS Code:

```bash
git add .
git commit -m "Update project"
git push origin main
```

Render automatically detects the new GitHub commit and deploys the updated version.

---

## 🔒 Security

* Passwords are handled securely
* Authentication is required for protected pages
* Role-based access is implemented
* Secret configuration should be stored using environment variables
* Default credentials should be changed before production use

---

## 🎯 Future Enhancements

* PostgreSQL database integration
* Email notifications
* Student portal
* Parent portal
* Advanced result analytics
* Excel import/export
* Cloud file storage
* Improved authentication and authorization
* Attendance management
* Performance charts and reports

---

## 👨‍💻 Developer

**Shubham Ramniwas Kushwaha**

B.Sc. Information Technology
Full Stack Developer | Python Developer | Cloud & Data Engineering Enthusiast

---

## ⭐ Project

If you find this project useful, consider giving the repository a ⭐ on GitHub.

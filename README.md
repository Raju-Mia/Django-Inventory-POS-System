# 🧩 Core App — Django Inventory & POS System

The **Core App** is the foundation of a modular Django-based inventory and sales management system.  
It provides user authentication, organizational management, and essential business modules such as Products, Sales, Purchases, Customers, and Suppliers.

---

## 🚀 Features

### 🔐 Authentication & Users
- Custom `CustomUser` model (email-based login)
- Role-based access control (`Admin`, `Manager`, `Staff`, `Operator`)
- User profile picture, phone, and organization linking
- OTP & Token-based verification for email/phone/password reset

### 🏢 Organization Management
- Each user belongs to an `Organization`
- Isolated data per organization (multi-tenant-like structure)

### 📦 Inventory & Sales
- Products linked to categories and organizations
- Suppliers, Customers, Purchases, and Sales modules
- Real-time stock tracking via `StockMovement`
- Automatic subtotal and reference tracking

### 🧾 POS / Billing System
- Invoice generation for each `Sale`
- Supports full, partial, and due payments
- Purchase & Sale line items tracked in detail

### 📬 Contact & Communication
- `ContactMessage` model for customer messages or support requests
- Easy management via Django Admin

---

## 🛠️ Tech Stack

| Component | Technology |
|------------|-------------|
| Framework | Django 5.x (or later) |
| Database | PostgreSQL / SQLite (dev) |
| Auth | Django CustomUser |
| Storage | Local / S3-compatible for media |
| Admin UI | Django Admin (customized) |

---

## 📁 Project Structure
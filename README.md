# 🛒 JoyCart – E-commerce Backend (FastAPI)

JoyCart is a backend-focused e-commerce application built using **FastAPI** and **SQLAlchemy** with real payment and refund handling via **Razorpay**.

This project focuses on **backend correctness**, **payment workflows**, and **real-world edge cases** rather than frontend polish.

---

## 🚀 Features

### 👤 Authentication
- JWT-based user authentication
- Role-based access (User / Seller)

### 🛍️ Products
- Seller product creation, editing, deletion
- Image uploads using Cloudinary
- Stock management

### 🛒 Orders & Checkout
- Cart → Checkout → Order flow
- Prevents duplicate order creation
- Order items tracked individually

### 💳 Payments (Razorpay)
- Online payments via Razorpay
- Secure webhook verification
- Payment confirmation handled asynchronously

### 🔄 Refund System (Important)
- Item-level cancellation
- Refund initiation via Razorpay API
- Refund status updated **only via webhooks**
- Supports partial refunds (per item)

---

## 🔁 Refund Flow (How It Works)

Refunds are **asynchronous** and handled in a production-safe way.

### 1️⃣ Cancel Item
- User or Seller cancels an order item
- Stock is restored
- Refund record is created with status `INITIATED`

### 2️⃣ Refund Initiation
- Backend calls Razorpay Refund API
- Razorpay returns a `gateway_refund_id`
- Refund remains `INITIATED`

### 3️⃣ Webhook Confirmation
- Razorpay sends `refund.processed` webhook
- Backend verifies signature
- Refund status updated to `REFUNDED`

> ⚠️ The system **never assumes** a refund is successful until the webhook confirms it.

---

## 🔐 Webhook Security

- All Razorpay webhooks are verified using HMAC SHA256
- Invalid signatures are ignored
- Prevents fake payment / refund confirmations

---

## 🧠 Important Backend Design Decisions

- **Database state is always committed before external API calls**
- External failures (Razorpay) do not corrupt DB state
- Refunds are idempotent and safe to retry
- UI reads payment/refund state **only from database**, never from assumptions

---

## 🧪 Local Development (Payments)

Razorpay webhooks require a **public URL**.

### Use ngrok:
```bash
ngrok http 8000

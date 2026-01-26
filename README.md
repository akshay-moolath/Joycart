# 🛒 JoyCart – Full‑Stack E‑commerce Backend (FastAPI)

JoyCart is a **production‑style e‑commerce backend** built using **FastAPI**, designed to demonstrate real‑world backend engineering practices such as authentication, role‑based access, order lifecycle management, payment & refund handling, seller workflows, and admin controls.

---

## 🚀 Live Deployment

**URL:** [https://joycart.onrender.com]

The application is deployed on Render and uses:

* PostgreSQL (production DB)
* Redis (caching)
* Razorpay (test mode) for online payments

---

## 🧠 Project Goals

* Build a **realistic e‑commerce backend**
* Practice **clean architecture** (routers vs services)
* Handle **payments and refunds safely**
* Implement **role‑based systems** (user, seller, admin)
* Learn **scalability & quality tooling** (Redis, pylint, static analysis)

---

## 🧩 Core Architecture

```
app/
├── routers/        # HTTP layer (FastAPI routes)
├── services/       # Business logic layer
├── models/         # SQLAlchemy ORM models
├── auth/           # Authentication & authorization
├── templates/      # Jinja2 templates (server-rendered UI)
├── static/         # CSS / JS
          
```

### Architectural Principles

* **Routers are thin** → only HTTP concerns
* **Services contain business logic** → reusable & testable
* **State transitions are explicit** (orders, payments, refunds)
* **No trust in frontend** → server always validates

---

## 👥 User Roles

### 👤 Normal User

* Register & login (JWT via HTTP‑only cookies)
* Browse products
* Manage cart
* Place orders (COD / Online)
* Track orders
* Cancel eligible items
* Write reviews (only after delivery)

### 🏪 Seller

* Register as seller
* Add / edit products
* Manage inventory
* View seller‑specific orders
* Confirm / ship orders
* Cancel orders (with correct refund logic)

### 🛡️ Admin

* View all users
* Block / unblock users
* Promote user to admin
* Access admin dashboard

---

## 🔐 Authentication & Security

* JWT‑based authentication
* Stored in **HTTP‑only cookies** (XSS safe)
* Role‑based dependency checks:

  * `get_current_user`
  * `get_current_seller`
  * `get_current_admin`
* Server‑side authorization for **every sensitive action**

---

## 🛍️ Product & Cart System

### Products

* Seller‑owned products
* SKU uniqueness per product
* Cannot delete product if it exists in any **active order**
* Stock validation at checkout time

### Cart

* One cart per user
* Add / update / remove items
* Quantity validation
* Cart total calculation on server
* Redis‑assisted caching for product listing

---

## 💳 Checkout & Payments

### Checkout Modes

* **Cart checkout**
* **Buy Now checkout**

### Payment Methods

* **Cash on Delivery (COD)**
* **Online Payment (Razorpay – Test Mode)**

### Payment Design Principles

* Amount always calculated on server
* Frontend never sends final price
* One checkout → one payment order
* Idempotent handling to avoid duplicates

---

## 🔄 Order Lifecycle

### Order Item Status Flow

```
PLACED → CONFIRMED → SHIPPED → DELIVERED
            ↘
           CANCELLED
```

* User can cancel before shipment
* Seller can cancel before shipment
* Stock is restored correctly on cancellation

### Order States

* FULL order & per‑item tracking
* Partial cancellations supported

---

## 💸 Refund System (Important Feature)

### Refund States

```
INITIATED → PROCESSING → REFUNDED / FAILED
```

### Refund Logic

* **COD orders** → no refund, payment marked `NOT_REQUIRED`
* **Online payments** → Razorpay refund API used
* Refunds created server‑side
* Razorpay **webhooks** used to finalize refund status
* Idempotency checks prevent duplicate refunds

This is one of the **strongest parts of the project** and mirrors real‑world e‑commerce behavior.

---

## 🔔 Razorpay Webhooks

Handled events:

* `payment.captured`
* `refund.processed`
* `refund.failed`

Webhook safety:

* HMAC signature verification
* Early rejection of invalid payloads
* Idempotent order/refund processing

---

## ⭐ Reviews System

* Only users with **DELIVERED orders** can review
* One review per user per product
* Rating validation (1–5)
* Average rating calculation
* Review timestamps handled safely

---

## ⚙️ Performance & Scalability Awareness

While not designed for massive scale, the project includes **scalability‑aware decisions**:

* Redis caching for product listings
* Avoidance of N+1 queries (joins used)
* Explicit DB transactions
* Background‑safe payment flows
* Stateless application design

---

## 🧪 Testing & Quality

### Manual & Integration Testing

* End‑to‑end testing of user, seller, admin flows
* Razorpay test mode used for payments & refunds
* Webhook testing via Razorpay dashboard

### Static Code Analysis

* **pylint score: 8.9+/10**
* Focused on fixing **real issues**, not cosmetic warnings
* Unsafe exception handling fixed
* Duplicate logic refactored

---

## 📦 Tech Stack

* **Backend:** FastAPI, Python
* **ORM:** SQLAlchemy
* **Database:** PostgreSQL,Sqlite
* **Cache:** Redis
* **Templates:** Jinja2
* **Payments:** Razorpay (Test Mode)
* **Auth:** JWT
* **Deployment:** Render

---

## 📈 What This Project Demonstrates

* Understanding of backend architecture
* Real payment & refund handling
* State‑driven design
* Secure authentication
* Role‑based systems
* Practical error handling
* Code quality awareness

This project was built to **learn and demonstrate backend engineering**, not just to "make it work".

---

## 🙌 Final Notes

JoyCart is an evolving project. Future improvements could include:

* Automated tests
* Async task queue for refunds
* Better admin analytics

**Built with focus, patience, and a lot of debugging.**

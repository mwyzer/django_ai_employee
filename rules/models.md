# 📐 Data Models

**App:** `orders` & `support`  
**ORM:** Django 6.0  
**Database:** MySQL 8.0  

---

## 1. Orders App Models

### 1.1 Product

Represents an AC product in the CoolBreeze catalog.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | `BigAutoField` | PK, auto | Primary key |
| `name` | `CharField(255)` | Required | Product name |
| `description` | `TextField` | Optional | Product description |
| `price` | `DecimalField(10,2)` | Required | Unit price |
| `category` | `CharField(100)` | Required | Product category |
| `in_stock` | `BooleanField` | Default: `True` | Stock availability |

```python
class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=100)
    in_stock = models.BooleanField(default=True)
```

---

### 1.2 Order

Represents a customer's order.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | `BigAutoField` | PK, auto | Primary key |
| `user` | `FK → User` | Required, CASCADE | Customer who placed the order |
| `product` | `FK → Product` | Optional, SET_NULL | Referenced product |
| `product_name` | `CharField(255)` | Required | Denormalized product name |
| `amount` | `DecimalField(10,2)` | Required | Order total |
| `status` | `CharField(20)` | Choices | `pending` / `dispatched` / `delivered` / `cancelled` |
| `carrier` | `CharField(100)` | Optional | Shipping carrier name |
| `tracking_number` | `CharField(100)` | Optional | Carrier tracking number |
| `delivery` | `TextField` | Optional | Delivery address notes |
| `created_at` | `DateTimeField` | Required | Order creation timestamp |
| `updated_at` | `DateTimeField` | Auto, nullable | Last update timestamp |

```python
class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("dispatched", "Dispatched"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, related_name="orders")
    product_name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    carrier = models.CharField(max_length=100, blank=True)
    tracking_number = models.CharField(max_length=100, blank=True)
    delivery = models.TextField(blank=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField(auto_now=True, null=True)
```

---

### 1.3 RefundRequest

Represents a refund request linked to an order.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | `BigAutoField` | PK, auto | Primary key |
| `order` | `FK → Order` | Required, CASCADE | The order being refunded |
| `user` | `FK → User` | Required, CASCADE | Customer requesting refund |
| `reason` | `TextField` | Required | Refund reason text |
| `status` | `CharField(20)` | Choices | `pending` / `approved` / `denied` |
| `created_at` | `DateTimeField` | Required | When the refund was requested |

```python
class RefundRequest(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("denied", "Denied"),
    ]
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="refund_requests")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="refund_requests")
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField()
```

---

## 2. Support App Models

### 2.1 Conversation

Represents a chat session between a user and the AI agents for a specific order.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | `BigAutoField` | PK, auto | Primary key |
| `user` | `FK → User` | Required, CASCADE | Customer in the conversation |
| `order` | `FK → Order` | Required, CASCADE | Order being discussed |
| `created_at` | `DateTimeField` | Auto | When conversation started |

**Computed Properties:**

| Property | Returns | Description |
|----------|---------|-------------|
| `manager_involved` | `bool` | `True` if any AgentLog has `event_type="manager"` |
| `risk_assessed` | `bool` | `True` if any AgentLog has `event_type="risk"` |

```python
class Conversation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="conversations")
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="conversations")
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def manager_involved(self):
        return self.agentlogs.filter(event_type="manager").exists()

    @property
    def risk_assessed(self):
        return self.agentlogs.filter(event_type="risk").exists()
```

---

### 2.2 Message

Individual chat messages within a conversation.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | `BigAutoField` | PK, auto | Primary key |
| `conversation` | `FK → Conversation` | Required, CASCADE | Parent conversation |
| `role` | `CharField(20)` | Choices | `user` or `assistant` |
| `content` | `TextField` | Required | Message text |
| `created_at` | `DateTimeField` | Auto | When message was sent |

```python
class Message(models.Model):
    ROLE_CHOICES = [
        ("user", "User"),
        ("assistant", "Assistant"),
    ]
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
```

---

### 2.3 AgentLog

Records every agent action, tool call, and decision for real-time SSE streaming and audit trail.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | `BigAutoField` | PK, auto | Primary key |
| `conversation` | `FK → Conversation` | Required, CASCADE | Parent conversation |
| `event_type` | `CharField(20)` | Choices | Event category |
| `message` | `TextField` | Required | Event details / log text |
| `created_at` | `DateTimeField` | Auto | When event occurred |

**Event Types:**

| Value | Label | Emitted When |
|-------|-------|-------------|
| `support` | Support Agent | Maya processes a message or replies |
| `tool_call` | Tool Call | An agent invokes a tool |
| `tool_result` | Tool Result | A tool returns its result |
| `manager` | Manager Agent | Manager agent is invoked (escalation) |
| `risk` | Risk Agent | Risk analyst evaluates fraud |
| `final` | Final Reply | Conversation is resolved |

```python
class AgentLog(models.Model):
    EVENT_CHOICES = [
        ("support", "Support Agent"),
        ("tool_call", "Tool Call"),
        ("tool_result", "Tool Result"),
        ("manager", "Manager Agent"),
        ("risk", "Risk Agent"),
        ("final", "Final Reply"),
    ]
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="agentlogs")
    event_type = models.CharField(max_length=20, choices=EVENT_CHOICES)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
```

---

## 3. Django Built-in Model: User

Uses Django's `django.contrib.auth.models.User`:

| Field | Description |
|-------|-------------|
| `username` | Login username |
| `password` | Hashed password |
| `email` | Email address |
| `first_name` | First name (used for greeting) |
| `last_name` | Last name |
| `is_staff` | Staff dashboard access (`True` for admin) |
| `is_superuser` | Full admin panel access |

---

## 4. Model Relationships Summary

```
User ──1:N──▶ Order ──1:N──▶ RefundRequest
  │               │
  │               │
  └──1:N──▶ Conversation ──1:N──▶ Message
                  │
                  └──1:N──▶ AgentLog
```

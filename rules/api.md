# 🔌 API Endpoints

**Base URL (dev):** `http://127.0.0.1:8000`  
**Base URL (prod):** `https://djangoaiemployees-production.up.railway.app`  
**Auth:** Django session-based (login required for most endpoints)  

---

## 1. Authentication Endpoints

### `GET /login/`

| Property | Value |
|----------|-------|
| **Auth** | Public |
| **Description** | Render login page |
| **Template** | `templates/login.html` |
| **Success** | HTML page with login form |

### `POST /login/`

| Property | Value |
|----------|-------|
| **Auth** | Public |
| **Description** | Authenticate user |
| **Body** | `username`, `password` (form-encoded) |
| **Success** | 302 → redirect to `/orders/` |
| **Failure** | 200 → login page with error |

### `GET /logout/`

| Property | Value |
|----------|-------|
| **Auth** | Login required |
| **Description** | Log out current user |
| **Success** | 302 → redirect to `/login/` |

---

## 2. Orders Endpoints

Base path: `/orders/` (included from `orders.urls`)

### `GET /orders/`

| Property | Value |
|----------|-------|
| **Auth** | Login required |
| **Description** | List current user's orders |
| **View** | `orders.views.orders_list` |
| **Template** | `templates/orders_list.html` |
| **Context** | `orders` — queryset of `Order` filtered by `request.user` |
| **Response** | HTML page |

### `GET /orders/<order_id>/`

| Property | Value |
|----------|-------|
| **Auth** | Login required |
| **Description** | Order detail page with AI chat interface |
| **View** | `orders.views.order_detail` |
| **Template** | `templates/order_detail.html` |
| **URL Param** | `order_id` — `int`, must belong to `request.user` |
| **Context** | `order`, `refunds`, `conversation`, `previous_messages` |
| **Response** | HTML page |
| **404** | If order not found or doesn't belong to user |

---

## 3. Support / Chat Endpoints

Base path: `/support/` (included from `support.urls`)

### `POST /support/chat/<order_id>/`

| Property | Value |
|----------|-------|
| **Auth** | Login required |
| **Description** | Send a message to the AI support agent |
| **View** | `support.views.chat` |
| **Body (JSON)** | `{ "message": "Where is my order?" }` |
| **Processing** | 1. Validate message is non-empty<br>2. Get/create `Conversation` for user+order<br>3. Persist user `Message`<br>4. Publish event to SSE queue<br>5. Invoke LangChain agent (`run_support_agent_langchain`)<br>6. Persist assistant `Message`<br>7. Return reply |

**Request Example:**
```json
{
    "message": "I want to request a refund for this order"
}
```

**Success Response (200):**
```json
{
    "reply": "I understand you'd like to request a refund. Let me check your order details first..."
}
```

**Error Response (400):**
```json
{
    "error": "Empty message"
}
```

**Error Response (404):**
```json
{
    "detail": "No Order matches the given query."
}
```

---

### `GET /support/dashboard/`

| Property | Value |
|----------|-------|
| **Auth** | Staff only (`@staff_member_required`) |
| **Description** | Staff dashboard — list all conversations |
| **View** | `support.views.dashboard` |
| **Template** | `templates/support/dashboard.html` |
| **Context** | `conversations` — all `Conversation` objects, newest first |
| **Response** | HTML page |

---

### `GET /support/dashboard/<conversation_id>/`

| Property | Value |
|----------|-------|
| **Auth** | Staff only (`@staff_member_required`) |
| **Description** | View a specific conversation's messages + agent logs |
| **View** | `support.views.conversation_detail` |
| **Template** | `templates/support/conversation_detail.html` |
| **URL Param** | `conversation_id` — `int` |
| **Context** | `conversation`, `messages` (ordered by `created_at`), `agentlogs` (ordered by `created_at`) |
| **Response** | HTML page |
| **404** | If conversation not found |

---

### `GET /support/dashboard/stream/<conversation_id>/`

| Property | Value |
|----------|-------|
| **Auth** | Public (`@staff_member_required` decorator is **commented out** in source) |
| **Description** | Server-Sent Events (SSE) real-time stream of agent activity |
| **View** | `support.views.conversation_stream` |
| **Content-Type** | `text/event-stream` |
| **Headers** | `Cache-Control: no-cache`, `X-Accel-Buffering: no` |
| **URL Param** | `conversation_id` — `int` |

**How It Works:**
1. Subscribes to the in-memory `queue.Queue` for this conversation
2. Blocks until events are published by `support/chat/`
3. Streams each event as SSE `data:` line
4. Unsubscribes on disconnect (finally block)

**SSE Event Format:**
```
data: {"type": "user_message", "message": "Where is my order?", "name": "Rathan"}

data: {"type": "tool_call", "tool": "get_order_details", "args": {...}}

data: {"type": "tool_result", "tool": "get_order_details", "result": {...}}

data: {"type": "support", "message": "Your order was dispatched on..."}

data: {"type": "final", "message": "Is there anything else I can help with?"}
```

---

## 4. Django Admin

### `GET /admin/`

| Property | Value |
|----------|-------|
| **Auth** | Superuser only |
| **Description** | Django admin panel |
| **Managed Models** | `User`, `Product`, `Order`, `RefundRequest`, `Conversation`, `Message`, `AgentLog` |
| **Response** | HTML (Django admin interface) |

---

## 5. Endpoint Summary

```
/login/                          GET    Public          Login page
/login/                          POST   Public          Authenticate
/logout/                         GET    Login           Log out
/orders/                         GET    Login           User's order list
/orders/<order_id>/              GET    Login           Order detail + AI chat
/support/chat/<order_id>/        POST   Login           Send message to AI agent
/support/dashboard/              GET    Staff           All conversations
/support/dashboard/<conv_id>/    GET    Staff           Conversation detail
/support/dashboard/stream/<cid>/ GET    Public (*)      SSE real-time stream
/admin/                          GET    Superuser       Django admin panel
```

> \* The SSE stream endpoint has `@staff_member_required` commented out in the source code, making it effectively public.

---

## 6. Authentication Model

- **Session-based auth** using Django's built-in `AuthenticationMiddleware`
- All customer-facing endpoints require `@login_required`
- Staff endpoints require `@staff_member_required` (with the SSE exception noted above)
- `LOGIN_URL = '/login/'` — unauthenticated users are redirected here
- `LOGIN_REDIRECT_URL = '/orders/'` — post-login destination
- `LOGOUT_REDIRECT_URL = '/login/'` — post-logout destination

---

## 7. URL Configuration Sources

```python
# dj_ai_employee_main/urls.py (root URLconf)
urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name="login.html"), name="login"),
    path('logout/', auth_views.LogoutView.as_view(), name="logout"),
    path('orders/', include('orders.urls')),
    path('support/', include('support.urls')),
]

# orders/urls.py
urlpatterns = [
    path('', views.orders_list, name='orders_list'),
    path('<int:order_id>/', views.order_detail, name='order_detail'),
]

# support/urls.py
urlpatterns = [
    path('chat/<int:order_id>/', views.chat, name="chat"),
    path('dashboard/', views.dashboard, name="dashboard"),
    path('dashboard/<int:conversation_id>/', views.conversation_detail, name="conversation_detail"),
    path('dashboard/stream/<int:conversation_id>/', views.conversation_stream, name="conversation_stream"),
]
```

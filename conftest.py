"""Shared fixtures for all test files."""
import pytest
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from orders.models import Product, Order, RefundRequest
from support.models import Conversation, Message, AgentLog


@pytest.fixture
def user(db):
    """Create a test user with orders and refunds."""
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
        first_name='Test'
    )
    return user


@pytest.fixture
def staff_user(db):
    """Create a staff user for dashboard access."""
    return User.objects.create_user(
        username='staffuser',
        email='staff@example.com',
        password='staffpass123',
        is_staff=True,
        first_name='Staff'
    )


@pytest.fixture
def product(db):
    """Create a test product."""
    return Product.objects.create(
        name='Test AC Unit',
        description='A test air conditioner',
        price=29999.00,
        category='Split AC',
        in_stock=True
    )


@pytest.fixture
def order(db, user, product):
    """Create a test order."""
    return Order.objects.create(
        user=user,
        product=product,
        product_name='Test AC Unit',
        amount=29999.00,
        status='dispatched',
        carrier='BlueDart',
        tracking_number='BD99281733',
        delivery='123 Test Street, Test City',
        created_at=timezone.now() - timedelta(days=10)
    )


@pytest.fixture
def order_pending(db, user, product):
    """Create a pending order."""
    return Order.objects.create(
        user=user,
        product=product,
        product_name='Test AC Unit',
        amount=29999.00,
        status='pending',
        carrier='',
        tracking_number='',
        delivery='123 Test Street, Test City',
        created_at=timezone.now() - timedelta(days=2)
    )


@pytest.fixture
def refund_request(db, user, order):
    """Create a test refund request."""
    return RefundRequest.objects.create(
        order=order,
        user=user,
        reason='Product damaged on arrival',
        status='pending',
        created_at=timezone.now() - timedelta(days=2)
    )


@pytest.fixture
def conversation(db, user, order):
    """Create a test conversation."""
    return Conversation.objects.create(
        user=user,
        order=order
    )


@pytest.fixture
def conversation_with_messages(db, user, order):
    """Create a conversation with messages."""
    conv = Conversation.objects.create(user=user, order=order)
    Message.objects.create(conversation=conv, role='user', content='Where is my order?')
    Message.objects.create(conversation=conv, role='assistant', content='Let me check that for you.')
    return conv

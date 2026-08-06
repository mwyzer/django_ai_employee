"""Shared fixtures for all test files."""
import json
import pytest
from unittest.mock import MagicMock
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


@pytest.fixture
def make_completion():
    """Factory for a fake OpenAI ChatCompletion: make_completion(content=...) for a final
    turn, or make_completion(tool_calls=[(name, args_dict), ...]) for a tool-call turn."""
    def _make(content=None, tool_calls=None, finish_reason='stop'):
        message = MagicMock()
        message.content = content
        if tool_calls:
            calls = []
            for i, (name, args) in enumerate(tool_calls):
                tc = MagicMock()
                tc.id = f'call_{i}'
                tc.function.name = name
                tc.function.arguments = json.dumps(args)
                calls.append(tc)
            message.tool_calls = calls
        else:
            message.tool_calls = None
        response = MagicMock()
        response.choices = [MagicMock(message=message, finish_reason=finish_reason)]
        return response
    return _make

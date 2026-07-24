"""Unit tests for models — Product, Order, RefundRequest, Conversation, Message, AgentLog."""
import pytest
from django.utils import timezone

from orders.models import Product, Order, RefundRequest
from support.models import Conversation, Message, AgentLog


@pytest.mark.unit
class TestProductModel:

    def test_create_product(self, db):
        product = Product.objects.create(
            name='CoolBreeze 3000', description='Premium AC',
            price=45999.00, category='Split AC', in_stock=True
        )
        assert str(product) == 'CoolBreeze 3000'
        assert product.in_stock is True

    def test_default_in_stock(self, db):
        product = Product.objects.create(
            name='Test', price=1000.00, category='Accessories'
        )
        assert product.in_stock is True


@pytest.mark.unit
class TestOrderModel:

    def test_create_order(self, user, product):
        order = Order.objects.create(
            user=user, product=product,
            product_name='CoolBreeze 3000', amount=45999.00,
            status='dispatched', carrier='BlueDart',
            tracking_number='BD001', delivery='123 Main St',
            created_at=timezone.now()
        )
        assert str(order) == f'Order #{order.id} - CoolBreeze 3000 (dispatched)'

    def test_default_status_pending(self, user, product):
        order = Order.objects.create(
            user=user, product=product,
            product_name='Test', amount=100.00,
            created_at=timezone.now()
        )
        assert order.status == 'pending'

    def test_related_to_user(self, user, order):
        assert order in user.orders.all()


@pytest.mark.unit
class TestRefundRequestModel:

    def test_create_refund(self, user, order):
        refund = RefundRequest.objects.create(
            order=order, user=user,
            reason='Damaged', created_at=timezone.now()
        )
        assert str(refund) == f'Refund for Order #{order.id} - pending'

    def test_via_relations(self, user, order):
        refund = RefundRequest.objects.create(
            order=order, user=user,
            reason='Test', created_at=timezone.now()
        )
        assert refund in order.refund_requests.all()
        assert refund in user.refund_requests.all()


@pytest.mark.unit
class TestConversationModel:

    def test_create(self, user, order):
        conv = Conversation.objects.create(user=user, order=order)
        assert str(conv) == f'Conversation #{conv.id} - testuser / Order #{order.id}'

    def test_manager_involved_false(self, user, order):
        conv = Conversation.objects.create(user=user, order=order)
        assert conv.manager_involved is False

    def test_manager_involved_true(self, user, order):
        conv = Conversation.objects.create(user=user, order=order)
        AgentLog.objects.create(conversation=conv, event_type='manager', message='Review')
        assert conv.manager_involved is True

    def test_risk_assessed(self, user, order):
        conv = Conversation.objects.create(user=user, order=order)
        assert conv.risk_assessed is False
        AgentLog.objects.create(conversation=conv, event_type='risk', message='Check')
        assert conv.risk_assessed is True


@pytest.mark.unit
class TestMessageModel:

    def test_create_and_str(self, user, order):
        conv = Conversation.objects.create(user=user, order=order)
        msg = Message.objects.create(conversation=conv, role='user', content='Hello')
        assert str(msg) == 'user: Hello'

    def test_truncation(self, user, order):
        conv = Conversation.objects.create(user=user, order=order)
        msg = Message.objects.create(
            conversation=conv, role='assistant', content='A' * 100
        )
        # "assistant: " (11 chars) + 50 chars content = 61 chars max
        assert len(str(msg)) <= 65

    def test_ordering(self, user, order):
        conv = Conversation.objects.create(user=user, order=order)
        m1 = Message.objects.create(conversation=conv, role='user', content='A')
        m2 = Message.objects.create(conversation=conv, role='assistant', content='B')
        assert list(conv.messages.order_by('created_at')) == [m1, m2]


@pytest.mark.unit
class TestAgentLogModel:

    def test_create(self, user, order):
        conv = Conversation.objects.create(user=user, order=order)
        log = AgentLog.objects.create(
            conversation=conv, event_type='support', message='Processing'
        )
        assert str(log) == '[support] - Processing'

    def test_all_event_types(self, user, order):
        conv = Conversation.objects.create(user=user, order=order)
        for et in ['support', 'tool_call', 'tool_result', 'manager', 'risk', 'final']:
            log = AgentLog.objects.create(conversation=conv, event_type=et, message='X')
            assert log.event_type == et

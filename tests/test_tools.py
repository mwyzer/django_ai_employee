"""Unit tests for support/tools.py — all tool functions in isolation."""
import pytest
from unittest.mock import patch
from datetime import timedelta
from django.utils import timezone

from support.tools import (
    get_order_details,
    get_refund_history,
    check_delivery_status,
    get_customer_risk_profile,
    search_knowledge_base,
)
from orders.models import RefundRequest


@pytest.mark.unit
class TestGetOrderDetails:

    def test_returns_full_order(self, order):
        """Should return complete order dict with all fields."""
        result = get_order_details(order.id)

        assert result['order_id'] == order.id
        assert result['product_name'] == 'Test AC Unit'
        assert result['amount'] == '29999.00'
        assert result['status'] == 'dispatched'
        assert result['carrier'] == 'BlueDart'
        assert result['tracking_number'] == 'BD99281733'
        assert 'ordered_on' in result
        assert isinstance(result['days_since_order'], int)

    def test_order_not_found(self, db):
        """Should return error dict when order doesn't exist."""
        result = get_order_details(99999)
        assert 'error' in result
        assert '99999' in result['error']


@pytest.mark.unit
class TestGetRefundHistory:

    def test_empty_history(self, user):
        """Should return empty history for user with no refunds."""
        result = get_refund_history(user.id)
        assert result['total_refund_requests'] == 0
        assert result['history'] == []

    def test_with_refunds(self, user, order):
        """Should return refund history with correct structure."""
        RefundRequest.objects.create(
            order=order, user=user,
            reason='Damaged', status='approved',
            created_at=timezone.now()
        )
        result = get_refund_history(user.id)
        assert result['total_refund_requests'] == 1
        assert result['history'][0]['order_id'] == order.id
        assert result['history'][0]['status'] == 'approved'


@pytest.mark.unit
class TestCheckDeliveryStatus:

    def test_known_tracking_number(self):
        """Should return delivery data for known tracking number."""
        result = check_delivery_status('BD99281733', 'BlueDart')
        assert result['tracking_number'] == 'BD99281733'
        assert result['status'] == 'In Transit'

    def test_unknown_tracking_number(self):
        """Should return default response for unknown tracking."""
        result = check_delivery_status('ZZZZZZZZZZ', 'UnknownCarrier')
        assert result['status'] == 'Unknown'

    def test_delivered_status(self):
        """Should return delivered status."""
        result = check_delivery_status('DL44729103', 'Delhivery')
        assert result['status'] == 'Delivered'


@pytest.mark.unit
class TestGetCustomerRiskProfile:

    def test_no_orders_no_refunds(self, user):
        """Should return zeroed profile."""
        result = get_customer_risk_profile(user.id)
        assert result['total_orders'] == 0
        assert result['refund_to_order_ratio'] == 0

    def test_ratio_calculation(self, user, order):
        """Should calculate correct refund-to-order ratio."""
        RefundRequest.objects.create(
            order=order, user=user,
            reason='A', status='approved',
            created_at=timezone.now()
        )
        RefundRequest.objects.create(
            order=order, user=user,
            reason='B', status='denied',
            created_at=timezone.now()
        )
        result = get_customer_risk_profile(user.id)
        assert result['total_orders'] == 1
        assert result['total_refund_requests'] == 2
        assert result['refund_to_order_ratio'] == 2.0

    def test_recent_90_days_filter(self, user, order):
        """Should only count refunds from last 90 days."""
        RefundRequest.objects.create(
            order=order, user=user,
            reason='Old', status='approved',
            created_at=timezone.now() - timedelta(days=100)
        )
        RefundRequest.objects.create(
            order=order, user=user,
            reason='Recent', status='pending',
            created_at=timezone.now() - timedelta(days=10)
        )
        result = get_customer_risk_profile(user.id)
        assert result['total_refund_requests'] == 2
        assert result['refunds_last_90_days'] == 1


@pytest.mark.unit
class TestSearchKnowledgeBase:

    @patch('support.tools.rag_search')
    def test_returns_result_wrapper(self, mock_rag):
        """Should wrap RAG result in dict."""
        mock_rag.return_value = 'Refund policy: 30-day return window.'
        result = search_knowledge_base('what is refund policy?')
        assert result == {'result': 'Refund policy: 30-day return window.'}
        mock_rag.assert_called_once_with('what is refund policy?')

"""Unit tests for support/event_queue.py — pub/sub in isolation."""
import pytest
import queue as qmod

from support.event_queue import subscribe, unsubscribe, publish, DONE, subscribers


@pytest.mark.unit
class TestEventQueueIntegration:

    def test_subscribe_unsubscribe(self):
        """Should register and deregister queues."""
        q = subscribe(42)
        assert 42 in subscribers
        assert q in subscribers[42]

        unsubscribe(42, q)
        assert 42 not in subscribers

    def test_multiple_subscribers(self):
        """Should support multiple queues per conversation."""
        q1 = subscribe(99)
        q2 = subscribe(99)
        assert len(subscribers[99]) == 2

    def test_publish_delivers(self):
        """Should deliver event to subscriber queue."""
        q = subscribe(10)
        publish(10, {'type': 'user_message', 'message': 'hello'})
        assert q.get(timeout=1) == {'type': 'user_message', 'message': 'hello'}

    def test_publish_to_all(self):
        """Should deliver to all queues for same conversation."""
        q1 = subscribe(11)
        q2 = subscribe(11)
        publish(11, {'type': 'test'})
        assert q1.get(timeout=1)['type'] == 'test'
        assert q2.get(timeout=1)['type'] == 'test'

    def test_publish_no_subscribers_no_error(self):
        """Should not raise when no subscribers."""
        publish(99999, {'type': 'test'})

    def test_isolated_conversations(self):
        """Events should not leak between conversations."""
        q_a = subscribe(100)
        q_b = subscribe(200)
        publish(100, {'type': 'only_for_100'})
        assert q_a.get(timeout=1)['type'] == 'only_for_100'
        assert q_b.empty()

    def test_done_sentinel(self):
        """DONE should be {'type': 'done'}."""
        assert DONE == {'type': 'done'}

    def test_removes_empty_key(self):
        """Should delete key when last queue unsubscribes."""
        q = subscribe(9)
        unsubscribe(9, q)
        assert 9 not in subscribers

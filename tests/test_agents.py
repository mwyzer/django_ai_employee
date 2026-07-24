"""Unit tests for agent loop logic — mocked DeepSeek API calls."""
import json
import pytest
from unittest.mock import patch, MagicMock

from support.agents import (
    execute_tool,
    SUPPORT_SYSTEM_PROMPT,
    MANAGER_SYSTEM_PROMPT,
    RISK_SYSTEM_PROMPT,
)


@pytest.mark.unit
class TestExecuteTool:

    def test_get_order_details(self, order):
        """execute_tool should route to get_order_details."""
        result = execute_tool('get_order_details', {'order_id': order.id})
        assert result['order_id'] == order.id
        assert result['product_name'] == 'Test AC Unit'

    def test_get_order_details_not_found(self, db):
        """Should return error for non-existent order."""
        result = execute_tool('get_order_details', {'order_id': 99999})
        assert 'error' in result

    def test_get_refund_history(self, user):
        """execute_tool should route to get_refund_history."""
        result = execute_tool('get_refund_history', {'user_id': user.id})
        assert result['total_refund_requests'] == 0

    def test_check_delivery_status(self):
        """execute_tool should route to check_delivery_status."""
        result = execute_tool(
            'check_delivery_status',
            {'tracking_number': 'BD99281733', 'carrier': 'BlueDart'}
        )
        assert result['status'] == 'In Transit'

    def test_get_customer_risk_profile(self, user):
        """execute_tool should route to get_customer_risk_profile."""
        result = execute_tool('get_customer_risk_profile', {'user_id': user.id})
        assert result['user_id'] == user.id

    @patch('support.tools.rag_search')
    def test_search_knowledge_base(self, mock_rag):
        """execute_tool should route to search_knowledge_base."""
        mock_rag.return_value = 'Some policy text'
        result = execute_tool('search_knowledge_base', {'query': 'refund policy'})
        assert result == {'result': 'Some policy text'}


@pytest.mark.unit
class TestAgentSystemPrompts:

    def test_support_prompt_contains_maya(self):
        """Support prompt should mention Maya."""
        assert 'Maya' in SUPPORT_SYSTEM_PROMPT
        assert 'CoolBreeze AC' in SUPPORT_SYSTEM_PROMPT

    def test_support_prompt_tool_instructions(self):
        """Support prompt should instruct to use tools."""
        assert 'tools' in SUPPORT_SYSTEM_PROMPT.lower()

    def test_manager_prompt_has_decision_options(self):
        """Manager prompt should list decision options."""
        assert 'Approve refund' in MANAGER_SYSTEM_PROMPT
        assert 'Deny refund' in MANAGER_SYSTEM_PROMPT
        assert 'Escalate to risk' in MANAGER_SYSTEM_PROMPT

    def test_risk_prompt_has_levels(self):
        """Risk prompt should define risk levels."""
        assert 'LOW' in RISK_SYSTEM_PROMPT
        assert 'MEDIUM' in RISK_SYSTEM_PROMPT
        assert 'HIGH' in RISK_SYSTEM_PROMPT


@pytest.mark.unit
class TestToolDefinitions:

    def test_support_tools_have_all_five(self, settings):
        """Support agent should have 5 tools defined."""
        settings.DEEPSEEK_API_KEY = 'test'
        settings.DEEPSEEK_MODEL = 'deepseek-chat'

        from support.agents import SUPPORT_TOOLS
        tool_names = [t['function']['name'] for t in SUPPORT_TOOLS]
        assert 'get_order_details' in tool_names
        assert 'get_refund_history' in tool_names
        assert 'check_delivery_status' in tool_names
        assert 'escalate_to_manager' in tool_names
        assert 'search_knowledge_base' in tool_names

    def test_manager_tools(self, settings):
        """Manager agent should have assess_fraud_risk tool."""
        settings.DEEPSEEK_API_KEY = 'test'
        settings.DEEPSEEK_MODEL = 'deepseek-chat'

        from support.agents import MANAGER_TOOLS
        tool_names = [t['function']['name'] for t in MANAGER_TOOLS]
        assert 'assess_fraud_risk' in tool_names

    def test_risk_tools(self, settings):
        """Risk agent should have get_customer_risk_profile tool."""
        settings.DEEPSEEK_API_KEY = 'test'
        settings.DEEPSEEK_MODEL = 'deepseek-chat'

        from support.agents import RISK_TOOLS
        tool_names = [t['function']['name'] for t in RISK_TOOLS]
        assert 'get_customer_risk_profile' in tool_names

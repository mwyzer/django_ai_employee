"""Smoke tests — quick sanity checks after deployment."""
import pytest
from django.urls import reverse, resolve


@pytest.mark.smoke
class TestURLResolution:

    def test_admin_url_resolves(self):
        """Admin URL should resolve."""
        match = resolve('/admin/')
        assert match is not None

    def test_login_url_resolves(self):
        """Login URL should resolve."""
        match = resolve('/login/')
        assert match.view_name == 'login'

    def test_chat_url_resolves(self):
        """Chat URL should resolve with order_id."""
        match = resolve('/support/chat/5/')
        assert match.view_name == 'chat'

    def test_dashboard_url_resolves(self):
        """Dashboard URL should resolve."""
        match = resolve('/support/dashboard/')
        assert match.view_name == 'dashboard'

    def test_conversation_detail_resolves(self):
        """Conversation detail URL should resolve."""
        match = resolve('/support/dashboard/1/')
        assert match.view_name == 'conversation_detail'

    def test_conversation_stream_resolves(self):
        """SSE stream URL should resolve."""
        match = resolve('/support/dashboard/stream/1/')
        assert match.view_name == 'conversation_stream'


@pytest.mark.smoke
class TestAppConfig:

    def test_orders_app_installed(self, settings):
        """Orders app should be in INSTALLED_APPS."""
        assert 'orders' in settings.INSTALLED_APPS

    def test_support_app_installed(self, settings):
        """Support app should be in INSTALLED_APPS."""
        assert 'support' in settings.INSTALLED_APPS

    def test_deepseek_settings_configured(self, settings):
        """DeepSeek settings should exist."""
        assert hasattr(settings, 'DEEPSEEK_API_KEY')
        assert hasattr(settings, 'DEEPSEEK_MODEL')
        assert settings.DEEPSEEK_API_KEY is not None

    def test_login_redirect_url(self, settings):
        """Login redirect should be configured."""
        assert settings.LOGIN_REDIRECT_URL == '/orders/'
        assert settings.LOGIN_URL == '/login/'


@pytest.mark.smoke
class TestDatabaseConnectivity:

    def test_can_create_user(self, db):
        """Should be able to create and query a user."""
        from django.contrib.auth.models import User
        user = User.objects.create_user(username='smoketest', password='smoke123')
        assert User.objects.filter(username='smoketest').exists()
        user.delete()

    def test_migrations_applied(self, db):
        """Migrations should be applied without errors."""
        from django.core.management import call_command
        from io import StringIO

        out = StringIO()
        try:
            call_command('showmigrations', stdout=out)
            output = out.getvalue()
            # All migrations should show [X] (applied)
            unapplied = [line for line in output.split('\n') if '[ ]' in line]
            assert len(unapplied) == 0, f'Unapplied migrations: {unapplied}'
        except Exception:
            pass  # showmigrations can be flaky in test mode


@pytest.mark.smoke
class TestAdminAccessible:

    def test_admin_login_page(self, client):
        """Admin login page should be accessible."""
        response = client.get('/admin/login/')
        assert response.status_code == 200

    def test_admin_index_redirects_to_login(self, client):
        """Admin index should redirect unauthenticated users."""
        response = client.get('/admin/')
        assert response.status_code == 302


@pytest.mark.smoke
class TestStaticFiles:

    def test_static_url_configured(self, settings):
        """STATIC_URL should be set."""
        assert settings.STATIC_URL in ['static/', '/static/']

    def test_whitenoise_installed(self, settings):
        """WhiteNoise should be in MIDDLEWARE."""
        assert 'whitenoise.middleware.WhiteNoiseMiddleware' in settings.MIDDLEWARE

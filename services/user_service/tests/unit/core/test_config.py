from app.core.config import settings

def test_test_database_url_is_set():

	'''TEST_DATABASE_URL should be set in test settings.'''

	assert hasattr(settings, "TEST_DATABASE_URL"), "TEST_DATABASE_URL must be set for tests"
	assert isinstance(settings.TEST_DATABASE_URL, str) and settings.TEST_DATABASE_URL


def test_basic_service_settings():

	'''Basic service settings should be populated.'''

	assert getattr(settings, "SERVICE_NAME", None), "SERVICE_NAME must be set"
	assert getattr(settings, "SERVICE_VERSION", None), "SERVICE_VERSION must be set"
	assert getattr(settings, "route_prefix", None), "route_prefix must be set"
	assert getattr(settings, "JWT_SECRET_KEY", None), "JWT_SECRET_KEY must be set"
	assert getattr(settings, "JWT_ALGORITHM", None), "JWT_ALGORITHM must be set"
	assert getattr(settings, "REFRESH_TOKEN_SECRET", None), "REFRESH_TOKEN_SECRET must be set"
	
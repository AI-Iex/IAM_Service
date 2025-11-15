import json
import logging
from uuid import UUID, uuid4
from app.core.logging_config import (
	setup_logging,
	set_request_context,
	reset_request_context,
)
from app.core.config import settings

def _emit_and_capture_log(capsys, privacy_level: str):

	'''Helper function to emit a log with a given privacy level and capture the output.'''

	# Configure logging for tests with explicit privacy level
	logger = setup_logging(service_name="test_service", level=logging.INFO, privacy_level=privacy_level)

	# Set a request context with a user id (UUID) and request id
	req_id = "req-abc-123"
	user_id = uuid4()
	req_token, user_token = set_request_context(req_id, user_id)

	# Log a message with extras that should be masked: email and a uuid-like token
	extra = {
		"email": "alice@example.com",
		"token": "123e4567-e89b-12d3-a456-426614174000",
	}

	logger.info("User login", extra=extra)

	# Reset context to avoid leaking state into other tests
	reset_request_context(req_token, user_token)

	# Capture stdout where the JSONFormatter writes
	out = capsys.readouterr().out.strip()
	assert out, "Expected logging output on stdout"

	# The formatter emits a single JSON object per log line
	payload = json.loads(out)

	# Basic fields
	assert payload["level"] == "INFO"
	assert payload["message"] == "User login"

	# Context fields injected by the RequestIdFilter
	assert payload.get("extra") is not None
	extras = payload["extra"]
	assert extras.get("request_id") == req_id

	# user id should be present as request_by_user_id in extras
	assert "request_by_user_id" in extras

	return extras, extra


def test_logging_masking_across_privacy_levels(capsys):

	'''Test that sensitive fields are masked according to privacy level settings.'''
	
	levels = ["none", "standard", "strict"]

	for lvl in levels:
		extras, original = _emit_and_capture_log(capsys, lvl)

		# Email masking: only 'none' leaves the email untouched
		if lvl == "none":
			assert extras.get("email") == original["email"]
		else:
			assert extras.get("email") != original["email"]
			assert "@" in extras.get("email")

		# Token masking: only strict truncates UUID-like tokens
		token_val = extras.get("token")
		if lvl == "strict":
			assert token_val.endswith("..."), f"Token should be truncated in strict mode; got {token_val}"
		else:
			assert token_val == original["token"], f"Token should be unmodified in {lvl} mode"
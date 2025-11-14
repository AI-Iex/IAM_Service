from app.core import exceptions

def test_exception_classes_have_status_codes_and_messages():

	'''Custom exception classes should have status_code and default message.'''

	exc_map = {
		exceptions.RepositoryError: 500,
		exceptions.EntityAlreadyExists: 409,
		exceptions.NotFoundError: 404,
		exceptions.DomainError: 400,
		exceptions.UnauthorizedError: 401
	}

	for cls, expected_code in exc_map.items():
		inst = cls()
		assert hasattr(inst, "status_code"), f"{cls.__name__} must have status_code"
		assert getattr(inst, "status_code") == expected_code
		# default str() should include the default message text
		assert isinstance(str(inst), str) and str(inst)


class RepositoryError(Exception):

    """ General repository error """

    status_code = 500

    def __init__(self, message: str = "Repository error"):
        super().__init__(message)


class EntityAlreadyExists(Exception):
    
    """ Entity already exists in the database """

    status_code = 409

    def __init__(self, message: str = "Entity already exists"):
        super().__init__(message)


class NotFoundError(Exception):

    """Entity not found"""

    status_code = 404

    def __init__(self, message: str = "Entity not found"):
        super().__init__(message)


class DomainError(Exception):

    """Business logic/validation errors"""

    status_code = 400

    def __init__(self, message: str = "Domain error"):
        super().__init__(message)

class RepositoryError(Exception):
    """Error genérico del repositorio / BD"""
    pass

class EntityAlreadyExists(Exception):
    """Entidad ya existe (unique contraint)"""
    pass

class NotFoundError(Exception):
    """Entidad no encontrada"""
    pass

class DomainError(Exception):
    """Errores de lógica/validación de negocio"""
    pass
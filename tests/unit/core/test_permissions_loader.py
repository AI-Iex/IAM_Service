from app.core import permissions_loader

def test_permissions_dict_contains_known_keys():
	
	'''Check that the permissions dictionary contains expected permission keys.'''
	
	perms = permissions_loader.PERMISSIONS
	assert isinstance(perms, dict)
	assert "users:create" in perms
	assert "roles:create" in perms
	assert "clients:create" in perms
	assert "permissions:create" in perms
    

def test_permissions_namespace_has_attribute_mapping():

	'''Check that the Permissions namespace maps attributes to permission keys.'''

	# Permissions.USERS_CREATE should map to the canonical permission key "users:create"

	assert hasattr(permissions_loader.Permissions, "USERS_CREATE")
	assert permissions_loader.Permissions.USERS_CREATE == "users:create"
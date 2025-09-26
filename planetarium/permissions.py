from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminOrIfAuthenticatedReadOnly(BasePermission):
    """
     Allows:
     - any authenticated user to read (GET)
     - only admin to create, update, delete
     """
    def has_permission(self, request, view):
        return bool(
            (
                request.method in SAFE_METHODS
                and request.user
                and request.user.is_authenticated
            )
            or (request.user and request.user.is_staff)
        )


class IsOwnerOrAdmin(BasePermission):
    """
    Grants object access only to the owner or admin
    """

    def has_object_permission(self, request, view, obj):
        owner = getattr(obj, "user", None) or getattr(obj, "created_by", None)

        return bool(
            request.user
            and (
                request.user.is_staff
                or owner == request.user
            )
        )

from rest_framework.permissions import BasePermission


class IsOwnerUser(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class IsParticipantUser(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

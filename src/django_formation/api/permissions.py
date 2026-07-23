from rest_framework.permissions import BasePermission


def _user_is_member_of(user, etablissement_id):
    if not user or not user.is_authenticated:
        return False
    from django_formation.models.membre import MembreEtablissement
    return MembreEtablissement.objects.filter(
        utilisateur=user, etablissement_id=etablissement_id, actif=True,
    ).exists()


class IsAuthenticatedMember(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)


class IsProprietaireOrAdmin(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return True

    def has_object_permission(self, request, view, obj):
        etablissement_id = getattr(obj, "etablissement_id", None) or getattr(obj, "id", None)
        from django_formation.models.membre import MembreEtablissement
        return MembreEtablissement.objects.filter(
            utilisateur=request.user, etablissement_id=etablissement_id,
            actif=True, role__in=["PROPRIETAIRE", "ADMINISTRATEUR"],
        ).exists()


class CanManageLearners(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        from django_formation.models.membre import MembreEtablissement
        return MembreEtablissement.objects.filter(
            utilisateur=request.user, etablissement_id=obj.etablissement_id,
            actif=True, role__in=["PROPRIETAIRE", "ADMINISTRATEUR", "RESPONSABLE", "AGENT_INSCRIPTION"],
        ).exists()


class CanManageEnrollments(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        from django_formation.models.membre import MembreEtablissement
        return MembreEtablissement.objects.filter(
            utilisateur=request.user, etablissement_id=obj.etablissement_id,
            actif=True, role__in=["PROPRIETAIRE", "ADMINISTRATEUR", "RESPONSABLE", "AGENT_INSCRIPTION"],
        ).exists()

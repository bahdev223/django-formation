from django.db import transaction

from django_formation.domain.exceptions.formation_exceptions import (
    InactiveEstablishmentError, ArchivedTrainingError, InvalidStatusTransitionError,
)
from django_formation.domain.value_objects.statut_formation import StatutFormation
from django_formation.models.etablissement import Etablissement
from django_formation.models.formation import Formation
from django_formation.signals.formation_signals import formation_publiee, formation_archivee


class FormationService:
    @transaction.atomic
    def creer_formation(self, *, etablissement: Etablissement, code: str, nom: str, **kwargs) -> Formation:
        if not etablissement.actif:
            raise InactiveEstablishmentError()
        formation = Formation.objects.create(etablissement=etablissement, code=code, nom=nom, **kwargs)
        return formation

    @transaction.atomic
    def modifier_formation(self, formation: Formation, **kwargs) -> Formation:
        for field, value in kwargs.items():
            if hasattr(formation, field):
                setattr(formation, field, value)
        formation.save()
        return formation

    @transaction.atomic
    def publier_formation(self, formation: Formation) -> Formation:
        if not StatutFormation(formation.statut).can_transition_to(StatutFormation.PUBLIEE):
            raise InvalidStatusTransitionError(formation.statut, "PUBLIEE")
        if not formation.etablissement.actif:
            raise InactiveEstablishmentError()
        formation.statut = Formation.Statut.PUBLIEE
        formation.save(update_fields=["statut"])
        formation_publiee.send(sender=self.__class__, formation=formation)
        return formation

    @transaction.atomic
    def suspendre_formation(self, formation: Formation) -> Formation:
        if not StatutFormation(formation.statut).can_transition_to(StatutFormation.SUSPENDUE):
            raise InvalidStatusTransitionError(formation.statut, "SUSPENDUE")
        formation.statut = Formation.Statut.SUSPENDUE
        formation.save(update_fields=["statut"])
        return formation

    @transaction.atomic
    def reactiver_formation(self, formation: Formation) -> Formation:
        if not StatutFormation(formation.statut).can_transition_to(StatutFormation.PUBLIEE):
            raise InvalidStatusTransitionError(formation.statut, "PUBLIEE")
        formation.statut = Formation.Statut.PUBLIEE
        formation.save(update_fields=["statut"])
        return formation

    @transaction.atomic
    def archiver_formation(self, formation: Formation) -> Formation:
        if not StatutFormation(formation.statut).can_transition_to(StatutFormation.ARCHIVEE):
            raise InvalidStatusTransitionError(formation.statut, "ARCHIVEE")
        formation.statut = Formation.Statut.ARCHIVEE
        formation.save(update_fields=["statut"])
        formation_archivee.send(sender=self.__class__, formation=formation)
        return formation

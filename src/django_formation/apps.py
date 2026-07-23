from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class FormationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_formation"
    verbose_name = _("Formation")

    def ready(self):
        from django_formation.signals import (
            apprenant_cree, apprenant_archive,
            formation_publiee, formation_archivee,
            session_inscriptions_ouvertes, session_demarre, session_terminee, session_annulee,
            inscription_creee, inscription_demarre, inscription_confirmee, inscription_refusee,
            inscription_annulee, inscription_abandonnee, inscription_terminee,
        )

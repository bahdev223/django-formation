from django.contrib import admin
from django_formation.models.etablissement import Etablissement
from django_formation.models.membre import MembreEtablissement
from django_formation.models.apprenant import Apprenant
from django_formation.models.formation import Formation
from django_formation.models.session import SessionFormation
from django_formation.models.inscription import Inscription
from django_formation.models.historique import HistoriqueStatutInscription


class MembreInline(admin.TabularInline):
    model = MembreEtablissement
    extra = 1


@admin.register(Etablissement)
class EtablissementAdmin(admin.ModelAdmin):
    list_display = ["nom", "code", "ville", "pays", "actif", "created_at"]
    list_filter = ["actif", "pays", "ville"]
    search_fields = ["nom", "code", "email"]
    inlines = [MembreInline]


@admin.register(MembreEtablissement)
class MembreEtablissementAdmin(admin.ModelAdmin):
    list_display = ["utilisateur", "etablissement", "role", "actif"]
    list_filter = ["role", "actif"]


@admin.register(Apprenant)
class ApprenantAdmin(admin.ModelAdmin):
    list_display = ["matricule", "nom", "prenom", "telephone", "etablissement", "statut"]
    list_filter = ["statut", "etablissement"]
    search_fields = ["matricule", "nom", "prenom", "telephone", "email"]


@admin.register(Formation)
class FormationAdmin(admin.ModelAdmin):
    list_display = ["code", "nom", "etablissement", "duree_heures", "tarif_indicatif", "statut"]
    list_filter = ["statut", "etablissement"]
    search_fields = ["code", "nom"]


@admin.register(SessionFormation)
class SessionFormationAdmin(admin.ModelAdmin):
    list_display = ["code", "nom", "formation", "date_debut", "date_fin", "capacite", "statut"]
    list_filter = ["statut", "etablissement"]
    search_fields = ["code", "nom"]


@admin.register(Inscription)
class InscriptionAdmin(admin.ModelAdmin):
    list_display = ["numero", "apprenant", "session", "date_inscription", "statut"]
    list_filter = ["statut"]
    search_fields = ["numero"]


@admin.register(HistoriqueStatutInscription)
class HistoriqueStatutInscriptionAdmin(admin.ModelAdmin):
    list_display = ["inscription", "ancien_statut", "nouveau_statut", "created_at"]
    readonly_fields = ["inscription", "ancien_statut", "nouveau_statut", "commentaire", "modifie_par"]

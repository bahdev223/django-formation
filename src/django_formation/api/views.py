from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from django_formation.models.etablissement import Etablissement
from django_formation.models.apprenant import Apprenant
from django_formation.models.formation import Formation
from django_formation.models.session import SessionFormation
from django_formation.models.inscription import Inscription
from django_formation.models.membre import MembreEtablissement
from django_formation.api.serializers import (
    EtablissementSerializer, EtablissementListSerializer,
    MembreEtablissementSerializer,
    ApprenantListSerializer, ApprenantDetailSerializer, ApprenantCreateSerializer,
    FormationListSerializer, FormationDetailSerializer,
    SessionListSerializer, SessionDetailSerializer,
    InscriptionListSerializer, InscriptionDetailSerializer, InscriptionCreateSerializer,
    SessionStatsSerializer, InscriptionHistoriqueSerializer,
)
from django_formation.api.permissions import (
    IsAuthenticatedMember, IsProprietaireOrAdmin, CanManageLearners, CanManageEnrollments,
)
from django_formation.services.apprenants import ApprenantService
from django_formation.services.formations import FormationService
from django_formation.services.sessions import SessionService
from django_formation.services.inscriptions import InscriptionService
from django_formation.selectors.apprenants import ApprenantSelector
from django_formation.selectors.formations import FormationSelector
from django_formation.selectors.sessions import SessionSelector
from django_formation.selectors.inscriptions import InscriptionSelector
from django_formation.domain.exceptions.formation_exceptions import FormationDomainError

apprenant_svc = ApprenantService()
formation_svc = FormationService()
session_svc = SessionService()
inscription_svc = InscriptionService()
apprenant_sel = ApprenantSelector()
formation_sel = FormationSelector()
session_sel = SessionSelector()
inscription_sel = InscriptionSelector()


def _get_etablissement_from_request(request):
    etablissement_id = request.GET.get("etablissement") or request.data.get("etablissement")
    if etablissement_id:
        return get_object_or_404(Etablissement, pk=etablissement_id, membres__utilisateur=request.user, membres__actif=True)
    return None


# ---- Établissements ----

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def etablissement_list_create(request):
    if request.method == "GET":
        qs = Etablissement.objects.filter(membres__utilisateur=request.user, membres__actif=True).distinct()
        return Response(EtablissementListSerializer(qs, many=True).data)
    serializer = EtablissementSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    etablissement = serializer.save()
    MembreEtablissement.objects.create(etablissement=etablissement, utilisateur=request.user, role="PROPRIETAIRE")
    return Response(EtablissementSerializer(etablissement).data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def etablissement_detail(request, pk):
    etablissement = get_object_or_404(Etablissement, pk=pk, membres__utilisateur=request.user, membres__actif=True)
    if request.method == "GET":
        return Response(EtablissementSerializer(etablissement).data)
    serializer = EtablissementSerializer(etablissement, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(EtablissementSerializer(etablissement).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def etablissement_activer(request, pk):
    etablissement = get_object_or_404(Etablissement, pk=pk, membres__utilisateur=request.user, membres__actif=True)
    etablissement.actif = True
    etablissement.save(update_fields=["actif"])
    return Response({"status": "ok"})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def etablissement_desactiver(request, pk):
    etablissement = get_object_or_404(Etablissement, pk=pk, membres__utilisateur=request.user, membres__actif=True)
    etablissement.actif = False
    etablissement.save(update_fields=["actif"])
    return Response({"status": "ok"})


# ---- Membres ----

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def membre_list_create(request, pk):
    etablissement = get_object_or_404(Etablissement, pk=pk)
    if request.method == "GET":
        qs = MembreEtablissement.objects.filter(etablissement=etablissement)
        return Response(MembreEtablissementSerializer(qs, many=True).data)
    serializer = MembreEtablissementSerializer(data={**request.data, "etablissement": str(etablissement.pk)})
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def membre_detail(request, pk):
    membre = get_object_or_404(MembreEtablissement, pk=pk)
    if request.method == "PATCH":
        serializer = MembreEtablissementSerializer(membre, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(MembreEtablissementSerializer(membre).data)
    membre.actif = False
    membre.save(update_fields=["actif"])
    return Response(status=status.HTTP_204_NO_CONTENT)


# ---- Apprenants ----

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def apprenant_list_create(request):
    if request.method == "GET":
        etablissement_id = request.query_params.get("etablissement")
        statut = request.query_params.get("statut")
        search = request.query_params.get("search")
        ordering = request.query_params.get("ordering", "nom")
        if not etablissement_id:
            return Response({"error": "etablissement parameter is required"}, status=400)
        qs = apprenant_sel.rechercher_apprenants(etablissement_id, query=search or "", statut=statut)
        qs = qs.order_by(ordering)
        return Response(ApprenantListSerializer(qs, many=True).data)
    serializer = ApprenantCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    etablissement_id = request.data.get("etablissement")
    etablissement = get_object_or_404(Etablissement, pk=etablissement_id)
    try:
        apprenant = apprenant_svc.creer_apprenant(etablissement=etablissement, **serializer.validated_data, cree_par=request.user)
        return Response(ApprenantDetailSerializer(apprenant).data, status=status.HTTP_201_CREATED)
    except FormationDomainError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def apprenant_detail(request, pk):
    apprenant = get_object_or_404(Apprenant, pk=pk)
    if request.method == "GET":
        return Response(ApprenantDetailSerializer(apprenant).data)
    serializer = ApprenantCreateSerializer(apprenant, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    for field, value in serializer.validated_data.items():
        setattr(apprenant, field, value)
    apprenant.save()
    return Response(ApprenantDetailSerializer(apprenant).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def apprenant_activer(request, pk):
    apprenant = get_object_or_404(Apprenant, pk=pk)
    try:
        apprenant_svc.activer_apprenant(apprenant)
        return Response(ApprenantDetailSerializer(apprenant).data)
    except FormationDomainError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def apprenant_desactiver(request, pk):
    apprenant = get_object_or_404(Apprenant, pk=pk)
    try:
        apprenant_svc.desactiver_apprenant(apprenant)
        return Response(ApprenantDetailSerializer(apprenant).data)
    except FormationDomainError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def apprenant_archiver(request, pk):
    apprenant = get_object_or_404(Apprenant, pk=pk)
    try:
        apprenant_svc.archiver_apprenant(apprenant)
        return Response(ApprenantDetailSerializer(apprenant).data)
    except FormationDomainError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def apprenant_inscriptions(request, pk):
    apprenant = get_object_or_404(Apprenant, pk=pk)
    inscriptions = apprenant_sel.inscriptions_apprenant(apprenant)
    return Response(InscriptionListSerializer(inscriptions, many=True).data)


# ---- Formations ----

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def formation_list_create(request):
    if request.method == "GET":
        etablissement_id = request.query_params.get("etablissement")
        statut = request.query_params.get("statut")
        search = request.query_params.get("search")
        if etablissement_id:
            qs = formation_sel.formations_par_etablissement(etablissement_id)
        else:
            qs = formation_sel.formations_accessibles_par_utilisateur(request.user)
        if statut:
            qs = qs.filter(statut=statut)
        if search:
            from django.db.models import Q
            qs = qs.filter(Q(nom__icontains=search) | Q(code__icontains=search))
        return Response(FormationListSerializer(qs, many=True).data)
    serializer = FormationDetailSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        formation = formation_svc.creer_formation(**serializer.validated_data)
        return Response(FormationDetailSerializer(formation).data, status=status.HTTP_201_CREATED)
    except FormationDomainError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def formation_detail(request, pk):
    formation = get_object_or_404(Formation, pk=pk)
    if request.method == "GET":
        return Response(FormationDetailSerializer(formation).data)
    serializer = FormationDetailSerializer(formation, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    for field, value in serializer.validated_data.items():
        setattr(formation, field, value)
    formation.save()
    return Response(FormationDetailSerializer(formation).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def formation_publier(request, pk):
    formation = get_object_or_404(Formation, pk=pk)
    try:
        formation_svc.publier_formation(formation)
        return Response(FormationDetailSerializer(formation).data)
    except FormationDomainError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def formation_suspendre(request, pk):
    formation = get_object_or_404(Formation, pk=pk)
    try:
        formation_svc.suspendre_formation(formation)
        return Response(FormationDetailSerializer(formation).data)
    except FormationDomainError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def formation_reactiver(request, pk):
    formation = get_object_or_404(Formation, pk=pk)
    try:
        formation_svc.reactiver_formation(formation)
        return Response(FormationDetailSerializer(formation).data)
    except FormationDomainError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def formation_archiver(request, pk):
    formation = get_object_or_404(Formation, pk=pk)
    try:
        formation_svc.archiver_formation(formation)
        return Response(FormationDetailSerializer(formation).data)
    except FormationDomainError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def formation_sessions(request, pk):
    formation = get_object_or_404(Formation, pk=pk)
    sessions = formation_sel.sessions_formation(pk)
    return Response(SessionListSerializer(sessions, many=True).data)


# ---- Sessions ----

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def session_list_create(request):
    if request.method == "GET":
        etablissement_id = request.query_params.get("etablissement")
        formation_id = request.query_params.get("formation")
        statut = request.query_params.get("statut")
        if etablissement_id:
            qs = SessionFormation.objects.filter(etablissement_id=etablissement_id)
        else:
            qs = session_sel.sessions_accessibles_par_utilisateur(request.user)
        if formation_id:
            qs = qs.filter(formation_id=formation_id)
        if statut:
            qs = qs.filter(statut=statut)
        return Response(SessionListSerializer(qs, many=True).data)
    serializer = SessionDetailSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        formation = get_object_or_404(Formation, pk=request.data["formation"])
        etablissement = get_object_or_404(Etablissement, pk=request.data["etablissement"])
        data = {k: v for k, v in serializer.validated_data.items() if k not in ("etablissement", "formation")}
        session = session_svc.creer_session(etablissement=etablissement, formation=formation, **data)
        return Response(SessionDetailSerializer(session).data, status=status.HTTP_201_CREATED)
    except FormationDomainError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def session_detail(request, pk):
    session = get_object_or_404(SessionFormation, pk=pk)
    if request.method == "GET":
        return Response(SessionDetailSerializer(session).data)
    serializer = SessionDetailSerializer(session, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    for field, value in serializer.validated_data.items():
        setattr(session, field, value)
    session.save()
    return Response(SessionDetailSerializer(session).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def session_ouvrir_inscriptions(request, pk):
    session = get_object_or_404(SessionFormation, pk=pk)
    try:
        session_svc.ouvrir_inscriptions(session)
        return Response(SessionDetailSerializer(session).data)
    except FormationDomainError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def session_fermer_inscriptions(request, pk):
    session = get_object_or_404(SessionFormation, pk=pk)
    try:
        session_svc.fermer_inscriptions(session)
        return Response(SessionDetailSerializer(session).data)
    except FormationDomainError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def session_demarrer(request, pk):
    session = get_object_or_404(SessionFormation, pk=pk)
    try:
        session_svc.demarrer_session(session)
        return Response(SessionDetailSerializer(session).data)
    except FormationDomainError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def session_terminer(request, pk):
    session = get_object_or_404(SessionFormation, pk=pk)
    try:
        session_svc.terminer_session(session)
        return Response(SessionDetailSerializer(session).data)
    except FormationDomainError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def session_annuler(request, pk):
    session = get_object_or_404(SessionFormation, pk=pk)
    try:
        session_svc.annuler_session(session)
        return Response(SessionDetailSerializer(session).data)
    except FormationDomainError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def session_inscriptions(request, pk):
    session = get_object_or_404(SessionFormation, pk=pk)
    inscrits = session_sel.inscrits_session(pk)
    return Response(InscriptionListSerializer(inscrits, many=True).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def session_statistiques(request, pk):
    session = get_object_or_404(SessionFormation, pk=pk)
    stats = {
        "session_id": session.pk,
        "capacite": session.capacite,
        "nombre_inscriptions": session.inscriptions.count(),
        "nombre_confirmes": session.inscriptions.filter(statut="CONFIRMEE").count(),
        "nombre_en_attente": session.inscriptions.filter(statut="EN_ATTENTE").count(),
        "nombre_annules": session.inscriptions.filter(statut="ANNULEE").count(),
        "places_restantes": session.nombre_places_restantes,
        "session_complete": session.est_complete,
    }
    return Response(SessionStatsSerializer(stats).data)


# ---- Inscriptions ----

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def inscription_list_create(request):
    if request.method == "GET":
        session_id = request.query_params.get("session")
        apprenant_id = request.query_params.get("apprenant")
        statut_filter = request.query_params.get("statut")
        if session_id:
            qs = inscription_sel.inscriptions_par_session(session_id)
        elif apprenant_id:
            qs = inscription_sel.inscriptions_par_apprenant(apprenant_id)
        else:
            qs = inscription_sel.inscriptions_accessibles_par_utilisateur(request.user)
        if statut_filter:
            qs = qs.filter(statut=statut_filter)
        return Response(InscriptionListSerializer(qs, many=True).data)
    serializer = InscriptionCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        apprenant = get_object_or_404(Apprenant, pk=serializer.validated_data["apprenant"])
        session = get_object_or_404(SessionFormation, pk=serializer.validated_data["session"])
        inscription = inscription_svc.creer_preinscription(
            apprenant=apprenant, session=session,
            commentaire=serializer.validated_data.get("commentaire", ""), cree_par=request.user,
        )
        return Response(InscriptionDetailSerializer(inscription).data, status=status.HTTP_201_CREATED)
    except FormationDomainError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def inscription_detail(request, pk):
    inscription = get_object_or_404(Inscription, pk=pk)
    return Response(InscriptionDetailSerializer(inscription).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def inscription_mettre_en_attente(request, pk):
    inscription = get_object_or_404(Inscription, pk=pk)
    try:
        inscription_svc.mettre_en_attente(inscription, modifie_par=request.user)
        return Response(InscriptionDetailSerializer(inscription).data)
    except FormationDomainError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def inscription_confirmer(request, pk):
    inscription = get_object_or_404(Inscription, pk=pk)
    try:
        inscription_svc.confirmer_inscription(inscription, modifie_par=request.user)
        return Response(InscriptionDetailSerializer(inscription).data)
    except FormationDomainError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def inscription_refuser(request, pk):
    inscription = get_object_or_404(Inscription, pk=pk)
    motif = request.data.get("motif", "")
    try:
        inscription_svc.refuser_inscription(inscription, motif=motif, modifie_par=request.user)
        return Response(InscriptionDetailSerializer(inscription).data)
    except FormationDomainError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def inscription_annuler(request, pk):
    inscription = get_object_or_404(Inscription, pk=pk)
    motif = request.data.get("motif", "")
    try:
        inscription_svc.annuler_inscription(inscription, motif=motif, modifie_par=request.user)
        return Response(InscriptionDetailSerializer(inscription).data)
    except FormationDomainError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def inscription_demarrer(request, pk):
    inscription = get_object_or_404(Inscription, pk=pk)
    try:
        inscription_svc.demarrer_inscription(inscription, modifie_par=request.user)
        return Response(InscriptionDetailSerializer(inscription).data)
    except FormationDomainError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def inscription_abandonner(request, pk):
    inscription = get_object_or_404(Inscription, pk=pk)
    try:
        inscription_svc.marquer_abandon(inscription, modifie_par=request.user)
        return Response(InscriptionDetailSerializer(inscription).data)
    except FormationDomainError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def inscription_terminer(request, pk):
    inscription = get_object_or_404(Inscription, pk=pk)
    try:
        inscription_svc.terminer_inscription(inscription, modifie_par=request.user)
        return Response(InscriptionDetailSerializer(inscription).data)
    except FormationDomainError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def inscription_historique(request, pk):
    inscription = get_object_or_404(Inscription, pk=pk)
    historique = inscription_sel.historique_inscription(pk)
    return Response(InscriptionHistoriqueSerializer(historique, many=True).data)

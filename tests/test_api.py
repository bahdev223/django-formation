import json
from datetime import date
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django_formation.models.etablissement import Etablissement
from django_formation.models.membre import MembreEtablissement
from django_formation.models.apprenant import Apprenant
from django_formation.models.formation import Formation
from django_formation.models.session import SessionFormation
from django_formation.models.inscription import Inscription


class FormationAPITest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="admin", password="testpass")
        self.client.force_login(self.user)
        self.etab = Etablissement.objects.create(nom="Sahel Formation", code="sahel")
        MembreEtablissement.objects.create(etablissement=self.etab, utilisateur=self.user, role="PROPRIETAIRE")

    def _post(self, url, data):
        return self.client.post(url, data=json.dumps(data), content_type="application/json")

    def test_api_liste_etablissements(self):
        response = self.client.get(reverse("formation:etablissement-list"))
        self.assertEqual(response.status_code, 200)

    def test_api_creation_apprenant(self):
        response = self._post(reverse("formation:apprenant-list"), {
            "etablissement": str(self.etab.id),
            "nom": "Diarra", "prenom": "Mamadou",
        })
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["nom"], "DIARRA")

    def test_api_liste_apprenants(self):
        Apprenant.objects.create(etablissement=self.etab, matricule="APP-001", nom="A", prenom="B")
        response = self.client.get(f"{reverse('formation:apprenant-list')}?etablissement={self.etab.id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_api_creation_formation(self):
        response = self._post(reverse("formation:formation-list"), {
            "etablissement": str(self.etab.id), "code": "DEVWEB", "nom": "Développement Web",
        })
        self.assertEqual(response.status_code, 201)

    def test_api_publication_formation(self):
        f = Formation.objects.create(etablissement=self.etab, code="DEVWEB", nom="Dev")
        response = self.client.post(reverse("formation:formation-publier", args=[f.id]))
        self.assertEqual(response.status_code, 200)

    def test_api_creation_session(self):
        f = Formation.objects.create(etablissement=self.etab, code="DEVWEB", nom="Dev", statut=Formation.Statut.PUBLIEE)
        response = self._post(reverse("formation:session-list"), {
            "etablissement": str(self.etab.id), "formation": str(f.id),
            "code": "DEVWEB-2026-S01", "nom": "Promo Sept 2026",
            "date_debut": "2026-09-01", "capacite": 25,
        })
        self.assertEqual(response.status_code, 201)

    def test_api_ouverture_inscriptions(self):
        f = Formation.objects.create(etablissement=self.etab, code="DEVWEB", nom="Dev", statut=Formation.Statut.PUBLIEE)
        s = SessionFormation.objects.create(
            etablissement=self.etab, formation=f, code="S01", nom="S1",
            date_debut=date(2026, 9, 1),
        )
        response = self.client.post(reverse("formation:session-ouvrir-inscriptions", args=[s.id]))
        self.assertEqual(response.status_code, 200)

    def test_api_creation_preinscription(self):
        f = Formation.objects.create(etablissement=self.etab, code="DEVWEB", nom="Dev", statut=Formation.Statut.PUBLIEE)
        s = SessionFormation.objects.create(
            etablissement=self.etab, formation=f, code="S01", nom="S1",
            date_debut=date(2026, 9, 1), capacite=5,
            statut=SessionFormation.Statut.INSCRIPTIONS_OUVERTES,
        )
        a = Apprenant.objects.create(etablissement=self.etab, matricule="APP-001", nom="A", prenom="B")
        response = self._post(reverse("formation:inscription-list"), {
            "apprenant": str(a.id), "session": str(s.id),
        })
        self.assertEqual(response.status_code, 201)

    def test_api_confirmation_inscription(self):
        f = Formation.objects.create(etablissement=self.etab, code="DEVWEB", nom="Dev", statut=Formation.Statut.PUBLIEE)
        s = SessionFormation.objects.create(
            etablissement=self.etab, formation=f, code="S01", nom="S1",
            date_debut=date(2026, 9, 1),
            statut=SessionFormation.Statut.INSCRIPTIONS_OUVERTES,
        )
        a = Apprenant.objects.create(etablissement=self.etab, matricule="APP-001", nom="A", prenom="B")
        ins = Inscription.objects.create(
            etablissement=self.etab, apprenant=a, session=s,
            numero="INS-001", date_inscription=date.today(),
        )
        response = self.client.post(reverse("formation:inscription-confirmer", args=[ins.id]))
        self.assertEqual(response.status_code, 200)


class MultiEtablissementIsolationTest(TestCase):
    """Test qu'un utilisateur ne peut pas accéder aux objets d'un autre établissement"""

    def setUp(self):
        self.user_a = User.objects.create_user(username="user_a", password="testpass")
        self.user_b = User.objects.create_user(username="user_b", password="testpass")
        self.etab_a = Etablissement.objects.create(nom="Etablissement A", code="eta")
        self.etab_b = Etablissement.objects.create(nom="Etablissement B", code="etb")
        MembreEtablissement.objects.create(etablissement=self.etab_a, utilisateur=self.user_a, role="PROPRIETAIRE")
        MembreEtablissement.objects.create(etablissement=self.etab_b, utilisateur=self.user_b, role="PROPRIETAIRE")

        from datetime import date
        self.formation_b = Formation.objects.create(etablissement=self.etab_b, code="ETB-FORM", nom="Formation B", statut=Formation.Statut.PUBLIEE)
        self.apprenant_b = Apprenant.objects.create(etablissement=self.etab_b, matricule="APP-ETB-001", nom="B", prenom="User")
        self.session_b = SessionFormation.objects.create(
            etablissement=self.etab_b, formation=self.formation_b,
            code="ETB-S01", nom="Session B", date_debut=date(2026, 9, 1),
            statut=SessionFormation.Statut.INSCRIPTIONS_OUVERTES,
        )

    def test_user_a_ne_peut_pas_lire_formation_b(self):
        self.client.force_login(self.user_a)
        response = self.client.get(reverse("formation:formation-detail", args=[self.formation_b.id]))
        self.assertEqual(response.status_code, 404)

    def test_user_a_ne_peut_pas_modifier_formation_b(self):
        self.client.force_login(self.user_a)
        response = self.client.patch(
            reverse("formation:formation-detail", args=[self.formation_b.id]),
            data=json.dumps({"nom": "Hack"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)

    def test_user_a_ne_peut_pas_publier_formation_b(self):
        self.client.force_login(self.user_a)
        response = self.client.post(reverse("formation:formation-publier", args=[self.formation_b.id]))
        self.assertEqual(response.status_code, 404)

    def test_user_a_ne_peut_pas_lire_apprenant_b(self):
        self.client.force_login(self.user_a)
        response = self.client.get(reverse("formation:apprenant-detail", args=[self.apprenant_b.id]))
        self.assertEqual(response.status_code, 404)

    def test_user_a_ne_peut_pas_modifier_apprenant_b(self):
        self.client.force_login(self.user_a)
        response = self.client.patch(
            reverse("formation:apprenant-detail", args=[self.apprenant_b.id]),
            data=json.dumps({"nom": "Hack"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)

    def test_user_a_ne_peut_pas_lire_session_b(self):
        self.client.force_login(self.user_a)
        response = self.client.get(reverse("formation:session-detail", args=[self.session_b.id]))
        self.assertEqual(response.status_code, 404)

    def test_user_a_ne_peut_pas_ouvrir_inscriptions_session_b(self):
        self.client.force_login(self.user_a)
        response = self.client.post(reverse("formation:session-ouvrir-inscriptions", args=[self.session_b.id]))
        self.assertEqual(response.status_code, 404)

    def test_user_a_ne_peut_pas_annuler_session_b(self):
        self.client.force_login(self.user_a)
        response = self.client.post(reverse("formation:session-annuler", args=[self.session_b.id]))
        self.assertEqual(response.status_code, 404)

    def test_user_a_ne_peut_pas_inscrire_dans_session_b(self):
        self.client.force_login(self.user_a)
        response = self._post(reverse("formation:inscription-list"), {
            "apprenant": str(self.apprenant_b.id), "session": str(self.session_b.id),
        })
        self.assertEqual(response.status_code, 404)

    def _post(self, url, data):
        return self.client.post(url, data=json.dumps(data), content_type="application/json")

    def test_lecteur_ne_peut_pas_publier_formation(self):
        """Un lecteur peut lire mais pas publier — reçoit 404 (objet filtré par rôle)"""
        lecteur = User.objects.create_user(username="lecteur", password="testpass")
        MembreEtablissement.objects.create(etablissement=self.etab_a, utilisateur=lecteur, role="LECTEUR")
        f = Formation.objects.create(etablissement=self.etab_a, code="LECT-FORM", nom="Formation test")
        self.client.force_login(lecteur)
        response = self.client.post(reverse("formation:formation-publier", args=[f.id]))
        self.assertEqual(response.status_code, 404)

    def test_agent_inscription_peut_lire_mais_pas_terminer_session(self):
        agent = User.objects.create_user(username="agent", password="testpass")
        MembreEtablissement.objects.create(etablissement=self.etab_a, utilisateur=agent, role="AGENT_INSCRIPTION")
        f = Formation.objects.create(etablissement=self.etab_a, code="AG-FORM", nom="Formation", statut=Formation.Statut.PUBLIEE)
        s = SessionFormation.objects.create(
            etablissement=self.etab_a, formation=f, code="AG-S01", nom="Session",
            date_debut=date(2026, 9, 1), statut=SessionFormation.Statut.INSCRIPTIONS_OUVERTES,
        )
        a = Apprenant.objects.create(etablissement=self.etab_a, matricule="APP-AG-001", nom="X", prenom="Y")
        ins = Inscription.objects.create(
            etablissement=self.etab_a, apprenant=a, session=s,
            numero="INS-AG-001", date_inscription=date.today(), statut=Inscription.Statut.CONFIRMEE,
        )
        self.client.force_login(agent)
        # Peut lire la session (AGENT_INSCRIPTION peut lire via _get_accessible)
        response = self.client.get(reverse("formation:session-detail", args=[s.id]))
        self.assertEqual(response.status_code, 200)
        # Ne peut pas terminer la session — reçoit 404 (objet filtré par rôle)
        response = self.client.post(reverse("formation:session-terminer", args=[s.id]))
        self.assertEqual(response.status_code, 404)

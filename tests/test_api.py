import json
from datetime import date
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from django_formation.models.etablissement import Etablissement
from django_formation.models.membre import MembreEtablissement
from django_formation.models.apprenant import Apprenant
from django_formation.models.formation import Formation
from django_formation.models.session import SessionFormation


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
        from django_formation.models.inscription import Inscription
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

# New roles retain legacy AGENT_INSCRIPTION and RESPONSABLE values.
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("django_formation", "0002_inscription_formation_unique_numero_inscription_etablissement")]

    operations = [
        migrations.AlterField(
            model_name="membreetablissement",
            name="role",
            field=models.CharField(max_length=30, choices=[
                ("PROPRIETAIRE", "Propriétaire"),
                ("ADMINISTRATEUR", "Administrateur"),
                ("RESPONSABLE", "Responsable de formation"),
                ("GERANT", "Gérant"),
                ("SECRETAIRE", "Secrétaire"),
                ("AGENT_INSCRIPTION", "Agent d'inscription"),
                ("LECTEUR", "Lecteur"),
            ], verbose_name="Rôle"),
        ),
    ]

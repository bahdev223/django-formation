from enum import Enum


class RoleEtablissement(Enum):
    PROPRIETAIRE = "PROPRIETAIRE"
    ADMINISTRATEUR = "ADMINISTRATEUR"
    RESPONSABLE = "RESPONSABLE"
    GERANT = "GERANT"
    SECRETAIRE = "SECRETAIRE"
    AGENT_INSCRIPTION = "AGENT_INSCRIPTION"
    LECTEUR = "LECTEUR"

    @property
    def label(self) -> str:
        return _LABELS[self]


_LABELS = {
    RoleEtablissement.PROPRIETAIRE: "Propriétaire",
    RoleEtablissement.ADMINISTRATEUR: "Administrateur",
    RoleEtablissement.RESPONSABLE: "Responsable de formation",
    RoleEtablissement.GERANT: "Gérant",
    RoleEtablissement.SECRETAIRE: "Secrétaire",
    RoleEtablissement.AGENT_INSCRIPTION: "Agent d'inscription",
    RoleEtablissement.LECTEUR: "Lecteur",
}

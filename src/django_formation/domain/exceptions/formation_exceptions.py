class FormationDomainError(Exception):
    pass


class InactiveEstablishmentError(FormationDomainError):
    def __init__(self, message="L'établissement est inactif"):
        super().__init__(message)


class InactiveLearnerError(FormationDomainError):
    def __init__(self, message="L'apprenant est inactif"):
        super().__init__(message)


class ArchivedLearnerError(FormationDomainError):
    def __init__(self, message="L'apprenant est archivé"):
        super().__init__(message)


class ArchivedTrainingError(FormationDomainError):
    def __init__(self, message="La formation est archivée"):
        super().__init__(message)


class InvalidStatusTransitionError(FormationDomainError):
    def __init__(self, current: str, target: str):
        super().__init__(f"Transition invalide de '{current}' vers '{target}'")


class SessionNotOpenError(FormationDomainError):
    def __init__(self, message="La session n'accepte pas les inscriptions"):
        super().__init__(message)


class SessionCapacityReachedError(FormationDomainError):
    def __init__(self, message="La capacité maximale de la session est atteinte"):
        super().__init__(message)


class DuplicateEnrollmentError(FormationDomainError):
    def __init__(self, message="Cet apprenant est déjà inscrit à cette session"):
        super().__init__(message)


class CrossEstablishmentOperationError(FormationDomainError):
    def __init__(self, message="Opération interdite entre différents établissements"):
        super().__init__(message)


class MissingRejectionReasonError(FormationDomainError):
    def __init__(self, message="Le motif de refus est obligatoire"):
        super().__init__(message)


class MissingCancellationReasonError(FormationDomainError):
    def __init__(self, message="Le motif d'annulation est obligatoire"):
        super().__init__(message)


class EstablishmentNotFoundError(FormationDomainError):
    def __init__(self, message="Établissement introuvable"):
        super().__init__(message)


class LearnerNotFoundError(FormationDomainError):
    def __init__(self, message="Apprenant introuvable"):
        super().__init__(message)


class TrainingNotFoundError(FormationDomainError):
    def __init__(self, message="Formation introuvable"):
        super().__init__(message)


class SessionNotFoundError(FormationDomainError):
    def __init__(self, message="Session introuvable"):
        super().__init__(message)


class EnrollmentNotFoundError(FormationDomainError):
    def __init__(self, message="Inscription introuvable"):
        super().__init__(message)

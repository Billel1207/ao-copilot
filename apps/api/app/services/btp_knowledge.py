"""Base de connaissances BTP française — enrichissement des analyses IA."""

# ─────────────────────────────────────────────────────────────────────────────
# GLOSSAIRE BTP (80+ termes)
# ─────────────────────────────────────────────────────────────────────────────

BTP_GLOSSARY: dict[str, str] = {
    # Documents de marché
    "RC": "Règlement de Consultation — document définissant les règles de la procédure de passation du marché (candidature, offre, critères de sélection, date limite de remise des offres).",
    "CCTP": "Cahier des Clauses Techniques Particulières — document contractuel décrivant les spécifications techniques, les matériaux, les méthodes d'exécution et les normes à respecter pour les travaux.",
    "CCAP": "Cahier des Clauses Administratives Particulières — document contractuel fixant les conditions d'exécution administrative et financière du marché (délais, pénalités, paiement, garanties).",
    "DPGF": "Décomposition du Prix Global et Forfaitaire — tableau quantitatif et financier permettant au soumissionnaire de ventiler son offre de prix par lots, ouvrages ou prestations.",
    "BPU": "Bordereau des Prix Unitaires — liste des prix unitaires HT proposés par l'entreprise pour chaque type de prestation, servant de base à la rémunération des travaux supplémentaires ou sur quantités.",
    "AE": "Acte d'Engagement — document contractuel signé par le candidat qui formalise son offre de prix et son engagement à réaliser les prestations aux conditions du marché.",
    "ATTRI": "Acte d'Attribution — document notifiant à l'entreprise retenue que son offre a été acceptée et que le marché lui est attribué.",
    "CCAG": "Cahier des Clauses Administratives Générales — texte réglementaire fixant les conditions générales d'exécution des marchés publics (travaux, fournitures, services, maîtrise d'oeuvre).",
    "CCAG-Travaux": "CCAG applicable aux marchés publics de travaux — texte de référence 2021 (arrêté du 30 mars 2021) régissant les relations contractuelles entre maître d'ouvrage et entreprises de travaux.",
    "DCE": "Dossier de Consultation des Entreprises — ensemble des documents mis à disposition des candidats pour leur permettre de préparer leur offre (RC, CCTP, CCAP, DPGF, plans...).",
    "DC1": "Lettre de candidature et habilitation du mandataire par ses cotraitants — formulaire officiel attestant la candidature et désignant le mandataire du groupement.",
    "DC2": "Déclaration du candidat individuel ou du membre du groupement — formulaire officiel récapitulant la situation juridique, financière et les capacités du candidat.",
    "DC3": "Acte d'Engagement (ancien formulaire) — document contractuel signé par le candidat formalisant l'offre de prix.",
    "DC4": "Déclaration de sous-traitance — formulaire officiel déclarant le sous-traitant et les prestations qui lui sont confiées.",

    # Acteurs et groupements
    "Mandataire": "Entreprise désignée par les membres d'un groupement (co-traitance) pour les représenter, coordonner les prestations et recevoir les paiements au nom du groupement.",
    "Cotraitant": "Entreprise membre d'un groupement momentané d'entreprises (GME) qui assume solidairement ou conjointement la réalisation de certaines prestations du marché.",
    "Co-traitance": "Mode de candidature associant plusieurs entreprises dans un groupement momentané (GME conjoint ou solidaire) pour répondre ensemble à un appel d'offres.",
    "Sous-traitance": "Contrat par lequel le titulaire du marché confie à une entreprise tierce (sous-traitant) l'exécution d'une partie des prestations, avec accord préalable du maître d'ouvrage.",
    "MOA": "Maîtrise d'Ouvrage — entité (personne publique ou privée) commanditaire de l'ouvrage, qui définit le besoin, finance le projet et en reste propriétaire.",
    "MOE": "Maîtrise d'Oeuvre — entité (architecte, bureau d'études) mandatée par le MOA pour concevoir le projet et diriger les travaux.",
    "OPC": "Ordonnancement, Pilotage et Coordination — mission de maîtrise d'oeuvre chargée de coordonner les interventions des entreprises et d'établir le planning détaillé.",
    "SPS": "Sécurité et Protection de la Santé — coordinateur chargé d'assurer la sécurité lors de la conception puis lors de l'exécution des travaux.",
    "BET": "Bureau d'Études Techniques — structure spécialisée intervenant en appui à la maîtrise d'oeuvre pour les études techniques (structure, fluides, thermique...).",

    # Documents et procédures techniques
    "PPSPS": "Plan Particulier de Sécurité et de Protection de la Santé — document obligatoire rédigé par chaque entreprise avant toute intervention sur chantier, décrivant les mesures de prévention des risques.",
    "PSS": "Plan de Sécurité et de Santé — document de référence établi par le coordinateur SPS regroupant les mesures de prévention pour le chantier.",
    "DOE": "Dossier des Ouvrages Exécutés — ensemble des documents remis par l'entrepreneur à la fin des travaux : plans conformes à exécution, notices techniques, fiches produits, garanties fabricants.",
    "DIUO": "Dossier d'Intervention Ultérieure sur l'Ouvrage — document élaboré par le coordinateur SPS regroupant les informations utiles à la maintenance future de l'ouvrage.",
    "OPR": "Opérations Préalables à la Réception — phase contradictoire entre maître d'ouvrage, maître d'oeuvre et entreprises permettant d'inventorier les réserves avant la réception des travaux.",
    "GPA": "Garantie de Parfait Achèvement — garantie d'un an à compter de la réception des travaux, obligeant l'entrepreneur à réparer tous les désordres signalés dans le PV de réception ou apparus dans l'année.",
    "DICT": "Déclaration d'Intention de Commencement de Travaux — déclaration obligatoire adressée aux gestionnaires de réseaux avant tout commencement de travaux, pour connaître l'emplacement des réseaux souterrains.",
    "DT": "Déclaration de projet de Travaux — demande adressée par le maître d'ouvrage aux exploitants de réseaux pour connaître les réseaux dans l'emprise du projet (avant DICT).",

    # Garanties et assurances
    "Garantie décennale": "Assurance obligatoire couvrant pendant 10 ans à compter de la réception les dommages compromettant la solidité de l'ouvrage ou le rendant impropre à sa destination (articles 1792 et suivants du Code civil).",
    "Garantie biennale": "Garantie de bon fonctionnement de 2 ans à compter de la réception, couvrant les éléments d'équipement dissociables de l'ouvrage (menuiseries, appareils sanitaires, installations électriques...).",
    "RIO": "Responsabilité décennale des constructeurs — responsabilité solidaire des constructeurs (entreprises, architectes, BET) pendant 10 ans pour les dommages à l'ouvrage.",
    "DO": "Dommages-Ouvrage — assurance obligatoire souscrite par le maître d'ouvrage, permettant le remboursement ou la réparation rapide des désordres relevant de la garantie décennale, sans attendre jugement.",
    "RC Pro": "Responsabilité Civile Professionnelle — assurance couvrant les dommages causés à des tiers dans le cadre de l'activité professionnelle de l'entreprise.",
    "Retenue de garantie": "Somme retenue sur chaque acompte (maximum 5% du marché) pour garantir l'exécution des obligations et la levée des réserves, libérée à l'expiration de la garantie de parfait achèvement.",
    "Caution bancaire": "Garantie fournie par un établissement financier, se substituant à la retenue de garantie ou garantissant la bonne fin du marché.",

    # Réception et fin de marché
    "PV de réception": "Procès-verbal de réception — document officiel signé par le maître d'ouvrage (avec ou sans réserves) constatant l'achèvement des travaux et leur acceptation, faisant courir les délais de garantie.",
    "Levée de réserves": "Action de l'entrepreneur consistant à réparer les désordres ou malfaçons consignés dans le PV de réception, après laquelle le maître d'ouvrage constate la levée par écrit.",
    "Réception avec réserves": "Réception prononcée en présence de malfaçons mineures, l'entrepreneur s'engageant à les corriger dans un délai fixé. Fait courir les délais de garantie.",
    "DGD": "Décompte Général et Définitif — document final arrêtant le montant définitif du marché, tenant compte de tous les avenants, travaux supplémentaires et déductions.",
    "DGD tacite": "DGD réputé accepté si l'entrepreneur ne conteste pas le projet de décompte dans les délais réglementaires.",
    "Constat d'huissier": "Acte établi par un huissier de justice constatant l'état des lieux avant travaux ou un sinistre, servant de preuve en cas de litige.",

    # Procédures de passation
    "Procédure adaptée (MAPA)": "Marché à Procédure Adaptée — procédure simplifiée applicable aux marchés dont le montant est inférieur aux seuils européens, laissant une liberté de négociation au pouvoir adjudicateur.",
    "Appel d'offres ouvert": "Procédure formalisée dans laquelle tout opérateur économique peut remettre une offre, sans pré-qualification ni négociation.",
    "Appel d'offres restreint": "Procédure formalisée avec une phase de sélection des candidats (short-listing) avant l'envoi du DCE aux seuls candidats retenus.",
    "Dialogue compétitif": "Procédure formalisée permettant la discussion avec les candidats sélectionnés pour définir les moyens propres à satisfaire le besoin, avant remise des offres.",
    "Procédure négociée": "Procédure dans laquelle le pouvoir adjudicateur consulte les opérateurs économiques de son choix et négocie les conditions du marché avec un ou plusieurs d'entre eux.",
    "Accord-cadre": "Accord conclu entre un pouvoir adjudicateur et des opérateurs économiques, établissant les termes des marchés ultérieurs (marchés subséquents) à passer pendant une durée déterminée.",
    "Allotissement": "Division d'un marché en plusieurs lots distincts, chacun pouvant faire l'objet d'une offre séparée, favorisant l'accès des PME.",
    "Variante": "Solution alternative proposée par le candidat, différente de la solution de base décrite dans le CCTP, soumise à autorisation dans le RC.",

    # Certifications et qualifications
    "Qualibat": "Organisme de qualification et certification des entreprises du bâtiment, délivrant des certifications techniques (ex: 2112 pour maçonnerie) et des qualifications.",
    "OPQIBI": "Organisme de Qualification des Ingénieurs et Bureaux d'Études — délivre des qualifications aux bureaux d'études techniques et ingénieries.",
    "FNTP": "Fédération Nationale des Travaux Publics — organisation professionnelle représentant les entreprises de travaux publics.",
    "MASE": "Manuel d'Amélioration Sécurité des Entreprises — certification sécurité pour les entreprises intervenantes sur sites industriels.",
    "ISO 9001": "Norme internationale de management de la qualité, attestant la mise en place d'un système de gestion de la qualité dans l'entreprise.",
    "ISO 14001": "Norme internationale de management environnemental, attestant la mise en place d'un système de gestion de l'impact environnemental.",
    "OHSAS 18001 / ISO 45001": "Norme de management de la santé et sécurité au travail (ISO 45001 remplace OHSAS 18001).",
    "RGE": "Reconnu Garant de l'Environnement — mention accordée aux entreprises de travaux et artisans respectant des critères de qualité pour les travaux de rénovation énergétique.",
    "APSAD": "Assemblée Plénière des Sociétés d'Assurances Dommages — certification délivrée pour les systèmes de sécurité incendie et anti-intrusion.",

    # Finance et facturation
    "Avance forfaitaire": "Somme versée par le maître d'ouvrage dès le début du marché (généralement 5% du montant HT), destinée à faciliter le démarrage des travaux, à rembourser progressivement.",
    "Acompte": "Versement partiel effectué au fur et à mesure de l'avancement des travaux, sur présentation d'une situation de travaux vérifiée par le maître d'oeuvre.",
    "Révision de prix": "Mécanisme contractuel permettant d'ajuster le montant du marché en fonction de l'évolution des indices de coût (matériaux, main-d'oeuvre), via une formule paramétrique.",
    "Actualisation des prix": "Ajustement du prix initial du marché entre la date de remise des prix et la date de début d'exécution, via l'application d'une formule d'actualisation.",
    "Pénalités de retard": "Sommes forfaitaires déduites du solde du marché en cas de dépassement des délais contractuels, exprimées en fraction du montant du marché par jour calendaire de retard.",
    "Intérêts moratoires": "Indemnités dues de plein droit par l'acheteur public à l'entreprise en cas de dépassement du délai global de paiement (30 jours en règle générale).",
    "Nantissement": "Affectation en garantie d'un droit de créance sur le marché au profit d'un établissement bancaire, permettant à l'entreprise d'obtenir un financement.",

    # Sécurité et environnement
    "VRD": "Voirie et Réseaux Divers — ensemble des travaux d'infrastructure (voirie, assainissement, eau potable, électricité, télécommunications) préalables ou concomitants à la construction.",
    "EPI": "Équipements de Protection Individuelle — matériels (casque, chaussures de sécurité, harnais, gilet haute visibilité...) obligatoires sur les chantiers BTP.",
    "ICF": "Installations de Chantier et Fixes — baraquements, clôtures, sanitaires, branchements provisoires mis en place par les entreprises pour la vie du chantier.",
    "Plan de retrait amiante": "Document obligatoire avant tous travaux sur matériaux contenant de l'amiante, décrivant les techniques de dépose et les mesures de protection.",
    "PGCSPS": "Plan Général de Coordination en matière de Sécurité et de Protection de la Santé — document élaboré par le coordinateur SPS pour les chantiers de catégorie 1 et 2.",

    # Marchés spécifiques
    "Marchés de travaux": "Marchés dont l'objet est la réalisation de travaux de bâtiment ou de génie civil.",
    "Marchés de services": "Marchés dont l'objet est la réalisation de prestations de service (études, maintenance, nettoyage...).",
    "Marchés de fournitures": "Marchés dont l'objet est l'achat, la location ou le crédit-bail de produits.",
    "Marché global": "Marché unique couvrant l'ensemble des prestations sans allotissement.",
    "Marché de conception-réalisation": "Marché confiant à un opérateur unique (ou groupement) la conception et la réalisation de l'ouvrage.",
    "PPP": "Partenariat Public-Privé — contrat associant une personne publique à un opérateur privé pour le financement, la conception, la construction, l'exploitation et la maintenance d'un ouvrage.",
    "BIM": "Building Information Modeling — méthode de travail collaborative s'appuyant sur un modèle numérique 3D intégrant toutes les données du projet (géométrie, matériaux, coûts, délais).",

    # Réglementation
    "Seuils européens": "Montants au-delà desquels les marchés publics doivent respecter les procédures formalisées européennes (publicité obligatoire au JOUE).",
    "JOUE": "Journal Officiel de l'Union Européenne — publication dans laquelle les marchés publics dépassant les seuils européens doivent être publiés.",
    "BOAMP": "Bulletin Officiel des Annonces des Marchés Publics — support officiel de publication des marchés publics français.",
    "JAL": "Journal d'Annonces Légales — journal habilité à publier les annonces légales des marchés publics.",
    "Dérogation MAPA": "Possibilité de passer un marché sans publicité ni mise en concurrence en dessous du seuil de 25 000 € HT.",
    "Candidature": "Première phase d'une procédure formalisée permettant à l'acheteur de vérifier les capacités techniques, financières et professionnelles des opérateurs.",
    "Offre": "Document par lequel le candidat présente sa proposition technique et financière pour exécuter le marché.",
    "Variante obligatoire": "Variante que le maître d'ouvrage impose aux candidats de remettre en plus de la solution de base.",
    "PSE": "Prestation Supplémentaire Éventuelle — prestation optionnelle listée dans le DCE, sur laquelle les candidats remettent un prix, mais qui n'est pas nécessairement commandée.",
    "NF DTU": "Norme Française Documents Techniques Unifiés — normes françaises de construction définissant les règles de l'art pour l'exécution des ouvrages du bâtiment.",
    "Eurocodes": "Normes européennes de calcul des structures (Eurocode 0 à 9), remplaçant progressivement les normes françaises de calcul (BAEL, CM66...).",
    "Essai de réception": "Tests réalisés en fin de chantier pour vérifier la conformité des ouvrages aux exigences du marché (essais d'étanchéité, de résistance, de performance thermique...).",
}


# ─────────────────────────────────────────────────────────────────────────────
# RÈGLES HEURISTIQUES CCAP (risques contractuels)
# ─────────────────────────────────────────────────────────────────────────────

CCAP_RISK_RULES: list[dict] = [
    {
        "rule": "penalite_retard",
        "description": "Pénalités de retard",
        "threshold": "1/1000 du marché par jour calendaire",
        "risk": "HAUT",
        "conseil": (
            "Le taux standard CCAG-Travaux est de 1/3000 du montant du marché par jour. "
            "Un taux supérieur à 1/1000 est considéré comme élevé et doit être négocié. "
            "Vérifier si le plafond est fixé (généralement 5 à 10% du marché) et si des "
            "événements de force majeure ou de suspension sont prévus."
        ),
    },
    {
        "rule": "retenue_garantie",
        "description": "Retenue de garantie excessive",
        "threshold": "> 5% du montant du marché",
        "risk": "HAUT",
        "conseil": (
            "La retenue de garantie est légalement plafonnée à 5% du montant initial du marché "
            "(article R2191-35 du Code de la commande publique). Au-delà, la clause est illégale. "
            "Vérifier la possibilité de substitution par une caution bancaire à première demande, "
            "moins coûteuse en trésorerie."
        ),
    },
    {
        "rule": "delai_paiement",
        "description": "Délai global de paiement",
        "threshold": "> 30 jours calendaires",
        "risk": "MOYEN",
        "conseil": (
            "Le délai légal de paiement pour les marchés publics est de 30 jours (décret 2013-269). "
            "Un délai supérieur ouvre droit à des intérêts moratoires automatiques. "
            "Vérifier le point de départ du délai (date de réception de la facture ou date de "
            "constatation des travaux) et les modalités de vérification des situations."
        ),
    },
    {
        "rule": "avance_forfaitaire_absence",
        "description": "Absence d'avance forfaitaire",
        "threshold": "0% alors que marché > 50 000 € HT",
        "risk": "MOYEN",
        "conseil": (
            "Pour les marchés supérieurs à 50 000 € HT, une avance forfaitaire de 5% est "
            "obligatoire sauf dérogation explicite (article R2191-3 du CCP). "
            "L'absence d'avance pèse sur la trésorerie de l'entreprise. "
            "Vérifier si une caution de remboursement est exigée pour bénéficier de l'avance."
        ),
    },
    {
        "rule": "clause_resiliation_unilaterale",
        "description": "Clause de résiliation unilatérale abusive",
        "threshold": "Résiliation sans indemnité ou indemnité < 5% des travaux restants",
        "risk": "HAUT",
        "conseil": (
            "Le CCAG-Travaux prévoit une indemnité de résiliation égale à 5% du montant HT des "
            "prestations non réalisées. Une clause plus restrictive est défavorable à l'entreprise. "
            "S'assurer que les frais engagés (études, commandes matériaux) sont couverts en cas "
            "de résiliation pour convenance du pouvoir adjudicateur."
        ),
    },
    {
        "rule": "clause_variation_masse_travaux",
        "description": "Absence de clause de variation de masse ou seuil bas",
        "threshold": "Pas de clause ou seuil < 5%",
        "risk": "MOYEN",
        "conseil": (
            "Une clause de variation de masse permet à l'entreprise de demander la résiliation ou "
            "une renégociation si les quantités varient de plus de 20% (règle standard). "
            "Un seuil inférieur à 5% expose l'entreprise à des variations importantes sans recours. "
            "Vérifier si le marché est à prix global et forfaitaire (risque quantités) ou à prix "
            "unitaires (mesure réelle)."
        ),
    },
    {
        "rule": "revision_prix_absente",
        "description": "Absence de clause de révision de prix sur marché long",
        "threshold": "Durée > 3 mois sans révision de prix",
        "risk": "MOYEN",
        "conseil": (
            "Sur des marchés de plus de 3 mois, l'absence de révision de prix expose l'entreprise "
            "à l'inflation des matériaux et de la main-d'oeuvre. "
            "Exiger une formule paramétrique adaptée (indices BT01, TP01...) ou intégrer une "
            "provision pour hausse des coûts dans l'offre de prix."
        ),
    },
    {
        "rule": "clause_solidarite_groupement",
        "description": "Solidarité totale du groupement",
        "threshold": "Groupement solidaire sur l'ensemble des prestations",
        "risk": "HAUT",
        "conseil": (
            "Dans un groupement solidaire, chaque membre est responsable de l'ensemble des "
            "prestations y compris celles des autres membres. "
            "Préférer un groupement conjoint si possible (chaque membre ne répond que de ses "
            "prestations propres). En solidaire, vérifier les assurances de chaque cotraitant "
            "et la qualité financière de chacun."
        ),
    },
    {
        "rule": "delai_reclamation_court",
        "description": "Délai de réclamation très court",
        "threshold": "< 30 jours pour émettre une réclamation",
        "risk": "MOYEN",
        "conseil": (
            "Un délai de réclamation très court peut priver l'entreprise de ses droits en cas de "
            "différend sur des aléas de chantier. "
            "Le CCAG-Travaux 2021 prévoit 30 jours pour formuler les réclamations. "
            "Mettre en place des processus internes de signalement rapide des aléas."
        ),
    },
    {
        "rule": "exigence_assurance_specifique",
        "description": "Exigences d'assurance spécifiques ou élevées",
        "threshold": "Montant garanti > 5 000 000 € ou assurances atypiques",
        "risk": "MOYEN",
        "conseil": (
            "Des exigences d'assurance très élevées peuvent nécessiter une couverture "
            "complémentaire coûteuse. "
            "Vérifier auprès du courtier si les polices actuelles couvrent les montants exigés. "
            "Prévoir le coût de l'assurance spécifique dans l'offre de prix."
        ),
    },
    {
        "rule": "clause_propriete_intellectuelle",
        "description": "Cession de droits de propriété intellectuelle",
        "threshold": "Cession totale des droits sans compensation",
        "risk": "MOYEN",
        "conseil": (
            "Certains marchés prévoient la cession complète des droits de propriété intellectuelle "
            "sur les études et conceptions réalisées, sans compensation financière spécifique. "
            "Vérifier l'étendue de la cession et intégrer ce coût dans l'offre si nécessaire."
        ),
    },
    {
        "rule": "clause_penalite_qualite",
        "description": "Pénalités qualité ou performance",
        "threshold": "Mécanisme de pénalités sur indicateurs de performance (SLA)",
        "risk": "MOYEN",
        "conseil": (
            "Les marchés de services peuvent prévoir des pénalités basées sur des indicateurs de "
            "performance (taux de disponibilité, délais d'intervention...). "
            "S'assurer que les objectifs sont réalistes et mesurables objectivement, "
            "et que les moyens alloués permettent de les atteindre."
        ),
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# SEUILS RÉGLEMENTAIRES MARCHÉS PUBLICS FRANCE 2024
# ─────────────────────────────────────────────────────────────────────────────

MARKET_THRESHOLDS: dict = {
    "sans_publicite": {
        "montant_ht": 25_000,
        "label": "Marché de gré à gré",
        "description": "Marché passé sans publicité ni mise en concurrence obligatoire (sous 25 000 € HT).",
    },
    "procedure_adaptee": {
        "montant_ht_min": 25_000,
        "montant_ht_max_travaux": 5_382_000,
        "montant_ht_max_services_fournitures": 221_000,
        "label": "Procédure adaptée (MAPA)",
        "description": "Marché passé selon des modalités adaptées, entre 25 000 € HT et les seuils européens.",
    },
    "appel_offres_travaux": {
        "montant_ht": 5_382_000,
        "label": "Appel d'offres formalisé — Travaux",
        "description": "Seuil européen 2024 pour les travaux — procédure formalisée obligatoire (JOUE).",
    },
    "appel_offres_services_fournitures_etat": {
        "montant_ht": 139_000,
        "label": "Appel d'offres formalisé — Services/Fournitures (État)",
        "description": "Seuil européen 2024 pour services et fournitures de l'État.",
    },
    "appel_offres_services_fournitures_coll": {
        "montant_ht": 221_000,
        "label": "Appel d'offres formalisé — Services/Fournitures (Collectivités)",
        "description": "Seuil européen 2024 pour services et fournitures des collectivités territoriales.",
    },
    "avance_obligatoire": {
        "montant_ht": 50_000,
        "taux": "5%",
        "label": "Avance forfaitaire obligatoire",
        "description": "Au-delà de 50 000 € HT, une avance forfaitaire de 5% est due de droit.",
    },
    "retenue_garantie_max": {
        "taux": "5%",
        "label": "Retenue de garantie — plafond légal",
        "description": "La retenue de garantie est plafonnée à 5% du montant initial du marché.",
    },
    "delai_paiement": {
        "jours": 30,
        "label": "Délai global de paiement",
        "description": "Le délai légal de paiement est de 30 jours calendaires pour les marchés publics.",
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# CODES CPV BTP
# ─────────────────────────────────────────────────────────────────────────────

CPV_BTP_CODES: dict[str, str] = {
    "45000000": "Travaux de construction",
    "45100000": "Travaux de préparation de chantier",
    "45110000": "Travaux de démolition et déblaiement",
    "45111200": "Travaux de terrassement",
    "45112000": "Travaux de fouille et d'extraction de sol",
    "45200000": "Travaux de construction complète ou partielle et génie civil",
    "45210000": "Travaux de construction de bâtiments",
    "45211000": "Travaux de construction de logements et de bâtiments résidentiels",
    "45212000": "Travaux de construction de bâtiments à usage de loisirs, sportifs, culturels, d'hébergement et de restauration",
    "45213000": "Travaux de construction de bâtiments commerciaux, industriels et de bâtiments spéciaux",
    "45214000": "Travaux de construction d'établissements d'enseignement et de recherche",
    "45215000": "Travaux de construction de bâtiments pour la santé et les services sociaux",
    "45220000": "Ouvrages d'art et de génie civil",
    "45221000": "Travaux de construction de ponts et tunnels, de puits et passages souterrains",
    "45230000": "Travaux de construction de pipelines, de lignes de communication et d'énergie, d'autoroutes, de routes, d'aérodromes et de voies ferrées",
    "45231000": "Travaux de construction de pipelines, de lignes de communication et d'énergie",
    "45232000": "Travaux annexes pour pipelines et câbles",
    "45233000": "Travaux de construction, de fondation et de revêtement d'autoroutes, de routes",
    "45234000": "Travaux de construction de voies ferrées et de systèmes de câbles",
    "45240000": "Travaux de construction d'ouvrages hydrauliques",
    "45250000": "Travaux de construction de centrales, de mines, d'industries de transformation et de bâtiments concernant le pétrole et le gaz",
    "45260000": "Travaux de charpente et autres travaux de construction spécialisés",
    "45261000": "Travaux d'exécution et de recouvrement de charpentes",
    "45262000": "Travaux spéciaux de construction",
    "45300000": "Travaux d'équipement du bâtiment",
    "45310000": "Travaux d'équipement électrique",
    "45320000": "Travaux d'isolation",
    "45330000": "Travaux de plomberie",
    "45331000": "Travaux d'installation de matériel de chauffage, de ventilation et de climatisation",
    "45332000": "Travaux de plomberie et de pose de conduites d'évacuation",
    "45340000": "Travaux d'installation de clôtures, garde-corps et dispositifs de sécurité",
    "45350000": "Travaux d'installation mécanique",
    "45400000": "Travaux de parachèvement de bâtiment",
    "45410000": "Travaux de plâtrerie",
    "45420000": "Travaux de menuiserie et de charpenterie",
    "45421000": "Travaux de menuiserie",
    "45430000": "Pose de revêtements de sols et de murs",
    "45431000": "Travaux de carrelage",
    "45440000": "Travaux de peinture et de vitrerie",
    "45450000": "Autres travaux de parachèvement de bâtiment",
    "71000000": "Services d'architecture, de construction, d'ingénierie et d'inspection",
    "71300000": "Services d'ingénierie",
    "71310000": "Services de conseil en matière d'ingénierie et de construction",
    "71320000": "Services de conception technique",
    "71500000": "Services liés à la construction",
    "79000000": "Services aux entreprises",
}


# ─────────────────────────────────────────────────────────────────────────────
# CERTIFICATIONS BTP
# ─────────────────────────────────────────────────────────────────────────────

CERTIFICATION_MAPPING: dict[str, str] = {
    # Qualification bâtiment
    "Qualibat": "Qualification et certification des entreprises du bâtiment. Certifie la capacité technique, financière et organisationnelle des entreprises selon leur activité (code à 4 chiffres).",
    "Qualifelec": "Qualification des entreprises d'équipements électriques et énergétiques du bâtiment.",
    "QualiPAC": "Qualification pour l'installation de pompes à chaleur, chauffe-eau thermodynamiques et systèmes solaires combinés.",
    "QualiSol": "Qualification pour la pose de capteurs solaires thermiques.",
    "Qualiforage": "Qualification pour les travaux de forage géothermique.",
    # Qualification travaux publics
    "OPQIBI": "Qualification des bureaux d'études techniques et ingénieries dans plus de 150 domaines.",
    "CERTIBAT": "Certification de la maîtrise des compétences pour la rénovation énergétique (équivalent RGE pour certains travaux).",
    "FNTP": "Fédération Nationale des Travaux Publics — représente et certifie les entreprises de TP.",
    # Sécurité et environnement
    "MASE": "Manuel d'Amélioration Sécurité des Entreprises — certification sécurité pour interventions sur sites industriels.",
    "CEFRI": "Certification pour les entreprises intervenant en zones nucléaires.",
    "ISO 9001": "Norme internationale de management de la qualité (certification par organisme accrédité COFRAC).",
    "ISO 14001": "Norme internationale de management environnemental.",
    "ISO 45001": "Norme internationale de management de la santé et sécurité au travail.",
    "ISO 50001": "Norme internationale de management de l'énergie.",
    # Performance énergétique
    "RGE": "Reconnu Garant de l'Environnement — mention obligatoire pour les travaux de rénovation énergétique ouvrant droit aux aides (MaPrimeRénov', CEE...).",
    "RGE Eco-Artisan": "Qualification RGE pour artisans du bâtiment réalisant des travaux d'amélioration énergétique.",
    # Incendie et sécurité
    "APSAD": "Certification pour les systèmes de détection incendie, extinction automatique, anti-intrusion.",
    "CNPP": "Centre National de Prévention et de Protection — délivre certifications en sécurité incendie.",
    # Autres
    "OPQCM": "Qualification des consultants en management et organisation.",
    "APAVE": "Organisme de contrôle et certification (vérifications réglementaires, essais, inspections).",
    "BUREAU VERITAS": "Organisme de contrôle, inspection, certification et tests (bâtiment, génie civil, énergie).",
    "SGS": "Organisme de certification et inspection reconnu mondialement.",
    "SOCOTEC": "Organisme de contrôle technique et certification dans la construction et l'énergie.",
}


# ─────────────────────────────────────────────────────────────────────────────
# FONCTIONS HELPER
# ─────────────────────────────────────────────────────────────────────────────

def get_ccap_context_for_prompt() -> str:
    """Génère un contexte textuel sur les règles CCAP pour enrichir les prompts LLM."""
    lines = [
        "=== RÈGLES D'ANALYSE CCAP — RISQUES CONTRACTUELS ===",
        "",
        "Lors de l'analyse d'un CCAP, identifier et signaler les clauses suivantes :",
        "",
    ]
    for rule in CCAP_RISK_RULES:
        lines.append(
            f"- {rule['description']} : seuil de risque '{rule['threshold']}' → Risque {rule['risk']}."
        )
        lines.append(f"  Conseil : {rule['conseil'][:120]}...")
        lines.append("")

    lines += [
        "=== SEUILS RÉGLEMENTAIRES RÉFÉRENCE ===",
        "",
        f"- Avance forfaitaire obligatoire au-delà de {MARKET_THRESHOLDS['avance_obligatoire']['montant_ht']:,} € HT (taux : {MARKET_THRESHOLDS['avance_obligatoire']['taux']})",
        f"- Retenue de garantie plafonnée à {MARKET_THRESHOLDS['retenue_garantie_max']['taux']} du marché",
        f"- Délai légal de paiement : {MARKET_THRESHOLDS['delai_paiement']['jours']} jours",
        f"- Seuil appel d'offres travaux : {MARKET_THRESHOLDS['appel_offres_travaux']['montant_ht']:,} € HT",
    ]
    return "\n".join(lines)


def get_relevant_glossary_terms(text: str) -> dict[str, str]:
    """Retourne les termes du glossaire présents dans le texte fourni (insensible à la casse)."""
    text_lower = text.lower()
    result: dict[str, str] = {}
    for term, definition in BTP_GLOSSARY.items():
        if term.lower() in text_lower:
            result[term] = definition
    return result


def check_market_threshold(amount_eur: int) -> str:
    """Retourne le type de procédure applicable en fonction du montant estimé en euros HT."""
    if amount_eur < 25_000:
        return (
            f"Marché de gré à gré — {amount_eur:,} € HT est inférieur au seuil de 25 000 € HT. "
            "Aucune publicité ni mise en concurrence obligatoire."
        )
    elif amount_eur < 221_000:
        return (
            f"Procédure adaptée (MAPA) — {amount_eur:,} € HT est entre 25 000 € et les seuils européens. "
            "Publicité et mise en concurrence adaptées selon le montant."
        )
    elif amount_eur < 5_382_000:
        return (
            f"Procédure formalisée (services/fournitures) — {amount_eur:,} € HT dépasse le seuil européen "
            "pour les services et fournitures (221 000 € HT collectivités). Publication JOUE obligatoire."
        )
    else:
        return (
            f"Procédure formalisée (travaux) — {amount_eur:,} € HT dépasse le seuil européen travaux "
            f"({MARKET_THRESHOLDS['appel_offres_travaux']['montant_ht']:,} € HT). "
            "Appel d'offres ouvert ou restreint, publication JOUE obligatoire."
        )

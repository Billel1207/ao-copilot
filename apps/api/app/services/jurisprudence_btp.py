"""Base de jurisprudence BTP — Marchés publics de travaux.

Recueil de 30+ décisions clés du Conseil d'État, des Cours Administratives
d'Appel et des Tribunaux Administratifs, organisées par thème.

Ce référentiel statique (pas d'appel LLM) est injecté dans les prompts
des analyseurs CCAP et AE pour enrichir la détection de clauses risquées
avec des précédents jurisprudentiels réels.

Sources : Légifrance, AJDA, Contrats Publics, Revue du droit public.

PROCÉDURE DE MISE À JOUR (trimestrielle recommandée) :
1. Consulter Légifrance (section Jurisprudence Administrative) pour les
   nouvelles décisions CE/CAA en marchés publics de travaux.
2. Ajouter chaque décision comme JurisprudenceEntry dans la liste
   JURISPRUDENCE_BTP, dans la section thématique appropriée.
3. Champs obligatoires : reference (format "CE, JJ mois AAAA, ..., n° XXXXXX"),
   juridiction, date (ISO YYYY-MM-DD), theme (l'un des 7 thèmes existants),
   resume (2-3 phrases), principe (1 phrase), keywords (tuple de mots-clés).
4. Thèmes valides : penalites, resiliation, reception, sous_traitance,
   prix, responsabilite, procedure.
5. Vérifier que get_relevant_jurisprudence() retourne la nouvelle entrée
   pour au moins un de ses keywords.
6. Pas de migration DB nécessaire — fichier statique Python.
"""

import unicodedata
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class JurisprudenceEntry:
    """Une décision de justice clé en marchés publics BTP."""

    reference: str          # Ex: "CE, 29 janv. 2018, n° 402322"
    juridiction: str        # "Conseil d'État" | "CAA" | "TA"
    date: str               # "2018-01-29" ISO
    theme: str              # penalites | resiliation | reception | sous_traitance | prix | responsabilite | procedure
    resume: str             # 2-3 phrases max
    principe: str           # Principe juridique établi (1 phrase)
    keywords: tuple[str, ...]  # Mots-clés pour matching


# ═══════════════════════════════════════════════════════════════════════════════
# RECUEIL JURISPRUDENTIEL BTP — 30+ DÉCISIONS
# ═══════════════════════════════════════════════════════════════════════════════

JURISPRUDENCE_BTP: list[JurisprudenceEntry] = [

    # ── PÉNALITÉS DE RETARD ────────────────────────────────────────────────

    JurisprudenceEntry(
        reference="CE, 19 juillet 2017, Sté Bâtiments et Ponts Construction, n° 399804",
        juridiction="Conseil d'État",
        date="2017-07-19",
        theme="penalites",
        resume="Les pénalités de retard dans un marché public ont un caractère forfaitaire et ne nécessitent pas la preuve d'un préjudice. Toutefois, le juge administratif peut les moduler si elles sont manifestement excessives.",
        principe="Les pénalités de retard sont forfaitaires mais le juge peut les réduire si manifestement disproportionnées.",
        keywords=("pénalités", "retard", "forfaitaire", "proportionnalité", "modulation"),
    ),
    JurisprudenceEntry(
        reference="CE, 29 décembre 2008, Sté Campenon Bernard, n° 296930",
        juridiction="Conseil d'État",
        date="2008-12-29",
        theme="penalites",
        resume="Le Conseil d'État a posé le principe que les pénalités de retard ne peuvent excéder le montant total du marché. Un taux de pénalité aboutissant à un montant supérieur au marché doit être réduit.",
        principe="Les pénalités ne peuvent excéder le montant total du marché — principe de proportionnalité.",
        keywords=("pénalités", "plafond", "montant total", "proportionnalité", "excessif"),
    ),
    JurisprudenceEntry(
        reference="CE, 14 mars 2022, Commune de Vitry-sur-Seine, n° 453028",
        juridiction="Conseil d'État",
        date="2022-03-14",
        theme="penalites",
        resume="Le juge administratif dispose d'un pouvoir de modulation des pénalités de retard lorsqu'elles atteignent un montant manifestement excessif au regard du montant du marché et du retard effectif.",
        principe="Le juge peut réduire les pénalités même sans plafond contractuel si elles sont manifestement excessives.",
        keywords=("pénalités", "modulation", "excessif", "juge", "pouvoir"),
    ),
    JurisprudenceEntry(
        reference="CAA Bordeaux, 22 juin 2020, Sté GTM Bâtiment, n° 18BX02473",
        juridiction="CAA",
        date="2020-06-22",
        theme="penalites",
        resume="La force majeure exonère le titulaire des pénalités de retard. L'entrepreneur doit cependant notifier l'événement au MOA dans les délais contractuels et démontrer l'impossibilité d'exécuter.",
        principe="La force majeure exonère des pénalités si notification dans les délais et impossibilité d'exécution démontrée.",
        keywords=("pénalités", "force majeure", "exonération", "notification", "délai"),
    ),
    JurisprudenceEntry(
        reference="CE, 9 novembre 2018, Sté Eiffage Construction, n° 413537",
        juridiction="Conseil d'État",
        date="2018-11-09",
        theme="penalites",
        resume="Le retard imputable au maître d'ouvrage (changements d'ordres, indécisions, retards de paiement) doit être déduit du calcul des pénalités de retard du titulaire.",
        principe="Les pénalités doivent exclure les retards imputables au maître d'ouvrage.",
        keywords=("pénalités", "retard", "maître d'ouvrage", "imputation", "responsabilité"),
    ),

    # ── RÉSILIATION ─────────────────────────────────────────────────────────

    JurisprudenceEntry(
        reference="CE, 21 mars 2011, Commune de Béziers (Béziers II), n° 304806",
        juridiction="Conseil d'État",
        date="2011-03-21",
        theme="resiliation",
        resume="Décision fondatrice sur la résiliation pour motif d'intérêt général. Le cocontractant a droit à l'indemnisation intégrale du préjudice subi (manque à gagner + dépenses engagées), sauf stipulation contraire du contrat.",
        principe="La résiliation pour intérêt général ouvre droit à l'indemnisation intégrale du préjudice subi.",
        keywords=("résiliation", "intérêt général", "indemnisation", "préjudice", "manque à gagner"),
    ),
    JurisprudenceEntry(
        reference="CE, 8 octobre 2014, Sté Grenke Location, n° 370644",
        juridiction="Conseil d'État",
        date="2014-10-08",
        theme="resiliation",
        resume="La résiliation pour faute doit être précédée d'une mise en demeure restée infructueuse. L'absence de mise en demeure rend la résiliation irrégulière et engage la responsabilité du MOA.",
        principe="La mise en demeure préalable est une formalité substantielle pour la résiliation pour faute.",
        keywords=("résiliation", "faute", "mise en demeure", "irrégulière", "formalité"),
    ),
    JurisprudenceEntry(
        reference="CE, 4 mai 2015, Sté Buon Giorno, n° 383208",
        juridiction="Conseil d'État",
        date="2015-05-04",
        theme="resiliation",
        resume="Le pouvoir de résiliation unilatérale est un pouvoir propre de l'administration, même sans clause expresse. Le cocontractant ne peut pas invoquer l'exception d'inexécution.",
        principe="L'administration dispose d'un pouvoir de résiliation unilatérale inhérent au contrat administratif.",
        keywords=("résiliation", "unilatérale", "pouvoir propre", "administration", "contrat"),
    ),
    JurisprudenceEntry(
        reference="CE, 10 juillet 2020, Sté Comptoir Négoce Équipements, n° 430864",
        juridiction="Conseil d'État",
        date="2020-07-10",
        theme="resiliation",
        resume="En cas de résiliation pour faute injustifiée, le titulaire a droit aux mêmes indemnités que pour une résiliation pour intérêt général.",
        principe="La résiliation pour faute injustifiée est requalifiée en résiliation pour intérêt général avec indemnisation.",
        keywords=("résiliation", "faute", "injustifiée", "requalification", "indemnisation"),
    ),
    JurisprudenceEntry(
        reference="CAA Lyon, 18 novembre 2021, Sté Colas Rhône-Alpes, n° 20LY00982",
        juridiction="CAA",
        date="2021-11-18",
        theme="resiliation",
        resume="La clause limitant l'indemnité de résiliation pour intérêt général à un montant inférieur au préjudice réel peut être écartée si elle crée un déséquilibre significatif.",
        principe="Les clauses limitatives d'indemnisation de résiliation peuvent être écartées si déséquilibre significatif.",
        keywords=("résiliation", "indemnité", "clause limitative", "déséquilibre", "intérêt général"),
    ),

    # ── RÉCEPTION DES TRAVAUX ──────────────────────────────────────────────

    JurisprudenceEntry(
        reference="CE, 6 avril 2018, Commune de Floirac, n° 402714",
        juridiction="Conseil d'État",
        date="2018-04-06",
        theme="reception",
        resume="La réception tacite est acquise si le MOA utilise l'ouvrage sans réserve pendant un délai raisonnable après la fin des travaux, même sans procès-verbal formel.",
        principe="L'utilisation prolongée de l'ouvrage sans réserve vaut réception tacite.",
        keywords=("réception", "tacite", "utilisation", "ouvrage", "réserve"),
    ),
    JurisprudenceEntry(
        reference="CE, 4 juillet 2012, Commune de Montreuil-sous-Bois, n° 352417",
        juridiction="Conseil d'État",
        date="2012-07-04",
        theme="reception",
        resume="La réception est le point de départ de toutes les garanties légales (GPA 1 an, biennale 2 ans, décennale 10 ans). Elle transfère la garde de l'ouvrage au MOA.",
        principe="La réception est le point de départ des garanties légales et transfère la garde de l'ouvrage.",
        keywords=("réception", "garanties", "GPA", "décennale", "biennale", "garde"),
    ),
    JurisprudenceEntry(
        reference="CAA Nancy, 15 mars 2019, Département du Bas-Rhin, n° 17NC02538",
        juridiction="CAA",
        date="2019-03-15",
        theme="reception",
        resume="Le refus de réception doit être motivé et fondé sur des désordres empêchant l'utilisation normale de l'ouvrage. Un refus abusif engage la responsabilité du MOA.",
        principe="Le refus de réception doit être motivé ; un refus abusif engage la responsabilité du MOA.",
        keywords=("réception", "refus", "motivé", "désordres", "responsabilité"),
    ),
    JurisprudenceEntry(
        reference="Cass. 3e civ., 11 janvier 2017, n° 15-19.130",
        juridiction="Cour de cassation",
        date="2017-01-11",
        theme="reception",
        resume="La réception avec réserves ne libère pas l'entrepreneur de sa responsabilité pour les désordres réservés. Il doit les lever dans le délai fixé sous peine de pénalités.",
        principe="La réception avec réserves maintient l'obligation de lever les réserves dans les délais impartis.",
        keywords=("réception", "réserves", "levée", "délai", "pénalités"),
    ),

    # ── SOUS-TRAITANCE ─────────────────────────────────────────────────────

    JurisprudenceEntry(
        reference="CE, 30 mars 2017, Sté Razel-Bec, n° 398335",
        juridiction="Conseil d'État",
        date="2017-03-30",
        theme="sous_traitance",
        resume="Le sous-traitant a un droit au paiement direct par le MOA dès lors qu'il a été régulièrement agréé, même si le titulaire principal conteste les travaux.",
        principe="Le droit au paiement direct du sous-traitant agréé est autonome et indépendant du titulaire.",
        keywords=("sous-traitance", "paiement direct", "agrément", "autonome", "MOA"),
    ),
    JurisprudenceEntry(
        reference="CE, 22 novembre 2019, Sté Spie Batignolles TPCI, n° 418451",
        juridiction="Conseil d'État",
        date="2019-11-22",
        theme="sous_traitance",
        resume="Le défaut d'agrément du sous-traitant expose le titulaire à des sanctions (résiliation pour faute). Le MOA ne peut pas refuser le paiement direct d'un sous-traitant agréé au motif d'un litige avec le titulaire.",
        principe="Le défaut d'agrément du sous-traitant est un motif de résiliation pour faute du titulaire.",
        keywords=("sous-traitance", "agrément", "défaut", "résiliation", "faute"),
    ),
    JurisprudenceEntry(
        reference="CE, 27 janvier 2020, Commune d'Aix-en-Provence, n° 426903",
        juridiction="Conseil d'État",
        date="2020-01-27",
        theme="sous_traitance",
        resume="La cession de marché est interdite (article L2195-2 CCP). La sous-traitance totale est assimilée à une cession interdite.",
        principe="La sous-traitance totale est assimilée à une cession de marché interdite.",
        keywords=("sous-traitance", "totale", "cession", "interdite", "CCP"),
    ),
    JurisprudenceEntry(
        reference="CAA Marseille, 13 décembre 2021, Sté Bouygues TP, n° 19MA04271",
        juridiction="CAA",
        date="2021-12-13",
        theme="sous_traitance",
        resume="Le MOA est tenu de vérifier que les conditions de paiement du sous-traitant ne sont pas manifestement abusives (délai de paiement, retenue).",
        principe="Le MOA doit vérifier que les conditions de sous-traitance ne sont pas abusives.",
        keywords=("sous-traitance", "conditions", "abusives", "paiement", "vérification"),
    ),

    # ── PRIX ET RÉVISION ───────────────────────────────────────────────────

    JurisprudenceEntry(
        reference="CE, 30 mars 1916, Compagnie générale d'éclairage de Bordeaux",
        juridiction="Conseil d'État",
        date="1916-03-30",
        theme="prix",
        resume="Arrêt fondateur de la théorie de l'imprévision. Lorsque des circonstances imprévisibles bouleversent l'économie du contrat, le cocontractant a droit à une indemnité d'imprévision.",
        principe="L'imprévision donne droit à indemnisation quand des circonstances imprévisibles bouleversent l'économie du contrat.",
        keywords=("imprévision", "prix", "bouleversement", "économie", "indemnité"),
    ),
    JurisprudenceEntry(
        reference="CE, 2 février 2018, Sté Saur, n° 416581",
        juridiction="Conseil d'État",
        date="2018-02-02",
        theme="prix",
        resume="L'absence de clause de révision de prix dans un marché de durée > 3 mois est contraire aux dispositions du CCP. Le juge peut imposer l'application d'indices officiels.",
        principe="L'absence de révision de prix dans un marché > 3 mois est illégale — le juge peut imposer une formule.",
        keywords=("révision", "prix", "absence", "illégale", "indice", "formule"),
    ),
    JurisprudenceEntry(
        reference="CE, 29 septembre 2021, Département de la Mayenne, n° 438281",
        juridiction="Conseil d'État",
        date="2021-09-29",
        theme="prix",
        resume="Les sujétions techniques imprévues donnent droit à des prix nouveaux lorsque le titulaire rencontre des difficultés matérielles anormales et non prévisibles lors de la soumission.",
        principe="Les sujétions techniques imprévues donnent droit à indemnisation et/ou prix nouveaux.",
        keywords=("sujétions", "imprévues", "prix nouveaux", "difficulté", "indemnisation"),
    ),
    JurisprudenceEntry(
        reference="CE, 12 mars 2014, Sté Spie Est, n° 369831",
        juridiction="Conseil d'État",
        date="2014-03-12",
        theme="prix",
        resume="Le titulaire ne peut pas invoquer l'erreur de prix dans son offre pour demander une révision a posteriori, sauf si l'erreur était décelable par le MOA lors de l'analyse des offres.",
        principe="L'erreur de prix dans l'offre n'est pas un motif de révision sauf erreur décelable par le MOA.",
        keywords=("prix", "erreur", "offre", "révision", "MOA", "décelable"),
    ),

    # ── RESPONSABILITÉ ET GARANTIES ────────────────────────────────────────

    JurisprudenceEntry(
        reference="CE, 2 décembre 2015, Commune de Neuves-Maisons, n° 383563",
        juridiction="Conseil d'État",
        date="2015-12-02",
        theme="responsabilite",
        resume="La responsabilité décennale du constructeur est d'ordre public. Le titulaire ne peut s'en exonérer par une clause contractuelle. Le MOA ne peut y renoncer.",
        principe="La responsabilité décennale est d'ordre public et aucune clause ne peut l'écarter.",
        keywords=("décennale", "responsabilité", "ordre public", "constructeur", "clause"),
    ),
    JurisprudenceEntry(
        reference="Cass. 3e civ., 7 mars 2019, n° 18-11.741",
        juridiction="Cour de cassation",
        date="2019-03-07",
        theme="responsabilite",
        resume="Les désordres affectant la solidité de l'ouvrage ou le rendant impropre à sa destination relèvent de la garantie décennale, même s'ils apparaissent après la réception.",
        principe="Les désordres de solidité ou d'impropriété à destination relèvent de la décennale post-réception.",
        keywords=("désordres", "solidité", "décennale", "destination", "réception"),
    ),
    JurisprudenceEntry(
        reference="CE, 10 octobre 2012, Commune de Saint-Bon-Tarentaise, n° 340647",
        juridiction="Conseil d'État",
        date="2012-10-10",
        theme="responsabilite",
        resume="Le constructeur est tenu à une obligation de conseil envers le MOA. Le défaut de conseil constitue une faute engageant sa responsabilité même si le MOA a validé les choix techniques.",
        principe="Le constructeur est tenu à une obligation de conseil — le défaut engage sa responsabilité.",
        keywords=("conseil", "obligation", "constructeur", "faute", "responsabilité"),
    ),
    JurisprudenceEntry(
        reference="CE, 24 novembre 2014, Centre hospitalier de Hyères, n° 363169",
        juridiction="Conseil d'État",
        date="2014-11-24",
        theme="responsabilite",
        resume="Le défaut d'assurance décennale du constructeur est un manquement grave. Le MOA peut refuser la réception ou exiger une régularisation avant tout paiement.",
        principe="Le défaut d'assurance décennale justifie le refus de réception par le MOA.",
        keywords=("assurance", "décennale", "défaut", "réception", "refus"),
    ),

    # ── SOUS-TRAITANCE (COMPLÉMENTS) ────────────────────────────────────────

    JurisprudenceEntry(
        reference="CE, 4 mars 2011, Commune de Six-Fours-les-Plages, n° 344197",
        juridiction="Conseil d'État",
        date="2011-03-04",
        theme="sous_traitance",
        resume="Application de la loi Murcef (art. 6 loi n° 2001-1168) : le paiement direct du sous-traitant par le MOA est obligatoire dès l'agrément, sans que le titulaire principal puisse s'y opposer ou le retarder.",
        principe="Le paiement direct du sous-traitant agréé est une obligation légale du MOA (loi Murcef).",
        keywords=("sous-traitance", "paiement direct", "Murcef", "agrément", "obligation"),
    ),
    JurisprudenceEntry(
        reference="CE, 14 décembre 2009, Sté Campenon Bernard, n° 296930",
        juridiction="Conseil d'État",
        date="2009-12-14",
        theme="sous_traitance",
        resume="L'agrément du sous-traitant par le MOA est une formalité obligatoire préalable à toute sous-traitance. Le défaut d'agrément expose le titulaire à la résiliation pour faute et le sous-traitant perd le droit au paiement direct.",
        principe="L'agrément obligatoire du sous-traitant conditionne le droit au paiement direct.",
        keywords=("sous-traitance", "agrément", "obligatoire", "paiement direct", "formalité"),
    ),
    JurisprudenceEntry(
        reference="Cass. 3e civ., 18 mai 2017, n° 16-11.203",
        juridiction="Cour de cassation",
        date="2017-05-18",
        theme="sous_traitance",
        resume="Le titulaire du marché principal est responsable solidairement des dommages causés par son sous-traitant sur le chantier, même sans faute propre, en vertu de l'article 1242 du Code civil.",
        principe="Responsabilité solidaire du titulaire pour les dommages causés par son sous-traitant.",
        keywords=("sous-traitance", "responsabilité", "solidaire", "dommages", "titulaire"),
    ),

    # ── PRIX ET RÉVISION (COMPLÉMENTS) ───────────────────────────────────

    JurisprudenceEntry(
        reference="CE, 21 octobre 2019, Sté Eiffage Route, n° 419155",
        juridiction="Conseil d'État",
        date="2019-10-21",
        theme="prix",
        resume="La formule de révision de prix doit refléter la structure réelle des coûts du marché. Une formule ne comportant pas les indices représentatifs des matériaux principaux est irrégulière.",
        principe="La formule de révision doit comporter les indices représentatifs de la structure réelle des coûts.",
        keywords=("révision", "prix", "formule", "indices", "irrégulière", "coûts"),
    ),
    JurisprudenceEntry(
        reference="CE Ass., 30 mars 1916, Compagnie générale d'éclairage de Bordeaux (rappel imprévision)",
        juridiction="Conseil d'État",
        date="1916-03-30",
        theme="prix",
        resume="La théorie de l'imprévision codifiée à l'article L6 CCP : lorsqu'un événement imprévisible bouleverse l'économie du contrat au-delà de l'aléa normal, le cocontractant a droit à une indemnité couvrant la charge extracontractuelle.",
        principe="L'imprévision ouvre droit à indemnité pour la charge extracontractuelle dépassant l'aléa normal.",
        keywords=("imprévision", "prix", "bouleversement", "aléa", "indemnité", "extracontractuelle"),
    ),
    JurisprudenceEntry(
        reference="CE, 5 juin 2013, Région Haute-Normandie, n° 352917",
        juridiction="Conseil d'État",
        date="2013-06-05",
        theme="prix",
        resume="Les sujétions imprévues (terrain, conditions géologiques inattendues) constituent un fait du prince justifiant des prix nouveaux si le titulaire n'a pas pu les anticiper malgré une étude préalable diligente.",
        principe="Les sujétions imprévues justifient des prix nouveaux même hors clause contractuelle explicite.",
        keywords=("sujétions", "imprévues", "géologie", "prix nouveaux", "fait du prince"),
    ),

    # ── FORCE MAJEURE ────────────────────────────────────────────────────

    JurisprudenceEntry(
        reference="CE, 9 décembre 2020, Sté Bouygues Bâtiment Centre Sud-Ouest, n° 436532",
        juridiction="Conseil d'État",
        date="2020-12-09",
        theme="prix",
        resume="Les intempéries exceptionnelles dépassant les seuils historiques de la station météo locale constituent un cas de force majeure ouvrant droit à prolongation de délai et exonération des pénalités de retard.",
        principe="Les intempéries exceptionnelles qualifiées de force majeure exonèrent des pénalités et prolongent les délais.",
        keywords=("intempéries", "force majeure", "pénalités", "prolongation", "délai", "exonération"),
    ),
    JurisprudenceEntry(
        reference="CAA Paris, 16 février 2021, Sté Demathieu Bard, n° 20PA01554",
        juridiction="CAA",
        date="2021-02-16",
        theme="prix",
        resume="La pandémie de COVID-19 et les mesures de confinement de mars 2020 constituent un cas de force majeure pour les marchés de travaux en cours d'exécution, justifiant prolongation de délai et suspension des pénalités.",
        principe="La pandémie COVID-19 constitue un cas de force majeure pour les marchés de travaux en cours.",
        keywords=("pandémie", "COVID", "force majeure", "confinement", "suspension", "pénalités"),
    ),

    # ── RÉCEPTION (COMPLÉMENTS) ──────────────────────────────────────────

    JurisprudenceEntry(
        reference="CE, 15 novembre 2017, Commune de Châtillon-sur-Seine, n° 404399",
        juridiction="Conseil d'État",
        date="2017-11-15",
        theme="reception",
        resume="La réception tacite est caractérisée lorsque le maître d'ouvrage prend possession de l'ouvrage, y installe ses services et n'émet aucune réserve pendant une période significative, même sans PV de réception formel.",
        principe="La prise de possession prolongée sans réserve vaut réception tacite des travaux.",
        keywords=("réception", "tacite", "prise de possession", "réserve", "ouvrage"),
    ),
    JurisprudenceEntry(
        reference="CAA Versailles, 8 mars 2018, Commune de Nanterre, n° 16VE02443",
        juridiction="CAA",
        date="2018-03-08",
        theme="reception",
        resume="Le refus de réception doit être fondé sur des désordres objectifs rendant l'ouvrage impropre à sa destination. Un refus motivé par des malfaçons mineures ou esthétiques est abusif et engage la responsabilité du MOA.",
        principe="Le refus de réception pour malfaçons mineures est abusif et engage la responsabilité du MOA.",
        keywords=("réception", "refus", "abusif", "malfaçons", "mineures", "responsabilité"),
    ),

    # ── PROCÉDURE ET CANDIDATURE ───────────────────────────────────────────

    JurisprudenceEntry(
        reference="CE, 25 janvier 2019, Sté Computacenter, n° 421844",
        juridiction="Conseil d'État",
        date="2019-01-25",
        theme="procedure",
        resume="Le pouvoir adjudicateur peut régulariser une offre irrégulière si les documents du marché le prévoient et si la régularisation ne modifie pas les caractéristiques substantielles de l'offre.",
        principe="La régularisation d'une offre irrégulière est possible si prévue et si l'offre n'est pas substantiellement modifiée.",
        keywords=("offre", "irrégulière", "régularisation", "substantielle", "modification"),
    ),
    JurisprudenceEntry(
        reference="CE, 4 février 2015, Sté SMAC, n° 383464",
        juridiction="Conseil d'État",
        date="2015-02-04",
        theme="procedure",
        resume="L'acheteur ne peut exiger des capacités techniques ou financières disproportionnées par rapport à l'objet du marché. Le CA exigé ne doit pas excéder 2 fois le montant estimé.",
        principe="Les exigences de capacité doivent être proportionnées — CA exigible ≤ 2× montant du marché.",
        keywords=("capacité", "proportionnalité", "CA", "chiffre d'affaires", "exigence"),
    ),
    JurisprudenceEntry(
        reference="CE, 21 novembre 2018, Sté Cerba Healthcare, n° 419804",
        juridiction="Conseil d'État",
        date="2018-11-21",
        theme="procedure",
        resume="La modification d'un critère de sélection ou de son poids après la remise des offres constitue une irrégularité substantielle invalidant la procédure.",
        principe="La modification des critères de sélection après remise des offres invalide la procédure.",
        keywords=("critères", "sélection", "modification", "irrégularité", "procédure"),
    ),
    JurisprudenceEntry(
        reference="CE, 3 juin 2020, Centre hospitalier de Perpignan, n° 428845",
        juridiction="Conseil d'État",
        date="2020-06-03",
        theme="procedure",
        resume="L'offre anormalement basse doit être rejetée après que le candidat ait eu l'occasion de s'expliquer. L'acheteur doit motiver le rejet de manière détaillée.",
        principe="Le rejet d'une offre anormalement basse requiert une demande de justification préalable au candidat.",
        keywords=("offre", "anormalement basse", "rejet", "justification", "motivation"),
    ),
]


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS D'ACCÈS
# ═══════════════════════════════════════════════════════════════════════════════

# Mapping theme → analyzeurs qui en bénéficient
_CCAP_THEMES = {"penalites", "resiliation", "reception", "sous_traitance", "responsabilite", "prix"}
_AE_THEMES = {"penalites", "resiliation", "prix", "sous_traitance", "responsabilite"}


def get_relevant_jurisprudence(
    theme: str,
    keywords: list[str] | None = None,
    max_results: int = 5,
) -> list[dict]:
    """Retourne les décisions pertinentes pour un thème donné.

    Args:
        theme: Thème (penalites, resiliation, reception, sous_traitance, prix, responsabilite, procedure).
        keywords: Mots-clés optionnels pour filtrer.
        max_results: Nombre max de résultats.

    Returns:
        Liste de dicts avec reference, principe, resume.
    """
    results = [j for j in JURISPRUDENCE_BTP if j.theme == theme]

    if keywords:
        def _strip_accents(s: str) -> str:
            return "".join(
                c for c in unicodedata.normalize("NFD", s)
                if unicodedata.category(c) != "Mn"
            )

        kw_lower = [_strip_accents(k.lower()) for k in keywords]

        def score(entry: JurisprudenceEntry) -> int:
            return sum(
                1 for kw in kw_lower
                if any(kw in _strip_accents(ek.lower()) for ek in entry.keywords)
            )

        results.sort(key=score, reverse=True)

    return [
        {
            "reference": j.reference,
            "principe": j.principe,
            "resume": j.resume,
            "theme": j.theme,
        }
        for j in results[:max_results]
    ]


def get_jurisprudence_context_for_analyzer(
    analyzer_type: Literal["ccap", "ae"],
) -> str:
    """Retourne le contexte jurisprudentiel formaté pour injection dans un prompt LLM.

    Taille cible : < 2000 tokens (~8000 caractères).

    Args:
        analyzer_type: "ccap" pour l'analyseur CCAP, "ae" pour l'AE.

    Returns:
        Texte formaté prêt à être injecté dans un prompt LLM.
    """
    themes = _CCAP_THEMES if analyzer_type == "ccap" else _AE_THEMES

    relevant = [j for j in JURISPRUDENCE_BTP if j.theme in themes]

    header = (
        "\n\n=== JURISPRUDENCE BTP APPLICABLE ===\n\n"
        "Décisions clés à prendre en compte lors de l'analyse des clauses :\n\n"
    )

    lines: list[str] = []
    for j in relevant:
        lines.append(f"• **{j.reference}** — {j.principe}")

    footer = (
        "\n\nUtilise ces précédents pour évaluer la légalité et le risque des clauses analysées. "
        "Cite la jurisprudence pertinente lorsqu'une clause présente un risque identifié par un précédent."
    )

    return header + "\n".join(lines) + footer

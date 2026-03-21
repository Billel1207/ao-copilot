import { Metadata } from "next";

export const metadata: Metadata = {
  title: "CGU — AO Copilot",
  description: "Conditions Générales d'Utilisation de la plateforme AO Copilot, service d'analyse d'appels d'offres BTP par IA.",
};

export default function CguPage() {
  return (
    <div className="max-w-3xl mx-auto py-12 px-6">
      <h1 className="text-3xl font-bold text-gray-900 mb-2">Conditions Générales d&apos;Utilisation</h1>
      <p className="text-sm text-gray-500 mb-8">En vigueur au 1er mars 2026</p>

      <section className="mb-8">
        <h2 className="text-xl font-semibold text-gray-800 mb-3">Article 1 — Objet du service</h2>
        <p className="text-gray-600">
          AO Copilot est un service SaaS (Software as a Service) d&apos;analyse automatique de Dossiers de
          Consultation des Entreprises (DCE) à destination des professionnels du BTP et de l&apos;ingénierie.
          Le service permet d&apos;analyser des appels d&apos;offres publics et privés grâce à l&apos;intelligence
          artificielle afin d&apos;en extraire les informations clés, les risques et les critères de sélection.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold text-gray-800 mb-3">Article 2 — Conditions d&apos;accès</h2>
        <p className="text-gray-600 mb-3">
          L&apos;accès au service est réservé aux professionnels (personnes morales ou personnes physiques
          agissant dans un cadre professionnel). En créant un compte, l&apos;utilisateur déclare :
        </p>
        <ul className="list-disc list-inside text-gray-600 space-y-1 ml-4">
          <li>Être majeur et avoir la capacité juridique de conclure un contrat</li>
          <li>Agir dans le cadre de son activité professionnelle</li>
          <li>Avoir pris connaissance et accepté les présentes CGU</li>
          <li>Fournir des informations exactes lors de l&apos;inscription</li>
        </ul>
        <p className="text-gray-600 mt-3">
          AO Copilot se réserve le droit de suspendre ou résilier tout compte ne respectant pas
          ces conditions.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold text-gray-800 mb-3">Article 3 — Obligations de l&apos;utilisateur</h2>
        <p className="text-gray-600 mb-3">L&apos;utilisateur s&apos;engage à :</p>
        <ul className="list-disc list-inside text-gray-600 space-y-1 ml-4">
          <li>Utiliser le service conformément à sa destination et à la législation française en vigueur</li>
          <li>Ne pas tenter de contourner les mesures de sécurité ou de contrôle d&apos;accès</li>
          <li>Ne pas uploader de documents contenant des données personnelles sensibles sans base légale appropriée</li>
          <li>Ne pas partager ses identifiants de connexion avec des tiers</li>
          <li>Respecter les quotas et limites associés à son plan d&apos;abonnement</li>
          <li>Signaler toute faille de sécurité ou usage abusif à contact@aocopilot.fr</li>
        </ul>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold text-gray-800 mb-3">Article 4 — Propriété intellectuelle</h2>
        <p className="text-gray-600">
          Les analyses, rapports et contenus générés par AO Copilot à partir des documents uploadés par
          l&apos;utilisateur sont mis à disposition de l&apos;utilisateur sous licence d&apos;utilisation non exclusive.
          AO Copilot SAS conserve la propriété de l&apos;ensemble des algorithmes, modèles et technologies
          sous-jacentes. Les documents uploadés par l&apos;utilisateur restent sa propriété exclusive.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold text-gray-800 mb-3">Article 5 — Limitation de responsabilité</h2>
        <p className="text-gray-600 mb-3">
          Les analyses produites par AO Copilot sont fournies à titre informatif et d&apos;aide à la décision.
          Elles ne sauraient remplacer l&apos;avis d&apos;un professionnel qualifié (juriste, économiste de la
          construction, etc.). AO Copilot SAS ne saurait être tenu responsable :
        </p>
        <ul className="list-disc list-inside text-gray-600 space-y-1 ml-4">
          <li>Des décisions prises par l&apos;utilisateur sur la base des analyses fournies</li>
          <li>Des erreurs ou imprécisions pouvant résulter de l&apos;analyse automatique par IA</li>
          <li>Des interruptions de service liées à des opérations de maintenance ou à des cas de force majeure</li>
          <li>De la perte de données au-delà de la durée de rétention applicable au plan souscrit</li>
        </ul>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold text-gray-800 mb-3">Article 6 — Plans et tarification</h2>
        <p className="text-gray-600">
          L&apos;accès au service est conditionné à la souscription d&apos;un plan d&apos;abonnement payant après
          expiration de la période d&apos;essai. Les tarifs et fonctionnalités de chaque plan sont détaillés
          sur la page de tarification. AO Copilot se réserve le droit de modifier ses tarifs sous réserve
          d&apos;un préavis de 30 jours communiqué par email.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold text-gray-800 mb-3">Article 7 — Résiliation</h2>
        <p className="text-gray-600">
          L&apos;utilisateur peut résilier son abonnement à tout moment depuis son espace client. La résiliation
          prend effet à la fin de la période de facturation en cours. AO Copilot peut résilier l&apos;accès
          d&apos;un utilisateur en cas de non-respect des présentes CGU, avec ou sans préavis selon la gravité
          du manquement.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold text-gray-800 mb-3">Article 8 — Modification des CGU</h2>
        <p className="text-gray-600">
          AO Copilot SAS se réserve le droit de modifier les présentes CGU à tout moment. Les utilisateurs
          seront informés par email de toute modification substantielle au moins 15 jours avant son entrée
          en vigueur. La poursuite de l&apos;utilisation du service vaut acceptation des nouvelles CGU.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold text-gray-800 mb-3">Article 9 — Droit applicable et juridiction compétente</h2>
        <p className="text-gray-600">
          Les présentes CGU sont régies par le droit français. En cas de litige, les parties s&apos;efforceront
          de trouver une solution amiable. À défaut, le litige sera soumis à la compétence exclusive des
          tribunaux de Paris (France).
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold text-gray-800 mb-3">Article 10 — Contact</h2>
        <p className="text-gray-600">
          Pour toute question relative aux présentes CGU :{" "}
          <a href="mailto:contact@aocopilot.fr" className="text-blue-600 hover:underline">
            contact@aocopilot.fr
          </a>
        </p>
      </section>

      <p className="text-xs text-gray-400 mt-12">Dernière mise à jour : mars 2026</p>
    </div>
  );
}

export default function ConfidentialitePage() {
  return (
    <div className="max-w-3xl mx-auto py-12 px-6">
      <h1 className="text-3xl font-bold text-gray-900 mb-2">Politique de confidentialité</h1>
      <p className="text-sm text-gray-500 mb-8">En vigueur au 1er mars 2026 — Conforme au RGPD (UE) 2016/679</p>

      <section className="mb-8">
        <h2 className="text-xl font-semibold text-gray-800 mb-3">1. Responsable du traitement</h2>
        <div className="text-gray-600 space-y-1">
          <p><span className="font-medium">Société :</span> AO Copilot SAS</p>
          <p><span className="font-medium">Siège social :</span> Paris, France</p>
          <p><span className="font-medium">Email DPO :</span>{" "}
            <a href="mailto:dpo@aocopilot.fr" className="text-blue-600 hover:underline">
              dpo@aocopilot.fr
            </a>
          </p>
        </div>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold text-gray-800 mb-3">2. Données collectées</h2>
        <p className="text-gray-600 mb-3">Dans le cadre de l&apos;utilisation du service AO Copilot, nous collectons :</p>
        <div className="space-y-3">
          <div>
            <h3 className="font-medium text-gray-700">Données de compte</h3>
            <ul className="list-disc list-inside text-gray-600 ml-4 space-y-1">
              <li>Nom et prénom</li>
              <li>Adresse email professionnelle</li>
              <li>Nom de l&apos;organisation</li>
              <li>Mot de passe (stocké sous forme de hachage bcrypt, jamais en clair)</li>
            </ul>
          </div>
          <div>
            <h3 className="font-medium text-gray-700">Données d&apos;utilisation</h3>
            <ul className="list-disc list-inside text-gray-600 ml-4 space-y-1">
              <li>Documents uploadés (DCE, appels d&apos;offres)</li>
              <li>Historique d&apos;analyses générées</li>
              <li>Journaux d&apos;actions (audit logs)</li>
              <li>Adresse IP et données de connexion</li>
            </ul>
          </div>
          <div>
            <h3 className="font-medium text-gray-700">Données de facturation</h3>
            <ul className="list-disc list-inside text-gray-600 ml-4 space-y-1">
              <li>Informations de paiement traitées par Stripe (nous ne stockons pas les numéros de carte)</li>
              <li>Historique des factures</li>
            </ul>
          </div>
        </div>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold text-gray-800 mb-3">3. Finalités du traitement</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-gray-600 border-collapse">
            <thead>
              <tr className="bg-gray-50">
                <th className="text-left p-3 border border-gray-200 font-medium text-gray-700">Finalité</th>
                <th className="text-left p-3 border border-gray-200 font-medium text-gray-700">Base légale</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="p-3 border border-gray-200">Fourniture du service d&apos;analyse IA</td>
                <td className="p-3 border border-gray-200">Exécution du contrat</td>
              </tr>
              <tr className="bg-gray-50">
                <td className="p-3 border border-gray-200">Gestion de votre compte et authentification</td>
                <td className="p-3 border border-gray-200">Exécution du contrat</td>
              </tr>
              <tr>
                <td className="p-3 border border-gray-200">Facturation et paiements</td>
                <td className="p-3 border border-gray-200">Obligation légale</td>
              </tr>
              <tr className="bg-gray-50">
                <td className="p-3 border border-gray-200">Sécurité et prévention des fraudes</td>
                <td className="p-3 border border-gray-200">Intérêt légitime</td>
              </tr>
              <tr>
                <td className="p-3 border border-gray-200">Amélioration du service (anonymisé)</td>
                <td className="p-3 border border-gray-200">Intérêt légitime</td>
              </tr>
              <tr className="bg-gray-50">
                <td className="p-3 border border-gray-200">Communications transactionnelles</td>
                <td className="p-3 border border-gray-200">Exécution du contrat</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold text-gray-800 mb-3">4. Durée de conservation</h2>
        <ul className="list-disc list-inside text-gray-600 space-y-1 ml-4">
          <li><span className="font-medium">Données de compte :</span> Durée de l&apos;abonnement + 3 ans après résiliation</li>
          <li><span className="font-medium">Documents uploadés :</span> Selon le plan souscrit (14 jours pour Trial, 30 jours Starter, 90 jours Pro, 365 jours Business)</li>
          <li><span className="font-medium">Journaux de sécurité :</span> 12 mois</li>
          <li><span className="font-medium">Données de facturation :</span> 10 ans (obligation légale comptable)</li>
        </ul>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold text-gray-800 mb-3">5. Sous-traitants et transferts</h2>
        <p className="text-gray-600 mb-3">Nous faisons appel aux sous-traitants suivants :</p>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-gray-600 border-collapse">
            <thead>
              <tr className="bg-gray-50">
                <th className="text-left p-3 border border-gray-200 font-medium text-gray-700">Prestataire</th>
                <th className="text-left p-3 border border-gray-200 font-medium text-gray-700">Rôle</th>
                <th className="text-left p-3 border border-gray-200 font-medium text-gray-700">Localisation</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="p-3 border border-gray-200">Scaleway SAS</td>
                <td className="p-3 border border-gray-200">Hébergement serveurs et stockage</td>
                <td className="p-3 border border-gray-200">France (Paris PAR1)</td>
              </tr>
              <tr className="bg-gray-50">
                <td className="p-3 border border-gray-200">Stripe Inc.</td>
                <td className="p-3 border border-gray-200">Traitement des paiements</td>
                <td className="p-3 border border-gray-200">UE (données cartes) + USA</td>
              </tr>
              <tr>
                <td className="p-3 border border-gray-200">Anthropic / OpenAI</td>
                <td className="p-3 border border-gray-200">Analyse IA des documents (Anthropic Claude) + Embeddings (OpenAI)</td>
                <td className="p-3 border border-gray-200">USA (clauses contractuelles types)</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p className="text-gray-500 text-sm mt-3">
          Les transferts hors UE (Anthropic, OpenAI, Stripe) sont encadrés par des clauses contractuelles types (CCT)
          approuvées par la Commission européenne.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold text-gray-800 mb-3">6. Vos droits RGPD</h2>
        <p className="text-gray-600 mb-3">
          Conformément au RGPD, vous disposez des droits suivants sur vos données personnelles :
        </p>
        <ul className="list-disc list-inside text-gray-600 space-y-1 ml-4">
          <li><span className="font-medium">Droit d&apos;accès :</span> obtenir une copie de vos données</li>
          <li><span className="font-medium">Droit de rectification :</span> corriger des données inexactes</li>
          <li><span className="font-medium">Droit à l&apos;effacement :</span> demander la suppression de vos données</li>
          <li><span className="font-medium">Droit à la portabilité :</span> recevoir vos données dans un format structuré</li>
          <li><span className="font-medium">Droit d&apos;opposition :</span> s&apos;opposer à certains traitements</li>
          <li><span className="font-medium">Droit à la limitation :</span> restreindre temporairement le traitement</li>
        </ul>
        <p className="text-gray-600 mt-3">
          Pour exercer vos droits, contactez notre DPO :{" "}
          <a href="mailto:dpo@aocopilot.fr" className="text-blue-600 hover:underline">
            dpo@aocopilot.fr
          </a>
          . Nous répondons dans un délai d&apos;un mois. Vous pouvez également introduire une réclamation auprès
          de la CNIL (<a href="https://www.cnil.fr" className="text-blue-600 hover:underline" target="_blank" rel="noopener noreferrer">www.cnil.fr</a>).
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold text-gray-800 mb-3">7. Hébergement en France</h2>
        <p className="text-gray-600">
          L&apos;ensemble des données est hébergé sur des serveurs situés en France (Scaleway, région Paris PAR1),
          garantissant la souveraineté numérique de vos données et la conformité avec les exigences RGPD.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold text-gray-800 mb-3">8. Sécurité des données</h2>
        <p className="text-gray-600">
          Nous mettons en oeuvre des mesures techniques et organisationnelles appropriées : chiffrement TLS
          en transit, chiffrement au repos, contrôle d&apos;accès par rôles (RBAC), isolation multi-tenant par
          Row-Level Security PostgreSQL, journaux d&apos;audit, et surveillance continue via Sentry et OpenTelemetry.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold text-gray-800 mb-3">9. Contact DPO</h2>
        <div className="text-gray-600 space-y-1">
          <p>Délégué à la Protection des Données (DPO) de AO Copilot SAS</p>
          <p>
            <a href="mailto:dpo@aocopilot.fr" className="text-blue-600 hover:underline">
              dpo@aocopilot.fr
            </a>
          </p>
        </div>
      </section>

      <p className="text-xs text-gray-400 mt-12">Dernière mise à jour : mars 2026</p>
    </div>
  );
}

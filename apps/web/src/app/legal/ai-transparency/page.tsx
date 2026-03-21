import Link from "next/link";

export const metadata = {
  title: "Transparence IA — AO Copilot",
  description:
    "Informations sur l'utilisation de l'intelligence artificielle dans AO Copilot, conformément au Règlement européen AI Act (2024/1689).",
};

export default function AITransparencyPage() {
  return (
    <div className="max-w-3xl mx-auto py-12 px-6">
      <h1 className="text-3xl font-bold text-gray-900 mb-2">
        Transparence Intelligence Artificielle
      </h1>
      <p className="text-sm text-blue-600 font-medium mb-8">
        Conformément au Règlement européen 2024/1689 (AI Act) — Article 50
      </p>

      {/* 1. Identification */}
      <section className="mb-8">
        <h2 className="text-xl font-semibold text-gray-800 mb-3">
          1. Identification du fournisseur
        </h2>
        <div className="text-gray-600 space-y-1">
          <p>
            <span className="font-medium">Fournisseur :</span> AO Copilot SAS
          </p>
          <p>
            <span className="font-medium">Contact :</span>{" "}
            <a
              href="mailto:contact@aocopilot.fr"
              className="text-blue-600 hover:underline"
            >
              contact@aocopilot.fr
            </a>
          </p>
          <p>
            <span className="font-medium">Site :</span>{" "}
            <a
              href="https://aocopilot.fr"
              className="text-blue-600 hover:underline"
            >
              aocopilot.fr
            </a>
          </p>
        </div>
      </section>

      {/* 2. Classification */}
      <section className="mb-8">
        <h2 className="text-xl font-semibold text-gray-800 mb-3">
          2. Classification du risque
        </h2>
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-3">
          <p className="text-blue-800 font-semibold">Risque limité</p>
          <p className="text-blue-700 text-sm mt-1">
            AO Copilot est classé comme un système IA à risque limité au sens du
            Règlement 2024/1689. Il est soumis aux obligations de transparence
            de l&apos;Article 50.
          </p>
        </div>
        <p className="text-gray-600 text-sm">
          AO Copilot n&apos;est pas un système IA à haut risque. Il ne prend
          aucune décision automatisée ayant un effet juridique sur les
          utilisateurs.
        </p>
      </section>

      {/* 3. Finalité */}
      <section className="mb-8">
        <h2 className="text-xl font-semibold text-gray-800 mb-3">
          3. Finalité du système IA
        </h2>
        <p className="text-gray-600 mb-3">
          AO Copilot utilise l&apos;intelligence artificielle pour :
        </p>
        <ul className="list-disc list-inside text-gray-600 space-y-1.5 ml-2">
          <li>
            Analyser les documents de consultation des entreprises (DCE) dans le
            secteur du BTP
          </li>
          <li>
            Extraire des informations structurées (délais, critères, risques) des
            documents PDF
          </li>
          <li>
            Générer des résumés, checklists et scores d&apos;aide à la décision
            (Go/No-Go)
          </li>
          <li>
            Produire des rapports d&apos;analyse exportables (PDF, Word)
          </li>
          <li>
            Assister la rédaction de mémoires techniques via des suggestions IA
          </li>
        </ul>
      </section>

      {/* 4. Modèles */}
      <section className="mb-8">
        <h2 className="text-xl font-semibold text-gray-800 mb-3">
          4. Modèles d&apos;IA utilisés
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="bg-gray-100">
                <th className="text-left p-2 border border-gray-200 font-semibold">
                  Fonction
                </th>
                <th className="text-left p-2 border border-gray-200 font-semibold">
                  Modèle
                </th>
                <th className="text-left p-2 border border-gray-200 font-semibold">
                  Fournisseur
                </th>
              </tr>
            </thead>
            <tbody className="text-gray-600">
              <tr>
                <td className="p-2 border border-gray-200">
                  Analyse de documents, résumé, scoring
                </td>
                <td className="p-2 border border-gray-200">Claude Sonnet</td>
                <td className="p-2 border border-gray-200">Anthropic</td>
              </tr>
              <tr>
                <td className="p-2 border border-gray-200">
                  Fallback (indisponibilité Anthropic)
                </td>
                <td className="p-2 border border-gray-200">GPT-4o</td>
                <td className="p-2 border border-gray-200">OpenAI</td>
              </tr>
              <tr>
                <td className="p-2 border border-gray-200">
                  Embeddings (recherche sémantique)
                </td>
                <td className="p-2 border border-gray-200">Mistral Embed</td>
                <td className="p-2 border border-gray-200">
                  Mistral AI (UE)
                </td>
              </tr>
              <tr>
                <td className="p-2 border border-gray-200">
                  OCR (reconnaissance de texte)
                </td>
                <td className="p-2 border border-gray-200">
                  PyMuPDF + Tesseract
                </td>
                <td className="p-2 border border-gray-200">Open source</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* 5. Données */}
      <section className="mb-8">
        <h2 className="text-xl font-semibold text-gray-800 mb-3">
          5. Données traitées
        </h2>
        <div className="text-gray-600 space-y-2">
          <p>
            <span className="font-medium">Entrées :</span> Documents PDF
            uploadés par l&apos;utilisateur (DCE, CCAP, CCTP, RC, DPGF, etc.)
          </p>
          <p>
            <span className="font-medium">Sorties :</span> Résumés structurés,
            checklists, scores, rapports — générés par IA et clairement
            étiquetés comme tels.
          </p>
          <p>
            <span className="font-medium">Stockage :</span> Les documents sont
            stockés sur Scaleway Object Storage (Paris, France) conformément au
            RGPD. Les embeddings sont stockés dans PostgreSQL avec pgvector.
          </p>
          <p>
            <span className="font-medium">Pas de réentraînement :</span> Vos
            documents ne sont jamais utilisés pour entraîner ou améliorer les
            modèles IA. Ils sont uniquement traités pour votre analyse.
          </p>
        </div>
      </section>

      {/* 6. Limitations */}
      <section className="mb-8">
        <h2 className="text-xl font-semibold text-gray-800 mb-3">
          6. Limitations connues
        </h2>
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
          <ul className="text-amber-800 text-sm space-y-1.5">
            <li>
              • L&apos;IA peut produire des erreurs d&apos;interprétation sur
              des documents mal scannés ou de faible qualité OCR
            </li>
            <li>
              • Les scores et recommandations sont indicatifs et ne remplacent
              pas l&apos;expertise humaine d&apos;un juriste ou d&apos;un
              ingénieur
            </li>
            <li>
              • L&apos;IA n&apos;a pas accès à des sources externes (pas
              d&apos;accès Internet, pas de bases de données externes)
            </li>
            <li>
              • La qualité de l&apos;analyse dépend directement de la qualité et
              de l&apos;exhaustivité des documents fournis
            </li>
            <li>
              • Les analyses sont basées sur le droit français des marchés
              publics et peuvent ne pas être applicables dans d&apos;autres
              juridictions
            </li>
          </ul>
        </div>
      </section>

      {/* 7. Supervision humaine */}
      <section className="mb-8">
        <h2 className="text-xl font-semibold text-gray-800 mb-3">
          7. Supervision humaine
        </h2>
        <p className="text-gray-600">
          Toutes les analyses IA sont présentées comme des{" "}
          <strong>aides à la décision</strong>. L&apos;utilisateur conserve
          l&apos;entière responsabilité de la décision finale (Go/No-Go,
          réponse à l&apos;appel d&apos;offres). Aucune action automatisée
          n&apos;est effectuée sans validation explicite de l&apos;utilisateur.
        </p>
      </section>

      {/* 8. Droits */}
      <section className="mb-8">
        <h2 className="text-xl font-semibold text-gray-800 mb-3">
          8. Vos droits
        </h2>
        <div className="text-gray-600 space-y-2">
          <p>Conformément au RGPD et à l&apos;AI Act, vous disposez de :</p>
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li>
              <strong>Droit d&apos;information :</strong> cette page vous
              informe de l&apos;utilisation de l&apos;IA dans nos services
            </li>
            <li>
              <strong>Droit d&apos;accès :</strong> vous pouvez demander
              l&apos;historique des analyses IA effectuées sur vos documents
            </li>
            <li>
              <strong>Droit de suppression :</strong> vous pouvez supprimer vos
              documents et analyses à tout moment
            </li>
            <li>
              <strong>Droit d&apos;opposition :</strong> vous pouvez refuser le
              traitement IA de vos documents
            </li>
            <li>
              <strong>Droit à l&apos;explication :</strong> vous pouvez demander
              des explications sur les résultats d&apos;analyse IA
            </li>
          </ul>
          <p className="mt-3">
            Pour exercer ces droits, contactez-nous à{" "}
            <a
              href="mailto:dpo@aocopilot.fr"
              className="text-blue-600 hover:underline"
            >
              dpo@aocopilot.fr
            </a>
          </p>
        </div>
      </section>

      {/* 9. Traçabilité */}
      <section className="mb-8">
        <h2 className="text-xl font-semibold text-gray-800 mb-3">
          9. Traçabilité et audit
        </h2>
        <p className="text-gray-600">
          Chaque appel au système IA est journalisé dans un registre d&apos;audit
          interne comprenant : le modèle utilisé, la date et l&apos;heure, le
          nombre de tokens traités, la latence, et un identifiant anonymisé. Ce
          registre est conservé conformément à nos obligations légales et est
          disponible sur demande pour les autorités compétentes.
        </p>
      </section>

      {/* Navigation */}
      <div className="flex items-center gap-4 pt-6 border-t border-gray-200">
        <Link
          href="/legal/confidentialite"
          className="text-sm text-blue-600 hover:underline"
        >
          Politique de confidentialité
        </Link>
        <Link
          href="/legal/cgu"
          className="text-sm text-blue-600 hover:underline"
        >
          CGU
        </Link>
        <Link
          href="/legal/mentions-legales"
          className="text-sm text-blue-600 hover:underline"
        >
          Mentions légales
        </Link>
      </div>

      <p className="text-xs text-gray-400 mt-8">
        Dernière mise à jour : mars 2026
      </p>
    </div>
  );
}

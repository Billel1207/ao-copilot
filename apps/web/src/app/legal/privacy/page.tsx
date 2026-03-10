"use client";

import Link from "next/link";

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-white">
      <header className="border-b bg-slate-50">
        <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/" className="text-lg font-bold text-blue-700">AO Copilot</Link>
          <nav className="flex gap-4 text-sm text-slate-500">
            <Link href="/legal/cgu" className="hover:text-slate-700">CGU</Link>
            <Link href="/legal/cgv" className="hover:text-slate-700">CGV</Link>
            <Link href="/legal/privacy" className="text-blue-700 font-medium">Politique de confidentialit&eacute;</Link>
          </nav>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-12">
        <h1 className="text-3xl font-bold text-slate-900 mb-2">Politique de Confidentialit&eacute; &amp; RGPD</h1>
        <p className="text-sm text-slate-400 mb-8">Derni&egrave;re mise &agrave; jour : 10 mars 2026</p>

        <div className="prose prose-slate max-w-none space-y-8 text-sm leading-relaxed">
          <section>
            <h2 className="text-xl font-semibold text-slate-800 mt-8 mb-3">1. Responsable de traitement</h2>
            <p>AO Copilot SAS, dont le si&egrave;ge social est situ&eacute; en France, est responsable du traitement des donn&eacute;es personnelles collect&eacute;es via le Service.</p>
            <p>Contact DPO : <a href="mailto:dpo@ao-copilot.fr" className="text-blue-600 hover:underline">dpo@ao-copilot.fr</a></p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-slate-800 mt-8 mb-3">2. Donn&eacute;es collect&eacute;es</h2>
            <p>Nous collectons les donn&eacute;es suivantes :</p>
            <div className="overflow-x-auto mt-4">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b bg-slate-50">
                    <th className="py-2 px-3 font-semibold">Donn&eacute;e</th>
                    <th className="py-2 px-3 font-semibold">Finalit&eacute;</th>
                    <th className="py-2 px-3 font-semibold">Base l&eacute;gale</th>
                    <th className="py-2 px-3 font-semibold">Dur&eacute;e</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b"><td className="py-2 px-3">Nom, pr&eacute;nom, email</td><td className="py-2 px-3">Cr&eacute;ation de compte</td><td className="py-2 px-3">Contrat</td><td className="py-2 px-3">Dur&eacute;e du contrat + 3 ans</td></tr>
                  <tr className="border-b"><td className="py-2 px-3">Nom d&apos;entreprise, SIRET</td><td className="py-2 px-3">Profil entreprise</td><td className="py-2 px-3">Contrat</td><td className="py-2 px-3">Dur&eacute;e du contrat</td></tr>
                  <tr className="border-b"><td className="py-2 px-3">Documents upload&eacute;s (DCE)</td><td className="py-2 px-3">Analyse IA</td><td className="py-2 px-3">Contrat</td><td className="py-2 px-3">Selon plan (7-365j)</td></tr>
                  <tr className="border-b"><td className="py-2 px-3">Donn&eacute;es de paiement</td><td className="py-2 px-3">Facturation</td><td className="py-2 px-3">Contrat</td><td className="py-2 px-3">G&eacute;r&eacute; par Stripe</td></tr>
                  <tr className="border-b"><td className="py-2 px-3">Logs de connexion, IP</td><td className="py-2 px-3">S&eacute;curit&eacute;</td><td className="py-2 px-3">Int&eacute;r&ecirc;t l&eacute;gitime</td><td className="py-2 px-3">12 mois</td></tr>
                </tbody>
              </table>
            </div>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-slate-800 mt-8 mb-3">3. H&eacute;bergement et transferts</h2>
            <p>Toutes les donn&eacute;es sont h&eacute;berg&eacute;es en France (Scaleway, Paris) au sein de l&apos;Union Europ&eacute;enne. Aucun transfert de donn&eacute;es hors UE n&apos;est effectu&eacute; pour le stockage.</p>
            <p className="mt-2"><strong>Sous-traitants :</strong></p>
            <ul className="list-disc pl-6 space-y-1 mt-2">
              <li><strong>Anthropic</strong> (Claude AI) &mdash; Analyse IA des documents. Les textes des documents sont envoy&eacute;s via API pour analyse. Anthropic ne conserve pas les donn&eacute;es au-del&agrave; du traitement (politique zero-retention sur les API).</li>
              <li><strong>OpenAI</strong> &mdash; G&eacute;n&eacute;ration d&apos;embeddings vectoriels. Seuls des fragments de texte anonymis&eacute;s sont transmis.</li>
              <li><strong>Stripe</strong> &mdash; Traitement des paiements. Certifi&eacute; PCI DSS Level 1.</li>
              <li><strong>Sentry</strong> &mdash; Monitoring d&apos;erreurs. Aucune donn&eacute;e personnelle transmise.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-slate-800 mt-8 mb-3">4. Vos droits (RGPD)</h2>
            <p>Conform&eacute;ment au R&egrave;glement G&eacute;n&eacute;ral sur la Protection des Donn&eacute;es (RGPD) et &agrave; la loi Informatique et Libert&eacute;s, vous disposez des droits suivants :</p>
            <ul className="list-disc pl-6 space-y-1 mt-2">
              <li><strong>Droit d&apos;acc&egrave;s</strong> &mdash; Obtenir une copie de vos donn&eacute;es personnelles</li>
              <li><strong>Droit de rectification</strong> &mdash; Corriger des donn&eacute;es inexactes ou incompl&egrave;tes</li>
              <li><strong>Droit &agrave; l&apos;effacement</strong> &mdash; Demander la suppression de vos donn&eacute;es</li>
              <li><strong>Droit &agrave; la portabilit&eacute;</strong> &mdash; Recevoir vos donn&eacute;es dans un format structur&eacute;</li>
              <li><strong>Droit d&apos;opposition</strong> &mdash; Vous opposer au traitement pour motifs l&eacute;gitimes</li>
              <li><strong>Droit &agrave; la limitation</strong> &mdash; Restreindre le traitement dans certains cas</li>
            </ul>
            <p className="mt-3">Pour exercer vos droits : <a href="mailto:dpo@ao-copilot.fr" className="text-blue-600 hover:underline">dpo@ao-copilot.fr</a>. R&eacute;ponse sous 30 jours.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-slate-800 mt-8 mb-3">5. Cookies</h2>
            <p>Le Service utilise uniquement des cookies techniques strictement n&eacute;cessaires au fonctionnement (session JWT, pr&eacute;f&eacute;rences). Aucun cookie publicitaire ou de tra&ccedil;age n&apos;est utilis&eacute;. Aucun consentement n&apos;est requis pour les cookies techniques (art. 82 de la loi Informatique et Libert&eacute;s).</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-slate-800 mt-8 mb-3">6. S&eacute;curit&eacute;</h2>
            <p>Nous mettons en &oelig;uvre les mesures de s&eacute;curit&eacute; suivantes :</p>
            <ul className="list-disc pl-6 space-y-1 mt-2">
              <li>Chiffrement TLS 1.3 pour toutes les communications</li>
              <li>Mots de passe hash&eacute;s (bcrypt, facteur de co&ucirc;t 12)</li>
              <li>JWT &agrave; dur&eacute;e limit&eacute;e (15 min) avec rotation des refresh tokens</li>
              <li>Isolation multi-tenant via Row-Level Security (RLS) PostgreSQL</li>
              <li>URLs de t&eacute;l&eacute;chargement sign&eacute;es (&agrave; dur&eacute;e limit&eacute;e, 15 min)</li>
              <li>Audit logs des actions sensibles</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-slate-800 mt-8 mb-3">7. Notification de violation</h2>
            <p>En cas de violation de donn&eacute;es personnelles, nous nous engageons &agrave; notifier la CNIL dans les 72 heures et &agrave; informer les personnes concern&eacute;es dans les meilleurs d&eacute;lais, conform&eacute;ment aux articles 33 et 34 du RGPD.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-slate-800 mt-8 mb-3">8. R&eacute;clamation</h2>
            <p>Si vous estimez que le traitement de vos donn&eacute;es ne respecte pas la r&eacute;glementation, vous pouvez adresser une r&eacute;clamation &agrave; la CNIL : <a href="https://www.cnil.fr/fr/plaintes" className="text-blue-600 hover:underline" target="_blank" rel="noopener noreferrer">www.cnil.fr/fr/plaintes</a>.</p>
          </section>
        </div>
      </main>
    </div>
  );
}

"use client";

import Link from "next/link";

export default function CGVPage() {
  return (
    <div className="min-h-screen bg-white">
      <header className="border-b bg-slate-50">
        <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/" className="text-lg font-bold text-blue-700">AO Copilot</Link>
          <nav className="flex gap-4 text-sm text-slate-500">
            <Link href="/legal/cgu" className="hover:text-slate-700">CGU</Link>
            <Link href="/legal/cgv" className="text-blue-700 font-medium">CGV</Link>
            <Link href="/legal/privacy" className="hover:text-slate-700">Politique de confidentialit&eacute;</Link>
          </nav>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-12">
        <h1 className="text-3xl font-bold text-slate-900 mb-2">Conditions G&eacute;n&eacute;rales de Vente</h1>
        <p className="text-sm text-slate-400 mb-8">Derni&egrave;re mise &agrave; jour : 10 mars 2026</p>

        <div className="prose prose-slate max-w-none space-y-8 text-sm leading-relaxed">
          <section>
            <h2 className="text-xl font-semibold text-slate-800 mt-8 mb-3">Article 1 &mdash; Objet</h2>
            <p>Les pr&eacute;sentes Conditions G&eacute;n&eacute;rales de Vente (ci-apr&egrave;s &laquo; CGV &raquo;) r&eacute;gissent les relations commerciales entre AO Copilot SAS (&laquo; le Prestataire &raquo;) et toute personne morale souscrivant &agrave; un abonnement payant (&laquo; le Client &raquo;).</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-slate-800 mt-8 mb-3">Article 2 &mdash; Plans tarifaires</h2>
            <p>Le Service est propos&eacute; sous forme d&apos;abonnements mensuels ou annuels :</p>
            <div className="overflow-x-auto mt-4">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b bg-slate-50">
                    <th className="py-2 px-3 font-semibold">Plan</th>
                    <th className="py-2 px-3 font-semibold">Prix mensuel</th>
                    <th className="py-2 px-3 font-semibold">Prix annuel</th>
                    <th className="py-2 px-3 font-semibold">Documents/mois</th>
                    <th className="py-2 px-3 font-semibold">Utilisateurs</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b"><td className="py-2 px-3">Gratuit</td><td className="py-2 px-3">0 &euro;</td><td className="py-2 px-3">&mdash;</td><td className="py-2 px-3">5</td><td className="py-2 px-3">1</td></tr>
                  <tr className="border-b"><td className="py-2 px-3">Starter</td><td className="py-2 px-3">79 &euro; HT</td><td className="py-2 px-3">758 &euro; HT</td><td className="py-2 px-3">15</td><td className="py-2 px-3">1</td></tr>
                  <tr className="border-b"><td className="py-2 px-3">Pro</td><td className="py-2 px-3">199 &euro; HT</td><td className="py-2 px-3">1 910 &euro; HT</td><td className="py-2 px-3">60</td><td className="py-2 px-3">5</td></tr>
                  <tr className="border-b"><td className="py-2 px-3">Europe</td><td className="py-2 px-3">299 &euro; HT</td><td className="py-2 px-3">2 870 &euro; HT</td><td className="py-2 px-3">100</td><td className="py-2 px-3">20</td></tr>
                  <tr className="border-b"><td className="py-2 px-3">Business</td><td className="py-2 px-3">499 &euro; HT</td><td className="py-2 px-3">4 790 &euro; HT</td><td className="py-2 px-3">Illimit&eacute;</td><td className="py-2 px-3">Illimit&eacute;</td></tr>
                </tbody>
              </table>
            </div>
            <p className="mt-3">Les prix sont indiqu&eacute;s en euros hors taxes (HT). La TVA applicable (20%) sera ajout&eacute;e au moment de la facturation.</p>
            <p>Option pay-per-doc : 3 &euro; HT par document unitaire.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-slate-800 mt-8 mb-3">Article 3 &mdash; Souscription et paiement</h2>
            <p>La souscription s&apos;effectue en ligne via la plateforme de paiement s&eacute;curis&eacute;e Stripe. Les moyens de paiement accept&eacute;s sont : carte bancaire (Visa, Mastercard, American Express), Apple Pay et Google Pay.</p>
            <p>L&apos;abonnement est reconduit automatiquement &agrave; chaque &eacute;ch&eacute;ance (mensuelle ou annuelle). Le Client peut r&eacute;silier &agrave; tout moment ; la r&eacute;siliation prend effet &agrave; la fin de la p&eacute;riode en cours.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-slate-800 mt-8 mb-3">Article 4 &mdash; P&eacute;riode d&apos;essai</h2>
            <p>Les plans Starter et Pro b&eacute;n&eacute;ficient d&apos;une p&eacute;riode d&apos;essai gratuite de 14 jours. Aucun pr&eacute;l&egrave;vement n&apos;est effectu&eacute; pendant cette p&eacute;riode. &Agrave; l&apos;issue de la p&eacute;riode d&apos;essai, le Client sera automatiquement factur&eacute; sauf annulation pr&eacute;alable.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-slate-800 mt-8 mb-3">Article 5 &mdash; Droit de r&eacute;tractation</h2>
            <p>Conform&eacute;ment &agrave; l&apos;article L221-28 du Code de la consommation, le Client professionnel (B2B) ne b&eacute;n&eacute;ficie pas du droit de r&eacute;tractation. Le Service &eacute;tant imm&eacute;diatement accessible apr&egrave;s souscription, le Client reconna&icirc;t et accepte que l&apos;ex&eacute;cution commence imm&eacute;diatement.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-slate-800 mt-8 mb-3">Article 6 &mdash; Niveau de service (SLA)</h2>
            <p>Le plan Business b&eacute;n&eacute;ficie d&apos;un SLA de disponibilit&eacute; de 99,9% mesur&eacute; mensuellement, hors maintenance programm&eacute;e (notifi&eacute;e 48h &agrave; l&apos;avance). En cas de non-respect, le Client Business peut demander un avoir proportionnel au temps d&apos;indisponibilit&eacute;.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-slate-800 mt-8 mb-3">Article 7 &mdash; R&eacute;tention des donn&eacute;es</h2>
            <p>Les documents et analyses sont conserv&eacute;s selon la dur&eacute;e de r&eacute;tention du plan souscrit (7 &agrave; 365 jours). Au-del&agrave;, les donn&eacute;es sont automatiquement supprim&eacute;es. Le Client peut exporter ses donn&eacute;es &agrave; tout moment avant suppression.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-slate-800 mt-8 mb-3">Article 8 &mdash; Facturation</h2>
            <p>Les factures sont &eacute;mises par Stripe et disponibles dans l&apos;espace de gestion du Client. Elles incluent le num&eacute;ro de TVA intracommunautaire du Client si fourni. En cas d&apos;&eacute;chec de paiement, le Service peut &ecirc;tre suspendu apr&egrave;s 2 tentatives infructueuses et notification par email.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-slate-800 mt-8 mb-3">Article 9 &mdash; Droit applicable et litiges</h2>
            <p>Les pr&eacute;sentes CGV sont soumises au droit fran&ccedil;ais. En cas de litige, les parties s&apos;engagent &agrave; rechercher une solution amiable avant toute proc&eacute;dure judiciaire. &Agrave; d&eacute;faut, les tribunaux de commerce de Paris seront seuls comp&eacute;tents.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-slate-800 mt-8 mb-3">Article 10 &mdash; Contact</h2>
            <p>AO Copilot SAS &mdash; <a href="mailto:contact@ao-copilot.fr" className="text-blue-600 hover:underline">contact@ao-copilot.fr</a></p>
          </section>
        </div>
      </main>
    </div>
  );
}

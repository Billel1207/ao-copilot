"use client";

import Link from "next/link";

export default function CGUPage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="border-b bg-slate-50">
        <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/" className="text-lg font-bold text-blue-700">AO Copilot</Link>
          <nav className="flex gap-4 text-sm text-slate-500">
            <Link href="/legal/cgu" className="text-blue-700 font-medium">CGU</Link>
            <Link href="/legal/cgv" className="hover:text-slate-700">CGV</Link>
            <Link href="/legal/privacy" className="hover:text-slate-700">Politique de confidentialit&eacute;</Link>
          </nav>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-12">
        <h1 className="text-3xl font-bold text-slate-900 mb-2">Conditions G&eacute;n&eacute;rales d&apos;Utilisation</h1>
        <p className="text-sm text-slate-400 mb-8">Derni&egrave;re mise &agrave; jour : 10 mars 2026</p>

        <div className="prose prose-slate max-w-none space-y-8 text-sm leading-relaxed">
          <section>
            <h2 className="text-xl font-semibold text-slate-800 mt-8 mb-3">Article 1 &mdash; Objet</h2>
            <p>Les pr&eacute;sentes Conditions G&eacute;n&eacute;rales d&apos;Utilisation (ci-apr&egrave;s &laquo; CGU &raquo;) ont pour objet de d&eacute;finir les modalit&eacute;s et conditions d&apos;utilisation de la plateforme AO Copilot (ci-apr&egrave;s &laquo; le Service &raquo;), &eacute;dit&eacute;e par la soci&eacute;t&eacute; AO Copilot SAS.</p>
            <p>Le Service est une application web (SaaS) d&apos;aide &agrave; la d&eacute;cision pour l&apos;analyse de Dossiers de Consultation des Entreprises (DCE) dans le secteur du B&acirc;timent et Travaux Publics (BTP).</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-slate-800 mt-8 mb-3">Article 2 &mdash; Acceptation des CGU</h2>
            <p>L&apos;utilisation du Service implique l&apos;acceptation pleine et enti&egrave;re des pr&eacute;sentes CGU. En cr&eacute;ant un compte, l&apos;Utilisateur reconna&icirc;t avoir lu, compris et accept&eacute; les pr&eacute;sentes CGU sans r&eacute;serve.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-slate-800 mt-8 mb-3">Article 3 &mdash; Description du Service</h2>
            <p>AO Copilot propose les fonctionnalit&eacute;s suivantes :</p>
            <ul className="list-disc pl-6 space-y-1 mt-2">
              <li>Upload et extraction de texte &agrave; partir de documents PDF, DOCX, JPEG, PNG, TIFF</li>
              <li>Analyse automatis&eacute;e par intelligence artificielle des pi&egrave;ces du DCE (RC, CCTP, CCAP, DPGF, AE)</li>
              <li>G&eacute;n&eacute;ration de r&eacute;sum&eacute;s, checklists, crit&egrave;res d&apos;attribution, scores Go/No-Go</li>
              <li>D&eacute;tection de clauses risqu&eacute;es, conflits intra-DCE, et d&eacute;rogations au CCAG-Travaux 2021</li>
              <li>Export PDF, Word et Excel des analyses</li>
              <li>Veille automatis&eacute;e sur les appels d&apos;offres (BOAMP, TED)</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-slate-800 mt-8 mb-3">Article 4 &mdash; Avertissement IA</h2>
            <p className="bg-amber-50 border border-amber-200 rounded-lg p-4 text-amber-900 font-medium">
              Les analyses g&eacute;n&eacute;r&eacute;es par AO Copilot sont produites par intelligence artificielle et constituent une aide &agrave; la d&eacute;cision. Elles ne se substituent en aucun cas &agrave; un conseil juridique, technique ou financier professionnel. L&apos;Utilisateur est seul responsable des d&eacute;cisions prises sur la base des analyses fournies par le Service.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-slate-800 mt-8 mb-3">Article 5 &mdash; Inscription et Compte</h2>
            <p>L&apos;acc&egrave;s au Service n&eacute;cessite la cr&eacute;ation d&apos;un compte utilisateur. L&apos;Utilisateur s&apos;engage &agrave; fournir des informations exactes et &agrave; les maintenir &agrave; jour. Il est responsable de la confidentialit&eacute; de ses identifiants de connexion.</p>
            <p>Chaque compte est rattach&eacute; &agrave; une Organisation. L&apos;administrateur de l&apos;Organisation est responsable de la gestion des membres de son &eacute;quipe.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-slate-800 mt-8 mb-3">Article 6 &mdash; Utilisation du Service</h2>
            <p>L&apos;Utilisateur s&apos;engage &agrave; :</p>
            <ul className="list-disc pl-6 space-y-1 mt-2">
              <li>Utiliser le Service conform&eacute;ment &agrave; sa destination (analyse de DCE BTP)</li>
              <li>Ne pas uploader de contenus illicites, diffamatoires ou portant atteinte aux droits de tiers</li>
              <li>Ne pas tenter de contourner les limitations techniques ou les quotas de son plan</li>
              <li>Ne pas reproduire, copier ou revendre le Service ou ses r&eacute;sultats &agrave; des tiers</li>
              <li>Respecter les lois et r&eacute;glementations applicables, notamment en mati&egrave;re de march&eacute;s publics</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-slate-800 mt-8 mb-3">Article 7 &mdash; Propri&eacute;t&eacute; intellectuelle</h2>
            <p>Le Service, son code source, ses algorithmes, son interface et son contenu &eacute;ditorial sont prot&eacute;g&eacute;s par le droit de la propri&eacute;t&eacute; intellectuelle. L&apos;Utilisateur conserve la propri&eacute;t&eacute; de ses documents upload&eacute;s. Les analyses g&eacute;n&eacute;r&eacute;es par le Service sont la propri&eacute;t&eacute; de l&apos;Utilisateur.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-slate-800 mt-8 mb-3">Article 8 &mdash; Limitation de responsabilit&eacute;</h2>
            <p>AO Copilot ne saurait &ecirc;tre tenu responsable des d&eacute;cisions prises par l&apos;Utilisateur sur la base des analyses g&eacute;n&eacute;r&eacute;es par le Service. Le Service est fourni &laquo; en l&apos;&eacute;tat &raquo;, sans garantie d&apos;exactitude, de compl&eacute;tude ou d&apos;ad&eacute;quation &agrave; un usage particulier.</p>
            <p>En aucun cas la responsabilit&eacute; d&apos;AO Copilot ne pourra exc&eacute;der le montant total pay&eacute; par l&apos;Utilisateur au cours des 12 derniers mois.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-slate-800 mt-8 mb-3">Article 9 &mdash; R&eacute;siliation</h2>
            <p>L&apos;Utilisateur peut r&eacute;silier son compte &agrave; tout moment depuis son espace de gestion d&apos;abonnement. AO Copilot se r&eacute;serve le droit de suspendre ou r&eacute;silier un compte en cas de violation des pr&eacute;sentes CGU, apr&egrave;s notification pr&eacute;alable sauf cas d&apos;urgence.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-slate-800 mt-8 mb-3">Article 10 &mdash; Droit applicable</h2>
            <p>Les pr&eacute;sentes CGU sont r&eacute;gies par le droit fran&ccedil;ais. Tout litige relatif &agrave; leur interpr&eacute;tation ou &agrave; leur ex&eacute;cution sera soumis aux tribunaux comp&eacute;tents de Paris, apr&egrave;s tentative de r&eacute;solution amiable.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-slate-800 mt-8 mb-3">Article 11 &mdash; Contact</h2>
            <p>Pour toute question relative aux pr&eacute;sentes CGU : <a href="mailto:contact@ao-copilot.fr" className="text-blue-600 hover:underline">contact@ao-copilot.fr</a></p>
          </section>
        </div>
      </main>
    </div>
  );
}

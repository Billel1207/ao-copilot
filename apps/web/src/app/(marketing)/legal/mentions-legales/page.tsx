export default function MentionsLegalesPage() {
  return (
    <div className="max-w-3xl mx-auto py-12 px-6">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Mentions légales</h1>

      <section className="mb-8">
        <h2 className="text-xl font-semibold text-gray-800 mb-3">Éditeur du site</h2>
        <div className="text-gray-600 space-y-1">
          <p><span className="font-medium">Dénomination sociale :</span> AO Copilot SAS</p>
          <p><span className="font-medium">Forme juridique :</span> Société par Actions Simplifiée (SAS)</p>
          <p><span className="font-medium">SIRET :</span> [À compléter]</p>
          <p><span className="font-medium">Capital social :</span> [À compléter]</p>
          <p><span className="font-medium">Siège social :</span> Paris, France</p>
          <p><span className="font-medium">Email :</span>{" "}
            <a href="mailto:contact@aocopilot.fr" className="text-blue-600 hover:underline">
              contact@aocopilot.fr
            </a>
          </p>
        </div>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold text-gray-800 mb-3">Directeur de publication</h2>
        <p className="text-gray-600">
          Le directeur de la publication est le représentant légal de AO Copilot SAS.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold text-gray-800 mb-3">Hébergement</h2>
        <div className="text-gray-600 space-y-1">
          <p><span className="font-medium">Hébergeur :</span> Scaleway SAS</p>
          <p><span className="font-medium">Adresse :</span> 8 rue de la Ville l&apos;Évêque, 75008 Paris, France</p>
          <p><span className="font-medium">Site web :</span>{" "}
            <a href="https://www.scaleway.com" className="text-blue-600 hover:underline" target="_blank" rel="noopener noreferrer">
              www.scaleway.com
            </a>
          </p>
          <p className="text-sm text-gray-500 mt-2">
            Les serveurs sont localisés en France (région Paris PAR1), conformément aux exigences RGPD.
          </p>
        </div>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold text-gray-800 mb-3">Propriété intellectuelle</h2>
        <p className="text-gray-600">
          L&apos;ensemble du contenu de ce site (textes, images, interface, code) est la propriété exclusive
          de AO Copilot SAS et est protégé par le droit de la propriété intellectuelle français.
          Toute reproduction, même partielle, est strictement interdite sans autorisation préalable écrite.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold text-gray-800 mb-3">Contact</h2>
        <div className="text-gray-600 space-y-1">
          <p>Pour toute question relative au site ou à nos services :</p>
          <p>
            <a href="mailto:contact@aocopilot.fr" className="text-blue-600 hover:underline">
              contact@aocopilot.fr
            </a>
          </p>
        </div>
      </section>

      <p className="text-xs text-gray-400 mt-12">Dernière mise à jour : mars 2026</p>
    </div>
  );
}

import type { Metadata } from "next";
import Link from "next/link";
import { LegalShell } from "../components/LegalShell";
import { PRODUCT_NAME, SUPPORT_EMAIL, WEBSITE_URL } from "../constants";

export const metadata: Metadata = {
  title: `Algemene voorwaarden | ${PRODUCT_NAME}`,
  description: `Algemene voorwaarden voor het gebruik van ${PRODUCT_NAME}.`,
};

export default function TermsPage() {
  return (
    <LegalShell
      title={{
        nl: "Algemene voorwaarden",
        en: "Terms of Service",
      }}
      updated={{
        nl: "Laatst bijgewerkt: 10 oktober 2026",
        en: "Last updated: 10 October 2026",
      }}
      nl={
        <>
          <p>
            Deze voorwaarden gelden voor het gebruik van {PRODUCT_NAME} (
            {WEBSITE_URL}), inclusief de ChatGPT-app en bijbehorende website.
            Door de dienst te gebruiken, ga je akkoord met deze voorwaarden.
          </p>

          <h2>1. Wat de dienst doet</h2>
          <p>
            {PRODUCT_NAME} helpt ChatGPT om antwoorden te baseren op beschikbare
            supermarktaanbiedingen. In v1 ondersteunen we Picnic-deals. De app
            kan helpen bij vragen over deals, boodschappenlijsten en
            maaltijdideeën.
          </p>

          <h2>2. Wat de dienst niet doet</h2>
          <ul>
            <li>geen bestellingen plaatsen bij supermarkten;</li>
            <li>geen betalingen verwerken;</li>
            <li>geen garantie geven op voorraad, prijs of bezorging;</li>
            <li>
              geen officiële dienst van Picnic, Albert Heijn, Jumbo of OpenAI
              zijn.
            </li>
          </ul>

          <h2>3. Prijzen en actualiteit</h2>
          <p>
            Dealinformatie kan verouderd, onvolledig of onjuist zijn.
            Beschikbaarheid en eindprijzen kunnen per moment verschillen.
            Controleer altijd je winkelmandje bij de retailer voordat je
            bestelt.
          </p>

          <h2>4. Acceptabel gebruik</h2>
          <p>Je mag de dienst niet gebruiken om:</p>
          <ul>
            <li>de dienst te misbruiken, overbelasten of omzeilen;</li>
            <li>illegale activiteiten uit te voeren;</li>
            <li>
              geautomatiseerd op grote schaal te scrapen of te herpubliceren
              buiten normaal ChatGPT-gebruik;
            </li>
            <li>
              te suggereren dat {PRODUCT_NAME} officieel bij een retailer
              hoort.
            </li>
          </ul>

          <h2>5. Intellectuele eigendom</h2>
          <p>
            De merknaam, website, teksten en software van {PRODUCT_NAME} blijven
            ons eigendom. Retailernamen en productnamen blijven van hun
            respectieve eigenaren.
          </p>

          <h2>6. Geen garantie</h2>
          <p>
            De dienst wordt geleverd &quot;as is&quot;. We garanderen niet dat
            de dienst ononderbroken, foutloos of altijd actueel is.
          </p>

          <h2>7. Aansprakelijkheid</h2>
          <p>
            Voor zover wettelijk toegestaan zijn wij niet aansprakelijk voor
            indirecte schade, gemiste besparingen, onjuiste prijzen, of schade
            die voortkomt uit beslissingen die je neemt op basis van de app.
            Onze totale aansprakelijkheid is beperkt tot €50 of het bedrag dat
            je in de voorafgaande 12 maanden aan ons hebt betaald, als dat
            hoger is.
          </p>

          <h2>8. Privacy</h2>
          <p>
            Verwerking van persoonsgegevens staat beschreven in ons{" "}
            <Link href="/privacy">privacybeleid</Link>.
          </p>

          <h2>9. Wijzigingen en beëindiging</h2>
          <p>
            We mogen de dienst of deze voorwaarden wijzigen, of de dienst
            (tijdelijk) stopzetten. Bij materiële wijzigingen passen we de
            datum bovenaan deze pagina aan.
          </p>

          <h2>10. Contact en toepasselijk recht</h2>
          <p>
            Vragen:{" "}
            <a href={`mailto:${SUPPORT_EMAIL}`}>{SUPPORT_EMAIL}</a>. Op deze
            voorwaarden is Nederlands recht van toepassing. Geschillen worden
            voorgelegd aan de bevoegde rechter in Nederland, voor zover
            dwingend recht dat toelaat.
          </p>
        </>
      }
      en={
        <>
          <p>
            These terms govern your use of {PRODUCT_NAME} ({WEBSITE_URL}),
            including the ChatGPT app and related website. By using the
            service, you agree to these terms.
          </p>

          <h2>1. What the service does</h2>
          <p>
            {PRODUCT_NAME} helps ChatGPT ground answers in available
            supermarket promotions. In v1 we support Picnic deals. The app can
            help with deal discovery, grocery lists, and meal ideas.
          </p>

          <h2>2. What the service does not do</h2>
          <ul>
            <li>place supermarket orders;</li>
            <li>process payments;</li>
            <li>guarantee stock, price, or delivery;</li>
            <li>
              act as an official service of Picnic, Albert Heijn, Jumbo, or
              OpenAI.
            </li>
          </ul>

          <h2>3. Prices and freshness</h2>
          <p>
            Deal information may be outdated, incomplete, or incorrect.
            Availability and final prices can change. Always verify your
            basket with the retailer before ordering.
          </p>

          <h2>4. Acceptable use</h2>
          <p>You may not use the service to:</p>
          <ul>
            <li>abuse, overload, or bypass the service;</li>
            <li>carry out illegal activity;</li>
            <li>
              scrape or republish deal data at scale outside normal ChatGPT
              use;
            </li>
            <li>
              imply that {PRODUCT_NAME} is an official retailer product.
            </li>
          </ul>

          <h2>5. Intellectual property</h2>
          <p>
            The {PRODUCT_NAME} brand, website, copy, and software remain our
            property. Retailer and product names remain the property of their
            respective owners.
          </p>

          <h2>6. No warranty</h2>
          <p>
            The service is provided &quot;as is.&quot; We do not warrant that
            it will be uninterrupted, error-free, or always current.
          </p>

          <h2>7. Liability</h2>
          <p>
            To the extent permitted by law, we are not liable for indirect
            damages, missed savings, incorrect prices, or decisions you make
            based on the app. Our total liability is limited to €50 or the
            amount you paid us in the preceding 12 months, whichever is
            higher.
          </p>

          <h2>8. Privacy</h2>
          <p>
            Personal-data processing is described in our{" "}
            <Link href="/privacy">privacy policy</Link>.
          </p>

          <h2>9. Changes and termination</h2>
          <p>
            We may change the service or these terms, or suspend the service.
            For material changes we update the date at the top of this page.
          </p>

          <h2>10. Contact and governing law</h2>
          <p>
            Questions:{" "}
            <a href={`mailto:${SUPPORT_EMAIL}`}>{SUPPORT_EMAIL}</a>. These
            terms are governed by Dutch law. Disputes are submitted to the
            competent courts in the Netherlands, to the extent mandatory law
            allows.
          </p>
        </>
      }
    />
  );
}

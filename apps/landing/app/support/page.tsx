import type { Metadata } from "next";
import Link from "next/link";
import { LegalShell } from "../components/LegalShell";
import { PRODUCT_NAME, SUPPORT_EMAIL, WEBSITE_URL } from "../constants";

export const metadata: Metadata = {
  title: `Support | ${PRODUCT_NAME}`,
  description: `Hulp en contactgegevens voor ${PRODUCT_NAME}.`,
};

export default function SupportPage() {
  return (
    <LegalShell
      title={{
        nl: "Support",
        en: "Support",
      }}
      updated={{
        nl: "We reageren meestal binnen 2 werkdagen",
        en: "We usually reply within 2 business days",
      }}
      nl={
        <>
          <p>
            Hulp nodig bij {PRODUCT_NAME}? Gebruik de informatie hieronder.
          </p>

          <h2>Contact</h2>
          <p>
            E-mail:{" "}
            <a href={`mailto:${SUPPORT_EMAIL}`}>{SUPPORT_EMAIL}</a>
            <br />
            Website: <a href={WEBSITE_URL}>{WEBSITE_URL}</a>
          </p>

          <h2>Veelgestelde vragen</h2>
          <h3>Hoe voeg ik de app toe in ChatGPT?</h3>
          <p>
            Zodra de app is gepubliceerd in de ChatGPT App Directory, kun je
            die daar zoeken en toevoegen. Tot die tijd toont de homepage een
            tijdelijke CTA.
          </p>

          <h3>Welke supermarkten worden ondersteund?</h3>
          <p>
            v1 ondersteunt Picnic. Albert Heijn en Jumbo staan op de
            roadmap.
          </p>

          <h3>Kan de app boodschappen bestellen?</h3>
          <p>
            Nee. De app helpt je deals vinden en een slimme lijst of
            maaltijdplan maken. Bestellen doe je zelf bij de retailer.
          </p>

          <h3>Een prijs lijkt niet te kloppen</h3>
          <p>
            Stuur ons de productnaam, de getoonde prijs, het tijdstip en bij
            voorkeur een screenshot. Controleer ondertussen altijd je
            winkelmandje bij Picnic.
          </p>

          <h3>Privacyverzoek</h3>
          <p>
            Voor inzage of verwijdering van gegevens, mail{" "}
            <a href={`mailto:${SUPPORT_EMAIL}`}>{SUPPORT_EMAIL}</a> met als
            onderwerp &quot;Privacyverzoek&quot;. Zie ook ons{" "}
            <Link href="/privacy">privacybeleid</Link>.
          </p>

          <h2>Handige links</h2>
          <ul>
            <li>
              <Link href="/privacy">Privacybeleid</Link>
            </li>
            <li>
              <Link href="/terms">Algemene voorwaarden</Link>
            </li>
            <li>
              <Link href="/#faq">FAQ op de homepage</Link>
            </li>
          </ul>
        </>
      }
      en={
        <>
          <p>Need help with {PRODUCT_NAME}? Use the information below.</p>

          <h2>Contact</h2>
          <p>
            Email:{" "}
            <a href={`mailto:${SUPPORT_EMAIL}`}>{SUPPORT_EMAIL}</a>
            <br />
            Website: <a href={WEBSITE_URL}>{WEBSITE_URL}</a>
          </p>

          <h2>Common questions</h2>
          <h3>How do I add the app in ChatGPT?</h3>
          <p>
            Once the app is published in the ChatGPT App Directory, search for
            it there and add it. Until then, the homepage shows a temporary
            CTA.
          </p>

          <h3>Which supermarkets are supported?</h3>
          <p>
            v1 supports Picnic. Albert Heijn and Jumbo are on the roadmap.
          </p>

          <h3>Can the app order groceries?</h3>
          <p>
            No. The app helps you find deals and build a smart list or meal
            plan. You place the order with the retailer yourself.
          </p>

          <h3>A price looks wrong</h3>
          <p>
            Email us the product name, shown price, timestamp, and preferably
            a screenshot. In the meantime, always verify your basket in
            Picnic.
          </p>

          <h3>Privacy request</h3>
          <p>
            To request access or deletion, email{" "}
            <a href={`mailto:${SUPPORT_EMAIL}`}>{SUPPORT_EMAIL}</a> with the
            subject &quot;Privacy request.&quot; See also our{" "}
            <Link href="/privacy">privacy policy</Link>.
          </p>

          <h2>Useful links</h2>
          <ul>
            <li>
              <Link href="/privacy">Privacy policy</Link>
            </li>
            <li>
              <Link href="/terms">Terms of service</Link>
            </li>
            <li>
              <Link href="/#faq">Homepage FAQ</Link>
            </li>
          </ul>
        </>
      }
    />
  );
}

import type { Metadata } from "next";
import { LegalShell } from "../components/LegalShell";
import { PRODUCT_NAME, SUPPORT_EMAIL, WEBSITE_URL } from "../constants";

export const metadata: Metadata = {
  title: `Privacybeleid | ${PRODUCT_NAME}`,
  description: `Privacybeleid van ${PRODUCT_NAME}: welke gegevens we verwerken, waarom, en hoe je contact opneemt.`,
};

export default function PrivacyPage() {
  return (
    <LegalShell
      title={{
        nl: "Privacybeleid",
        en: "Privacy Policy",
      }}
      updated={{
        nl: "Laatst bijgewerkt: 10 oktober 2026",
        en: "Last updated: 10 October 2026",
      }}
      nl={
        <>
          <p>
            Dit privacybeleid beschrijft hoe {PRODUCT_NAME} ({WEBSITE_URL})
            persoonsgegevens verwerkt wanneer je onze ChatGPT-app, website of
            supportkanalen gebruikt.
          </p>

          <h2>1. Wie is verantwoordelijk?</h2>
          <p>
            De verwerkingsverantwoordelijke is {PRODUCT_NAME}. Voor
            privacyvragen kun je mailen naar{" "}
            <a href={`mailto:${SUPPORT_EMAIL}`}>{SUPPORT_EMAIL}</a>.
          </p>

          <h2>2. Welke gegevens verwerken we?</h2>
          <ul>
            <li>
              <strong>Technische app-identiteit.</strong> Als ChatGPT een
              geanonimiseerde <code>openai/subject</code> meestuurt, maken we
              daarvan een HMAC-hash. Die hash gebruiken we als stabiele
              analysekoppeling. De ruwe subject-waarde wordt niet opgeslagen in
              PostHog.
            </li>
            <li>
              <strong>Gebruik van tools.</strong> We registreren dat een tool
              is aangeroepen, welke tool het was, het resultaat
              (succes/fouttype), duur, en begrensde toolparameters. Resultaten
              van tools, ruwe foutteksten, IP-adressen en volledige headers
              worden niet naar PostHog gestuurd.
            </li>
            <li>
              <strong>Operationele auditlogs.</strong> Onze servers schrijven
              auditlogs van MCP-verkeer voor betrouwbaarheid, beveiliging en
              debugging. Gevoelige velden zoals tokens en wachtwoorden worden
              geredacteerd.
            </li>
            <li>
              <strong>Websitegegevens.</strong> Onze website kan standaard
              serverlogs en beveiligingsmetadata verwerken die nodig zijn om de
              site te hosten.
            </li>
            <li>
              <strong>Supportberichten.</strong> Als je ons mailt, verwerken we
              je e-mailadres en de inhoud van je bericht.
            </li>
          </ul>

          <h2>3. Doeleinden</h2>
          <ul>
            <li>de ChatGPT-app leveren en verbeteren;</li>
            <li>misbruik, storingen en kwaliteit monitoren;</li>
            <li>supportvragen beantwoorden;</li>
            <li>voldoen aan wettelijke verplichtingen.</li>
          </ul>

          <h2>4. Rechtsgrondslagen</h2>
          <p>
            We verwerken gegevens op basis van gerechtvaardigd belang
            (productwerking, beveiliging, analytics zonder account) en, waar
            van toepassing, uitvoering van een overeenkomst of wettelijke
            verplichting. Voor supportcommunicatie is de grondslag meestal
            jouw verzoek om contact.
          </p>

          <h2>5. Ontvangers</h2>
          <ul>
            <li>
              <strong>PostHog</strong> voor productanalytics (EU-hosting
              wanneer zo geconfigureerd).
            </li>
            <li>
              <strong>Hosting- en infrastructuurleveranciers</strong> die onze
              servers, netwerk of logging ondersteunen.
            </li>
            <li>
              <strong>OpenAI / ChatGPT</strong> als platform waarop je de app
              gebruikt; hun verwerking valt onder hun eigen voorwaarden en
              privacybeleid.
            </li>
          </ul>

          <h2>6. Bewaartermijnen</h2>
          <ul>
            <li>
              Analyticsgebeurtenissen: standaard maximaal 24 maanden, tenzij
              een kortere retentie is ingesteld.
            </li>
            <li>
              Auditlogs: maximaal 90 dagen, tenzij langer nodig is voor
              beveiligingsonderzoek.
            </li>
            <li>
              Supportmails: maximaal 24 maanden na afronding van het verzoek,
              tenzij langer nodig is voor juridische redenen.
            </li>
          </ul>

          <h2>7. Gevoelige promptinhoud</h2>
          <p>
            Stuur geen medische, allergie- of andere gevoelige gegevens mee
            tenzij dat nodig is voor je vraag. Toolparameters kunnen
            analytisch worden vastgelegd. We raden aan die gegevens zo beperkt
            mogelijk te houden.
          </p>

          <h2>8. Jouw rechten</h2>
          <p>
            Onder de AVG kun je verzoeken om inzage, rectificatie, verwijdering,
            beperking, bezwaar of dataportabiliteit. Mail{" "}
            <a href={`mailto:${SUPPORT_EMAIL}`}>{SUPPORT_EMAIL}</a>. Je kunt
            ook een klacht indienen bij de Autoriteit Persoonsgegevens.
          </p>

          <h2>9. Beveiliging</h2>
          <p>
            We gebruiken HTTPS, redaction van gevoelige velden, en beperkte
            toegang tot logs en analytics. Geen beveiligingsmaatregel is
            absoluut.
          </p>

          <h2>10. Wijzigingen</h2>
          <p>
            We kunnen dit beleid bijwerken. De datum bovenaan deze pagina
            toont de laatste wijziging.
          </p>
        </>
      }
      en={
        <>
          <p>
            This privacy policy explains how {PRODUCT_NAME} ({WEBSITE_URL})
            processes personal data when you use our ChatGPT app, website, or
            support channels.
          </p>

          <h2>1. Controller</h2>
          <p>
            The controller is {PRODUCT_NAME}. For privacy questions, email{" "}
            <a href={`mailto:${SUPPORT_EMAIL}`}>{SUPPORT_EMAIL}</a>.
          </p>

          <h2>2. Data we process</h2>
          <ul>
            <li>
              <strong>Technical app identity.</strong> When ChatGPT sends an
              anonymized <code>openai/subject</code>, we derive an HMAC hash
              and use it as a stable analytics key. The raw subject is not
              stored in PostHog.
            </li>
            <li>
              <strong>Tool usage.</strong> We record that a tool was called,
              which tool, outcome (success/error type), duration, and bounded
              tool parameters. Tool results, raw error messages, IP addresses,
              and full headers are not sent to PostHog.
            </li>
            <li>
              <strong>Operational audit logs.</strong> Our servers write MCP
              audit logs for reliability, security, and debugging. Sensitive
              fields such as tokens and passwords are redacted.
            </li>
            <li>
              <strong>Website data.</strong> Our website may process standard
              server logs and security metadata needed to host the site.
            </li>
            <li>
              <strong>Support messages.</strong> If you email us, we process
              your email address and message content.
            </li>
          </ul>

          <h2>3. Purposes</h2>
          <ul>
            <li>provide and improve the ChatGPT app;</li>
            <li>monitor abuse, outages, and quality;</li>
            <li>answer support requests;</li>
            <li>comply with legal obligations.</li>
          </ul>

          <h2>4. Legal bases</h2>
          <p>
            We process data based on legitimate interests (product operation,
            security, pre-account analytics) and, where applicable, contract
            performance or legal obligation. Support correspondence is usually
            based on your request for contact.
          </p>

          <h2>5. Recipients</h2>
          <ul>
            <li>
              <strong>PostHog</strong> for product analytics (EU hosting when
              configured).
            </li>
            <li>
              <strong>Hosting and infrastructure providers</strong> that
              support our servers, networking, or logging.
            </li>
            <li>
              <strong>OpenAI / ChatGPT</strong> as the platform where you use
              the app; their processing is governed by their own terms and
              privacy policy.
            </li>
          </ul>

          <h2>6. Retention</h2>
          <ul>
            <li>
              Analytics events: up to 24 months by default, unless a shorter
              retention is configured.
            </li>
            <li>
              Audit logs: up to 90 days, unless longer retention is needed for
              a security investigation.
            </li>
            <li>
              Support emails: up to 24 months after the request is closed,
              unless longer retention is required for legal reasons.
            </li>
          </ul>

          <h2>7. Sensitive prompt content</h2>
          <p>
            Do not include medical, allergy, or other sensitive details unless
            needed for your request. Tool parameters may be captured for
            analytics. Keep such details to a minimum.
          </p>

          <h2>8. Your rights</h2>
          <p>
            Under the GDPR you may request access, rectification, erasure,
            restriction, objection, or portability. Email{" "}
            <a href={`mailto:${SUPPORT_EMAIL}`}>{SUPPORT_EMAIL}</a>. You may
            also lodge a complaint with your local supervisory authority.
          </p>

          <h2>9. Security</h2>
          <p>
            We use HTTPS, redaction of sensitive fields, and limited access to
            logs and analytics. No security measure is absolute.
          </p>

          <h2>10. Changes</h2>
          <p>
            We may update this policy. The date at the top of this page shows
            the latest change.
          </p>
        </>
      }
    />
  );
}

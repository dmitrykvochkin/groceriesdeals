"use client";

import Image from "next/image";
import { DemoVideo } from "./components/DemoVideo";
import { useEffect, useState } from "react";
import { Brand } from "./components/Brand";
import { BrandMark } from "./components/BrandMark";
import { LanguageSwitch, type Language } from "./components/LanguageSwitch";
import { SiteFooter } from "./components/SiteFooter";
import { PRODUCT_NAME } from "./constants";

const copy = {
  nl: {
    navHow: "Zo werkt het",
    navFaq: "Veelgestelde vragen",
    availability: "Nu met Picnic",
    eyebrow: "Bespaar op elke boodschappenlijst",
    titleStart: "Bespaar tot 30%",
    titleAccent: "op online boodschappen.",
    intro:
      "Laat ChatGPT je boodschappenlijst maken met de beste actuele acties. Zo geef je minder uit, zonder zelf alle aanbiedingen af te gaan.",
    primaryCta: "Add to my ChatGPT",
    supportedLabel: "Ondersteunde supermarkten",
    picnicLabel: "Actuele deals",
    ahLabel: "Albert Heijn",
    soon: "Binnenkort",
    prompt: "Maak een gezonde boodschappenlijst voor 3 avondmaaltijden onder €40.",
    answerIntro: "Hier is je voordelige lijst bij Picnic:",
    saved: "Tot 30% goedkoper met actuele deals",
    live: "Actuele Picnic-deals",
    composerPlaceholder: "Vraag iets",
    chatDisclaimer: "ChatGPT kan fouten maken. Controleer belangrijke informatie.",
    howEyebrow: "Zo werkt het",
    howIntro:
      `ChatGPT begrijpt wat je nodig hebt. ${PRODUCT_NAME} brengt de actuele supermarktdeals. Samen maken ze een slimme boodschappenlijst waarmee jij bespaart.`,
    steps: [
      {
        title: "Vertel ChatGPT wat je nodig hebt",
        body: "Deel je budget, je huishouden of wat je deze week wilt koken, gewoon in je chat.",
      },
      {
        title: "brengt de deals",
        body: `ChatGPT gebruikt de actuele supermarktdeals van ${PRODUCT_NAME} om slimme keuzes te maken.`,
      },
      {
        title: "Samen maken ze jouw lijst",
        body: "Je krijgt een voordelige boodschappenlijst direct in ChatGPT.",
      },
    ],
    demoBadge: "1 min. 35 sec. demo",
    demoCaption: "Zonder geluid · Engelse ondertiteling",
    demoLink: "Bekijk de volledige demo",
    faqEyebrow: "Goed om te weten",
    faqTitle: "Veelgestelde vragen",
    faqs: [
      {
        q: `Wat doet ${PRODUCT_NAME} precies?`,
        a: `${PRODUCT_NAME} is een app voor ChatGPT die actuele supermarktdeals gebruikt om jouw vragen te beantwoorden. Vraag bijvoorbeeld naar gezonde aanbiedingen, een voordelig weekmenu of snacks binnen een bepaald budget.`,
      },
      {
        q: "Welke supermarkten worden ondersteund?",
        a: "We starten met Picnic. Ondersteuning voor Albert Heijn en Jumbo staat op de planning en volgt binnenkort.",
      },
      {
        q: "Zijn de aanbiedingen altijd actueel?",
        a: "De app gebruikt de meest recente dealinformatie die beschikbaar is. Prijzen en beschikbaarheid kunnen per moment of locatie verschillen; controleer daarom altijd je winkelmandje.",
      },
      {
        q: "Kan de app mijn boodschappen bestellen?",
        a: "Nog niet. De app helpt je om relevante deals te vinden en slimme keuzes te maken. Bestellen doe je daarna zelf bij de supermarkt.",
      },
    ],
  },
  en: {
    navHow: "How it works",
    navFaq: "FAQ",
    availability: "Now with Picnic",
    eyebrow: "Save on every grocery list",
    titleStart: "Save up to 30%",
    titleAccent: "on online groceries.",
    intro:
      "Let ChatGPT build your grocery list with the best current deals. Spend less without comparing every offer yourself.",
    primaryCta: "Add to my ChatGPT",
    supportedLabel: "Supported supermarkets",
    picnicLabel: "Current deals",
    ahLabel: "Albert Heijn",
    soon: "Coming soon",
    prompt: "Build a healthy grocery list for 3 dinners under €40.",
    answerIntro: "Here’s your better-value Picnic list:",
    saved: "Save up to 30% with current deals",
    live: "Current Picnic deals",
    composerPlaceholder: "Message ChatGPT",
    chatDisclaimer: "ChatGPT can make mistakes. Check important info.",
    howEyebrow: "How it works",
    howIntro:
      `ChatGPT understands what you need. ${PRODUCT_NAME} brings the current supermarket deals. Together, they build a smart grocery list that saves you money.`,
    steps: [
      {
        title: "Tell ChatGPT what you need",
        body: "Share your budget, household, or what you want to cook this week, right in your chat.",
      },
      {
        title: "brings the deals",
        body: `ChatGPT uses ${PRODUCT_NAME}’s current supermarket deals to make smarter choices.`,
      },
      {
        title: "Together, they build your list",
        body: "You get a money-saving grocery list directly in ChatGPT.",
      },
    ],
    demoBadge: "1 min. 35 sec. demo",
    demoCaption: "Silent · English captions",
    demoLink: "Watch the full demo",
    faqEyebrow: "Good to know",
    faqTitle: "Frequently asked questions",
    faqs: [
      {
        q: `What does ${PRODUCT_NAME} do?`,
        a: `${PRODUCT_NAME} is a ChatGPT app that uses current supermarket deals to answer your questions. Ask for healthy offers, a budget-friendly weekly menu, or snacks within a specific budget.`,
      },
      {
        q: "Which supermarkets are supported?",
        a: "We’re starting with Picnic. Albert Heijn and Jumbo support are on our roadmap and coming soon.",
      },
      {
        q: "Are the offers always up to date?",
        a: "The app uses the latest deal information available. Prices and availability can vary by time or location, so always check your basket before ordering.",
      },
      {
        q: "Can the app order my groceries?",
        a: "Not yet. The app helps you discover relevant deals and make smarter choices. You complete the order with the supermarket yourself.",
      },
    ],
  },
} as const;

const products = [
  { emoji: "🥒", nl: "Courgette", en: "Courgette", price: "€0,99", deal: "−30%" },
  { emoji: "🥣", nl: "Havermout", en: "Oats", price: "€1,49", deal: "−25%" },
  { emoji: "🫐", nl: "Blauwe bessen", en: "Blueberries", price: "€2,29", deal: "−20%" },
] as const;

export default function Home() {
  const [language, setLanguage] = useState<Language>("nl");
  const t = copy[language];

  useEffect(() => {
    document.documentElement.lang = language;
  }, [language]);

  return (
    <main id="top">
      <header className="siteHeader">
        <div className="container navInner">
          <Brand href="#top" />

          <nav className="desktopNav" aria-label={language === "nl" ? "Hoofdnavigatie" : "Main navigation"}>
            <a href="#how">{t.navHow}</a>
            <a href="#faq">{t.navFaq}</a>
          </nav>

          <div className="navActions">
            <div className="availabilityPill">
              <span aria-hidden="true" />
              {t.availability}
            </div>
            <LanguageSwitch language={language} onChange={setLanguage} />
          </div>
        </div>
      </header>

      <section className="hero">
        <div className="heroOrb heroOrbOne" aria-hidden="true" />
        <div className="heroOrb heroOrbTwo" aria-hidden="true" />
        <div className="container heroGrid">
          <div className="heroCopy">
            <p className="eyebrow"><span>✦</span>{t.eyebrow}</p>
            <h1>
              {t.titleStart}<br />
              <span>{t.titleAccent}</span>
            </h1>
            <p className="heroIntro">{t.intro}</p>
            <div className="heroActions">
              {/* Replace this URL with the final ChatGPT app listing when it is available. */}
              <a className="button buttonPrimary" href="https://chatgpt.com/" target="_blank" rel="noreferrer">
                <span className="chatGptButtonIcon" aria-hidden="true">
                  <Image src="/ChatGPTLogo.png" alt="" width={48} height={27} />
                </span>
                <span className="buttonLabel">{t.primaryCta}</span>
                <span className="chatGptButtonArrow" aria-hidden="true">↗</span>
              </a>
            </div>
            <p className="eyebrow providerEyebrow"><span>✦</span>{t.supportedLabel}</p>
            <div className="providerRow" aria-label={t.supportedLabel}>
              <div className="provider providerLive">
                <span className="picnicLogo" aria-hidden="true">P</span>
                <span><strong>Picnic</strong><small>{t.picnicLabel}</small></span>
              </div>
              <div className="provider providerSoon">
                <span className="retailerLogo retailerLogoAh" aria-hidden="true">
                  <Image src="/ab_hijn.png" alt="" width={56} height={28} />
                </span>
                <span><strong>{t.ahLabel}</strong><small>{t.soon}</small></span>
              </div>
              <div className="provider providerSoon">
                <span className="retailerLogo retailerLogoJumbo" aria-hidden="true">
                  <Image src="/jumbo.png" alt="" width={29} height={29} />
                </span>
                <span><strong>Jumbo</strong><small>{t.soon}</small></span>
              </div>
            </div>
          </div>

          <div className="productVisual" aria-label={language === "nl" ? "Voorbeeld van een gesprek met de app" : "Example conversation with the app"}>
            <div className="chatCard">
              <div className="chatTopbar">
                <span className="chatSidebarIcon" aria-hidden="true">
                  <span />
                </span>
                <div className="chatTitle">
                  <strong>ChatGPT</strong>
                  <span aria-hidden="true">⌄</span>
                </div>
                <div className="chatTopbarActions" aria-hidden="true">
                  <span className="chatShareIcon">↗</span>
                  <span className="chatNewIcon"><span /></span>
                </div>
              </div>

              <div className="chatConversation">
                <div className="message userMessage">{t.prompt}</div>
                <div className="message assistantMessage">
                  <div className="assistantIcon" aria-hidden="true">
                    <Image src="/ChatGPTLogo.png" alt="" width={24} height={24} />
                  </div>
                  <div className="answerBody">
                    <p>{t.answerIntro}</p>
                    <div className="dealList">
                      {products.map((product) => (
                        <div className="dealItem" key={product.nl}>
                          <span className="productEmoji" aria-hidden="true">{product.emoji}</span>
                          <span className="productName">{product[language]}</span>
                          <strong>{product.price}</strong>
                          <span className="dealBadge">{product.deal}</span>
                        </div>
                      ))}
                    </div>
                    <div className="savingLine"><span aria-hidden="true">✓</span>{t.saved}</div>
                    <div className="assistantActions" aria-hidden="true">
                      <span>⧉</span>
                      <span>♡</span>
                      <span>↻</span>
                    </div>
                  </div>
                </div>
              </div>
              <div className="chatComposer" aria-hidden="true">
                <span className="composerPlaceholder">{t.composerPlaceholder}</span>
                <div className="composerToolbar">
                  <span className="composerAdd">+</span>
                  <span className="composerTool"><BrandMark className="miniBrand" />{PRODUCT_NAME}</span>
                  <span className="composerMic" />
                  <b>↑</b>
                </div>
              </div>
              <p className="chatDisclaimer">{t.chatDisclaimer}</p>
            </div>
            <div className="floatingTag tagTop"><span>●</span> LIVE</div>
            <div className="floatingTag tagBottom">🥕 + 🧠</div>
          </div>
        </div>
      </section>

      <section className="howSection" id="how">
        <div className="container">
          <div className="sectionHeading">
            <div>
              <p className="eyebrow"><span>✦</span>{t.howEyebrow}</p>
              <h2 className="partnershipTitle">
                <span>ChatGPT</span>
                <span className="partnershipPlus">+</span>
                <span className="partnershipProduct">{PRODUCT_NAME}</span>
              </h2>
            </div>
            <p>{t.howIntro}</p>
          </div>

          <div className="howGrid">
            <div className="steps">
              {t.steps.map((step, index) => (
                <article className="step" key={step.title}>
                  <span className="stepNumber">0{index + 1}</span>
                  <div>
                    <h3>
                      {index === 1 && <><span className="partnershipProduct">{PRODUCT_NAME}</span>{" "}</>}
                      {step.title}
                    </h3>
                    <p>{step.body}</p>
                  </div>
                </article>
              ))}
            </div>

            <div className="demoFrame">
              <DemoVideo />
              <div className="demoFooter">
                <span className="demoBadge"><i />{t.demoBadge}</span>
                <span>{t.demoCaption}</span>
                <a href="/review/demo">{t.demoLink} ↗</a>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="faqSection" id="faq">
        <div className="container faqGrid">
          <div className="faqIntro">
            <p className="eyebrow"><span>✦</span>{t.faqEyebrow}</p>
            <h2>{t.faqTitle}</h2>
            <div className="faqIllustration" aria-hidden="true">
              <span className="tomato">🍅</span>
              <span className="speech">?</span>
            </div>
          </div>
          <div className="faqList">
            {t.faqs.map((faq, index) => (
              <details key={faq.q} open={index === 0}>
                <summary>
                  <span>{faq.q}</span>
                  <i aria-hidden="true" />
                </summary>
                <p>{faq.a}</p>
              </details>
            ))}
          </div>
        </div>
      </section>

      <SiteFooter language={language} homeHref="#top" />
    </main>
  );
}

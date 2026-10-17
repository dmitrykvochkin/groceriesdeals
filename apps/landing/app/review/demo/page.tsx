import type { Metadata } from "next";
import { Brand } from "../../components/Brand";
import { DemoVideo } from "../../components/DemoVideo";
import { SiteFooter } from "../../components/SiteFooter";
import styles from "./page.module.css";

export const metadata: Metadata = {
  title: "Save money on groceries with ChatGPT | KortingZoeker",
  description: "KortingZoeker brings current supermarket offers into your ChatGPT conversations, helping you plan meals around deals and spend less on groceries. Currently supporting Picnic.",
};

const benefits = [
  { number: "01", title: "Make the most of current deals.", body: "Find Picnic offers that fit what you want to cook. Plan around discounted ingredients to help your grocery budget go further." },
  { number: "02", title: "A budget you can plan around.", body: "Give ChatGPT your household size and spending target. Use deal prices to shape meal ideas, with estimates for other ingredients clearly separated." },
  { number: "03", title: "A list you can actually use.", body: "Turn meal ideas into one grocery list. Shared ingredients make the plan easier to shop for, and you decide what to buy at the retailer." },
];

export default function DemoPage() {
  return (
    <main id="top" lang="en" className={styles.page}>
      <header className={styles.header}>
        <div className={`container ${styles.nav}`}>
          <Brand />
          <a href="#demo" className={styles.navLink}>Watch the demo <span aria-hidden="true">↗</span></a>
        </div>
      </header>

      <section className={`container ${styles.hero}`} aria-labelledby="demo-title">
        <div className={styles.kicker}><span /> Current Picnic deals, inside ChatGPT</div>
        <h1 id="demo-title">Save money<br /><em>on your groceries.</em></h1>
        <p className={styles.intro}>KortingZoeker brings current supermarket offers into your ChatGPT conversations, helping you spend less on the meals you want to make. Share your budget and what you like to eat, then turn available deals into meal ideas and one practical shopping list.</p>
        <a className={styles.primaryLink} href="#demo">See it in action <span aria-hidden="true">↓</span></a>
        <span className={styles.heroNote}>95 seconds · No sound needed</span>
        <div className={styles.benefits}>
          {benefits.map((benefit) => <article key={benefit.number} className={styles.benefit}>
            <span className={styles.number}>{benefit.number}</span>
            <h2>{benefit.title}</h2>
            <p>{benefit.body}</p>
          </article>)}
        </div>
      </section>

      <section id="demo" className={styles.watch} aria-labelledby="watch-title">
        <div className="container">
          <div className={styles.sectionHeading}>
            <div><p className={styles.label}>THE PRODUCT IN PRACTICE</p><h2 id="watch-title">From “what’s for dinner?” to a plan.</h2></div>
            <span className={styles.videoMeta}>1:35 <span aria-hidden="true">/</span> English captions · Silent</span>
          </div>
          <div className={styles.player}><DemoVideo /></div>
          <div className={styles.videoFooter}><p>A real walkthrough: one request, three dinners and a combined grocery list.</p><a href="/korting_zoeker_demo_001_captioned.mp4">Open video <span aria-hidden="true">↗</span></a></div>
        </div>
      </section>

      <section className={`container ${styles.useCase}`} aria-labelledby="case-title">
        <div className={styles.caseIntro}><p className={styles.label}>THE USE CASE</p><h2 id="case-title">Three dinners.<br />Four people.<br />A €40 target.</h2><p>The demo starts with a familiar challenge: feed the household, keep meals varied and stay within a budget.</p><blockquote>“I want three healthy dinners for four people under a forty-euro target, using Picnic deals where possible.”</blockquote></div>
        <div className={styles.caseDetails}>
          <article className={styles.caseStep}><span className={styles.number}>01</span><div><h3>Find deals that can shape the plan</h3><p>KortingZoeker supplies current Picnic discounts. ChatGPT uses those offers to suggest salmon with potatoes and spinach, courgette bolognese, and a pumpkin, chickpea and minced-meat chili.</p></div></article>
          <article className={styles.caseStep}><span className={styles.number}>02</span><div><h3>See what the groceries could cost</h3><p>Ingredients are combined into one list, with minced meat shared across two dinners. Deal-backed prices and estimates for other groceries are shown separately.</p></div></article>
          <div className={styles.budget}>
            <p className={styles.budgetLabel}>THE ESTIMATE IN THIS DEMO</p>
            <dl><div><dt>Groceries with deal-backed prices</dt><dd>€27.53</dd></div><div><dt>Other groceries <span>estimated</span></dt><dd>€10.10</dd></div><div className={styles.total}><dt>Estimated total</dt><dd>€37.63</dd></div></dl>
            <p className={styles.budgetNote}>€2.37 below the €40 target</p>
          </div>
          <article className={styles.caseStep}><span className={styles.number}>03</span><div><h3>Keep the purchase in your hands</h3><p>The demo then asks the app to order and pay. It explains that it cannot place orders, add items to a Picnic basket or process payments. You take your list to the retailer and complete checkout yourself.</p></div></article>
        </div>
      </section>
      <div className={`container ${styles.context}`}><p><strong>A planning example, not a live price quote.</strong> Prices reflect the deals available when the demo was recorded. Other grocery prices are estimates, and the plan assumes cooking oil, salt, pepper and basic herbs or spices at home. Final prices, availability and any delivery charges must be checked at the retailer.</p></div>
      <SiteFooter language="en" />
    </main>
  );
}

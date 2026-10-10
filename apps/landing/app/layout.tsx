import type { Metadata } from "next";
import { headers } from "next/headers";
import type { ReactNode } from "react";
import { PRODUCT_NAME } from "./constants";
import "./globals.css";

const title = `${PRODUCT_NAME} — slimme boodschappenlijsten met actuele deals`;
const description =
  "Laat ChatGPT een slimme boodschappenlijst of maaltijdplan maken met actuele Picnic-deals via kortingzoeker.com.";

export async function generateMetadata(): Promise<Metadata> {
  const requestHeaders = await headers();
  const host = (requestHeaders.get("x-forwarded-host") ?? requestHeaders.get("host") ?? "localhost:3438")
    .split(",")[0]
    .trim();
  const forwardedProtocol = requestHeaders.get("x-forwarded-proto")?.split(",")[0].trim();
  const protocol = forwardedProtocol ?? (host.startsWith("localhost") ? "http" : "https");
  const origin = `${protocol}://${host}`;

  return {
    metadataBase: new URL(origin),
    title,
    description,
    openGraph: {
      type: "website",
      locale: "nl_NL",
      siteName: PRODUCT_NAME,
      title,
      description,
      images: [
        {
          url: `${origin}/og.png`,
          width: 1200,
          height: 630,
          alt: title,
        },
      ],
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
      images: [`${origin}/og.png`],
    },
  };
}

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="nl">
      <body>{children}</body>
    </html>
  );
}

import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";
import { Header } from "@/components/header";

export const metadata: Metadata = {
  title: "NewsMind | A clearer view of your world",
  description:
    "Daily news, thoughtfully organized. Regional perspectives, reliable attribution, and a calm reading experience.",
};
const themeScript = `(function(){try{var t=localStorage.getItem('newsmind-theme')||'system';document.documentElement.dataset.theme=t==='system'?(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'):t}catch(e){}})()`;
export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body>
        <a className="skip-link" href="#main">
          Skip to news
        </a>
        <Header />
        <main id="main" className="page-width">
          {children}
        </main>
        <footer className="page-width footer">
          <Link className="wordmark" href="/">
            NewsMind<span>.</span>
          </Link>
          <p>A clearer view of your world.</p>
          <span>News is available for four days from publication.</span>
        </footer>
      </body>
    </html>
  );
}

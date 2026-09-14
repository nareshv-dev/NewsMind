"use client";
import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { Suspense, useSyncExternalStore, useState } from "react";
import {
  Search,
  Sun,
  Moon,
  Monitor,
  Bookmark,
  UserRound,
  Menu,
  X,
  ArrowUpRight,
} from "lucide-react";
import { categories } from "@/lib/types";

function savedTheme() {
  try {
    const value = localStorage.getItem("newsmind-theme");
    return value && ["system", "light", "dark"].includes(value)
      ? value
      : "system";
  } catch {
    return "system";
  }
}
function subscribeTheme(callback: () => void) {
  const media = matchMedia("(prefers-color-scheme: dark)");
  const sync = () => {
    const value = savedTheme();
    document.documentElement.dataset.theme =
      value === "system" ? (media.matches ? "dark" : "light") : value;
    callback();
  };
  sync();
  window.addEventListener("storage", sync);
  window.addEventListener("newsmind-theme-change", sync);
  media.addEventListener("change", sync);
  return () => {
    window.removeEventListener("storage", sync);
    window.removeEventListener("newsmind-theme-change", sync);
    media.removeEventListener("change", sync);
  };
}

function Navigation() {
  const pathname = usePathname();
  const params = useSearchParams();
  const theme = useSyncExternalStore(
    subscribeTheme,
    savedTheme,
    () => "system",
  );
  const [mobile, setMobile] = useState(false);
  function toggleTheme() {
    const next =
      theme === "system" ? "dark" : theme === "dark" ? "light" : "system";
    localStorage.setItem("newsmind-theme", next);
    window.dispatchEvent(new Event("newsmind-theme-change"));
  }
  return (
    <header className="header">
      <div className="topline page-width">
        <span>INDEPENDENT PERSPECTIVES. INFORMED DAYS.</span>
        <Link href="/search">
          Explore the latest <ArrowUpRight size={13} aria-hidden />
        </Link>
      </div>
      <div className="masthead page-width">
        <div className="brand">
          <Link href="/" className="wordmark">
            NewsMind<span>.</span>
          </Link>
          <span className="brand-caption">YOUR WORLD, IN PERSPECTIVE</span>
        </div>
        <form action="/search" className="header-search" role="search">
          <Search size={18} aria-hidden />
          <label className="sr-only" htmlFor="header-query">
            Search news
          </label>
          <input
            key={params.get("q")}
            id="header-query"
            name="q"
            defaultValue={params.get("q") || ""}
            placeholder="Find a story, topic or perspective"
          />
          <button type="submit" aria-label="Submit search" title="Search">
            <ArrowUpRight size={18} />
          </button>
        </form>
        <div className="header-actions">
          <button
            onClick={toggleTheme}
            className="icon-button"
            title={`Theme: ${theme}. Switch theme`}
            aria-label={`Theme: ${theme}. Switch theme`}
          >
            {theme === "dark" ? (
              <Moon size={19} />
            ) : theme === "light" ? (
              <Sun size={19} />
            ) : (
              <Monitor size={19} />
            )}
          </button>
          <Link
            href="/bookmarks"
            className="icon-button"
            title="Saved articles"
            aria-label="Saved articles"
          >
            <Bookmark size={19} />
          </Link>
          <Link
            href="/account"
            className="account-link"
            aria-label="Sign in"
            title="Sign in"
          >
            <UserRound size={17} aria-hidden />
            <span>Sign in</span>
          </Link>
          <button
            className="icon-button menu-toggle"
            aria-label="Category menu"
            aria-expanded={mobile}
            onClick={() => setMobile(!mobile)}
          >
            {mobile ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </div>
      <nav
        className={`category-nav page-width ${mobile ? "open" : ""}`}
        aria-label="News categories"
      >
        <Link
          href="/"
          className={pathname === "/" ? "active" : ""}
          onClick={() => setMobile(false)}
        >
          For you
        </Link>
        {categories.map((c) => (
          <Link
            key={c.slug}
            href={`/category/${c.slug}`}
            className={pathname === `/category/${c.slug}` ? "active" : ""}
            onClick={() => setMobile(false)}
          >
            {c.name}
          </Link>
        ))}
        <span className="nav-note">A little clarity, every day.</span>
      </nav>
    </header>
  );
}
export function Header() {
  return (
    <Suspense
      fallback={
        <header className="page-width masthead">
          <Link href="/" className="wordmark">
            NewsMind.
          </Link>
        </header>
      }
    >
      <Navigation />
    </Suspense>
  );
}

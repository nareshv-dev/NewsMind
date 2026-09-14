"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import {
  ArrowRight,
  ArrowUpRight,
  SlidersHorizontal,
  RefreshCw,
  Newspaper,
  Globe2,
  MoveRight,
  ChevronLeft,
  ChevronRight,
  X,
} from "lucide-react";
import { api } from "@/lib/api";
import { categories, type Page, type Article, type Health } from "@/lib/types";
import { ArticleCard, StoryImage, Timestamp } from "@/components/article-card";

export function Feed({
  category,
  search = false,
}: {
  category?: string;
  search?: boolean;
}) {
  const params = useSearchParams();
  const pathname = usePathname();
  const router = useRouter();
  const [response, setResponse] = useState<{
    key: string;
    data: Page | null;
    error: string;
  }>({ key: "", data: null, error: "" });
  const [health, setHealth] = useState<Health | null>(null);
  const [sources, setSources] = useState<string[]>([]);
  const [retry, setRetry] = useState(0);
  const [filterOverride, setFilters] = useState<boolean | null>(null);
  const filters = filterOverride ?? search;
  const [highlights, setHighlights] = useState<
    { slug: string; name: string; article: Article }[]
  >([]);
  const queryString = params.toString();
  const isHome = !category && !search;
  const requestKey = `${queryString}|${category || ""}|${search}|${retry}`;
  const loading = response.key !== requestKey;
  const data = loading ? null : response.data;
  const error = loading ? "" : response.error;
  useEffect(() => {
    api<Health>("/health")
      .then(setHealth)
      .catch(() => {});
    api<string[]>("/sources")
      .then(setSources)
      .catch(() => {});
  }, [retry]);
  useEffect(() => {
    const abort = new AbortController();
    const query = new URLSearchParams(queryString);
    if (category) query.set("category", category);
    query.set("page_size", "9");
    api<Page>(`/${search ? "search" : "articles"}?${query}`, {
      signal: abort.signal,
    })
      .then((data) => {
        if (!abort.signal.aborted)
          setResponse({ key: requestKey, data, error: "" });
      })
      .catch((e) => {
        if (!abort.signal.aborted)
          setResponse({ key: requestKey, data: null, error: e.message });
      });
    return () => abort.abort();
  }, [queryString, category, search, requestKey]);
  useEffect(() => {
    if (!isHome) return;
    const abort = new AbortController();
    Promise.all(
      categories.map(async (c) => {
        const result = await api<Page>(
          `/articles?category=${c.slug}&page_size=6`,
          { signal: abort.signal },
        );
        return { ...c, candidates: result.items };
      }),
    )
      .then((values) => {
        const seen = new Set<string>();
        setHighlights(
          values.flatMap(({ slug, name, candidates }) => {
            const article =
              candidates.find(
                (a) => a.category_slug === slug && !seen.has(a.id),
              ) || candidates.find((a) => !seen.has(a.id));
            if (!article) return [];
            seen.add(article.id);
            return [{ slug, name, article }];
          }),
        );
      })
      .catch(() => {});
    return () => abort.abort();
  }, [isHome, retry]);
  function update(key: string, value: string) {
    const query = new URLSearchParams(queryString);
    if (value) query.set(key, value);
    else query.delete(key);
    if (key !== "page") query.delete("page");
    router.push(`${pathname}?${query}`);
  }
  const label = categories.find((c) => c.slug === category)?.name;
  const hasFilters = [
    "category",
    "region",
    "source",
    "since",
    "until",
    "language",
    "topic",
    "q",
  ].some((key) => params.has(key));
  const homeLead =
    isHome &&
    !hasFilters &&
    Number(params.get("page") || 1) === 1 &&
    params.get("sort") !== "oldest";
  const lead = homeLead && data?.items[0];
  const side = homeLead ? data?.items.slice(1, 3) || [] : [];
  const latest = homeLead ? data?.items.slice(3) || [] : data?.items || [];
  const daily = data?.items.slice(0, 3) || [];
  const date = new Date().toLocaleDateString("en-IN", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  });
  return (
    <>
      <div className="edition">
        <span>
          <Globe2 size={14} aria-hidden />{" "}
          {category
            ? `${label} edition`
            : "A world of stories. One place to begin."}
        </span>
        <time suppressHydrationWarning>{date}</time>
      </div>
      {(data?.demo_mode || health?.demo_mode) && (
        <div className="demo-banner">
          <span className="status-dot" /> <strong>Demo edition</strong>
          <span>
            Fictional sample stories for exploring NewsMind. These are not live
            news reports.
          </span>
        </div>
      )}
      {health &&
        !health.demo_mode &&
        ["failed", "partial", "never_run"].includes(
          health.latest_ingestion_status,
        ) && (
          <div className="notice" role="status">
            {health.latest_ingestion_status === "never_run"
              ? "Live ingestion has not run yet."
              : "The latest provider fetch had errors. Available stories may not include the newest coverage."}
          </div>
        )}
      <div className="page-title">
        <div>
          <span className="eyebrow">
            {search
              ? "DISCOVER MORE"
              : category
                ? "YOUR DAILY PERSPECTIVE"
                : "THE DAILY EDITION"}
          </span>
          <h1>
            {search
              ? params.get("q")
                ? `Results for “${params.get("q")}”`
                : "Find your next perspective."
              : category
                ? label
                : "A clearer view of your world."}
          </h1>
          {category && <p>Latest stories and perspectives in {label}.</p>}
        </div>
        {isHome && (
          <p className="title-note">
            From your neighbourhood to the world.
            <br />
            The stories that bring it into focus.
          </p>
        )}
      </div>
      {search && (
        <form action="/search" className="search-form" role="search">
          <label className="sr-only" htmlFor="results-query">
            Search headlines and descriptions
          </label>
          <input
            name="q"
            id="results-query"
            defaultValue={params.get("q") || ""}
            placeholder="Search headlines and descriptions"
          />
          {Array.from(params.entries())
            .filter(([k]) => k !== "q" && k !== "page")
            .map(([key, value]) => (
              <input key={key} type="hidden" name={key} value={value} />
            ))}
          <button className="primary-button" type="submit">
            Search <ArrowRight size={16} aria-hidden />
          </button>
        </form>
      )}
      {loading ? (
        <div className="skeleton-grid" aria-label="Loading news" role="status">
          <div />
          <div />
          <div />
          <span className="sr-only">Loading stories</span>
        </div>
      ) : error ? (
        <div className="empty-state" role="alert">
          <Newspaper size={32} aria-hidden />
          <h2>We couldn&apos;t load this edition.</h2>
          <p>
            {typeof error === "string" ? error : "Service unavailable"}. Check
            your connection or try again.
          </p>
          <button
            onClick={() => setRetry((v) => v + 1)}
            className="primary-button"
          >
            <RefreshCw size={16} aria-hidden />
            Try again
          </button>
        </div>
      ) : (
        <>
          {lead && (
            <section className="lead-section" aria-label="Lead stories">
              <article className="lead-story">
                <Link href={`/article/${lead.id}`} tabIndex={-1} aria-hidden>
                  <StoryImage article={lead} lead />
                </Link>
                <div className="lead-copy">
                  <div className="eyebrow">
                    <span className="status-dot" /> THE LEAD STORY{" "}
                    <span className="lead-category">{lead.category}</span>
                  </div>
                  <h2>
                    <Link href={`/article/${lead.id}`}>{lead.headline}</Link>
                  </h2>
                  <p>{lead.summary}</p>
                  <div className="lead-bottom">
                    <div className="article-meta">
                      <span>{lead.source}</span>
                      <span>/</span>
                      <Timestamp value={lead.published_at} />
                    </div>
                    <Link className="read-story" href={`/article/${lead.id}`}>
                      Read the story <ArrowUpRight size={18} aria-hidden />
                    </Link>
                  </div>
                </div>
              </article>
              <div className="side-stories">
                <div className="section-label">
                  IN FOCUS <span>02 STORIES</span>
                </div>
                {side.map((a) => (
                  <ArticleCard key={a.id} article={a} compact />
                ))}
              </div>
            </section>
          )}
          <div className="content-columns">
            <section className="latest-section">
              <div className="section-heading">
                <div>
                  <span className="eyebrow">
                    {search
                      ? "SEARCH RESULTS"
                      : "KEEP YOUR FINGER ON THE PULSE"}
                  </span>
                  <h2>
                    {search
                      ? `${data?.total || 0} stories found`
                      : homeLead
                        ? "The latest"
                        : "Latest stories"}
                    <span className="heading-dot">.</span>
                  </h2>
                </div>
                <div className="feed-controls">
                  <label className="sr-only" htmlFor="sort">
                    Sort articles
                  </label>
                  <select
                    id="sort"
                    value={params.get("sort") || "newest"}
                    onChange={(e) => update("sort", e.target.value)}
                  >
                    <option value="newest">Newest first</option>
                    <option value="oldest">Oldest first</option>
                  </select>
                  <button
                    className={`filter-button ${filters ? "selected" : ""}`}
                    onClick={() => setFilters(!filters)}
                    aria-expanded={filters}
                  >
                    <SlidersHorizontal size={16} aria-hidden />
                    Filters
                  </button>
                </div>
              </div>
              {filters && (
                <div className="filters">
                  {!category && (
                    <label>
                      Category
                      <select
                        value={params.get("category") || ""}
                        onChange={(e) => update("category", e.target.value)}
                      >
                        <option value="">All categories</option>
                        {categories.map((c) => (
                          <option value={c.slug} key={c.slug}>
                            {c.name}
                          </option>
                        ))}
                      </select>
                    </label>
                  )}
                  <label>
                    Region
                    <select
                      value={params.get("region") || ""}
                      onChange={(e) => update("region", e.target.value)}
                    >
                      <option value="">All regions</option>
                      {["Regional", "National", "Global"].map((r) => (
                        <option key={r}>{r}</option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Source
                    <select
                      value={params.get("source") || ""}
                      onChange={(e) => update("source", e.target.value)}
                    >
                      <option value="">All sources</option>
                      {sources.map((s) => (
                        <option key={s}>{s}</option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Language
                    <select
                      value={params.get("language") || ""}
                      onChange={(e) => update("language", e.target.value)}
                    >
                      <option value="">All languages</option>
                      <option value="en">English</option>
                      <option value="ta">Tamil</option>
                    </select>
                  </label>
                  <label>
                    Published from
                    <input
                      type="date"
                      value={params.get("since")?.slice(0, 10) || ""}
                      onChange={(e) =>
                        update(
                          "since",
                          e.target.value ? `${e.target.value}T00:00:00Z` : "",
                        )
                      }
                    />
                  </label>
                  <label>
                    Published until
                    <input
                      type="date"
                      value={params.get("until")?.slice(0, 10) || ""}
                      onChange={(e) =>
                        update(
                          "until",
                          e.target.value ? `${e.target.value}T23:59:59Z` : "",
                        )
                      }
                    />
                  </label>
                  {hasFilters && (
                    <button
                      className="clear-button"
                      onClick={() => router.push(pathname)}
                    >
                      <X size={14} aria-hidden />
                      Clear filters
                    </button>
                  )}
                </div>
              )}
              {latest.length ? (
                <div className="article-grid">
                  {latest.map((a) => (
                    <ArticleCard key={a.id} article={a} />
                  ))}
                </div>
              ) : (
                <div className="empty-state">
                  <Newspaper size={30} aria-hidden />
                  <h3>No stories in this view yet.</h3>
                  <p>
                    {hasFilters
                      ? "Try another search or adjust your filters."
                      : data?.demo_mode
                        ? "Run the demo seed command to load example stories."
                        : "Stories will appear after a successful provider fetch."}
                  </p>
                  {hasFilters && (
                    <button
                      className="primary-button"
                      onClick={() => router.push(pathname)}
                    >
                      Reset filters
                    </button>
                  )}
                </div>
              )}
              {data && data.total > data.page_size && (
                <nav className="pagination" aria-label="Article pagination">
                  <button
                    className="text-button"
                    disabled={data.page === 1}
                    onClick={() => update("page", String(data.page - 1))}
                  >
                    <ChevronLeft size={16} aria-hidden />
                    Previous
                  </button>
                  <span>
                    Page {data.page} of {Math.ceil(data.total / data.page_size)}
                  </span>
                  <button
                    className="text-button"
                    disabled={data.page * data.page_size >= data.total}
                    onClick={() => update("page", String(data.page + 1))}
                  >
                    Next
                    <ChevronRight size={16} aria-hidden />
                  </button>
                </nav>
              )}
            </section>
            {isHome && (
              <aside className="briefing">
                <div className="briefing-top">
                  <span className="briefing-icon">
                    <Newspaper size={21} aria-hidden />
                  </span>
                  <span className="eyebrow">A MOMENT OF CLARITY</span>
                </div>
                <h2>
                  Your daily
                  <br />
                  briefing<span>.</span>
                </h2>
                <p className="briefing-intro">
                  Three recent stories.
                  <br />A thoughtful place to start.
                </p>
                <ol>
                  {daily.map((a, i) => (
                    <li key={a.id}>
                      <span className="brief-number">0{i + 1}</span>
                      <div>
                        <span className="eyebrow">{a.category}</span>
                        <Link href={`/article/${a.id}`}>{a.headline}</Link>
                      </div>
                    </li>
                  ))}
                </ol>
                <Link className="briefing-link" href="/search">
                  Explore all stories <MoveRight size={18} aria-hidden />
                </Link>
                <div className="reading-window">
                  <span>THE FOUR-DAY WINDOW</span>
                  <p>
                    Fresh perspectives, without the endless archive. Stories
                    stay available for four days after publication.
                  </p>
                </div>
              </aside>
            )}
          </div>
          {isHome && highlights.length > 0 && (
            <section className="highlights">
              <div className="section-heading">
                <div>
                  <span className="eyebrow">FOLLOW YOUR CURIOSITY</span>
                  <h2>
                    Across the editions<span className="heading-dot">.</span>
                  </h2>
                </div>
                <Link href="/search" className="text-link">
                  All stories
                  <ArrowRight size={17} aria-hidden />
                </Link>
              </div>
              <div className="highlight-grid">
                {highlights.map((h) => (
                  <div className="highlight" key={h.slug}>
                    <Link
                      className="highlight-name"
                      href={`/category/${h.slug}`}
                    >
                      {h.name}
                      <ArrowUpRight size={17} aria-hidden />
                    </Link>
                    <Link href={`/article/${h.article.id}`}>
                      <h3>{h.article.headline}</h3>
                    </Link>
                    <Timestamp value={h.article.published_at} />
                  </div>
                ))}
              </div>
            </section>
          )}
        </>
      )}
    </>
  );
}

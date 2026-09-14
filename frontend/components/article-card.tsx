"use client";
import Link from "next/link";
import { useState } from "react";
import { ArrowUpRight, ImageOff } from "lucide-react";
import type { Article } from "@/lib/types";

export function Timestamp({ value }: { value: string }) {
  return (
    <time dateTime={value} suppressHydrationWarning>
      {new Date(value).toLocaleString("en-IN", {
        month: "short",
        day: "numeric",
        hour: "numeric",
        minute: "2-digit",
      })}
    </time>
  );
}
export function StoryImage({
  article,
  lead = false,
}: {
  article: Article;
  lead?: boolean;
}) {
  const [failed, setFailed] = useState(false);
  return (
    <div className={`story-image ${lead ? "lead-image" : ""}`}>
      {article.image_url && !failed ? (
        // Provider/fixture URLs are dynamic; native images permit graceful failure without a remote hostname allowlist.
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={article.image_url}
          alt=""
          loading={lead ? "eager" : "lazy"}
          onError={() => setFailed(true)}
        />
      ) : (
        <div className="image-fallback">
          <ImageOff size={28} aria-hidden />
          <span>{article.category}</span>
        </div>
      )}
      {article.demo && <span className="image-label">ILLUSTRATIVE IMAGE</span>}
    </div>
  );
}
export function ArticleCard({
  article,
  compact = false,
}: {
  article: Article;
  compact?: boolean;
}) {
  return (
    <article className={`article-card ${compact ? "compact" : ""}`}>
      <Link href={`/article/${article.id}`} tabIndex={-1} aria-hidden>
        <StoryImage article={article} />
      </Link>
      <div className="card-copy">
        <div className={`eyebrow cat-${article.category_slug}`}>
          {article.category}
          {article.demo && <span className="demo-tag">DEMO</span>}
        </div>
        <h3>
          <Link href={`/article/${article.id}`}>{article.headline}</Link>
        </h3>
        {!compact && article.summary && <p>{article.summary}</p>}
        <div className="article-meta">
          <span>{article.source}</span>
          <span className="meta-dot">/</span>
          <Timestamp value={article.published_at} />
          <ArrowUpRight size={15} aria-hidden />
        </div>
      </div>
    </article>
  );
}

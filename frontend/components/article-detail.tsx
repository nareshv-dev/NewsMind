"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, ArrowUpRight, Bookmark, Check, Share2 } from "lucide-react";
import { api } from "@/lib/api";
import type { Article } from "@/lib/types";
import { supabase } from "@/lib/auth";
import { StoryImage, Timestamp } from "./article-card";
export function ArticleDetail({ id }: { id: string }) {
  const [article, setArticle] = useState<Article | null>(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [saved, setSaved] = useState(false);
  useEffect(() => {
    const abort = new AbortController();
    api<Article>(`/articles/${id}`, { signal: abort.signal })
      .then(setArticle)
      .catch((e) => {
        if (!abort.signal.aborted) setError(e.message);
      });
    return () => abort.abort();
  }, [id]);
  useEffect(() => {
    let active = true;
    if (supabase)
      supabase.auth.getSession().then(async ({ data }) => {
        if (data.session) {
          const bookmarks = await api<Article[]>("/bookmarks", {
            headers: { Authorization: `Bearer ${data.session.access_token}` },
          }).catch(() => []);
          if (active) setSaved(bookmarks.some((a) => a.id === id));
        }
      });
    return () => {
      active = false;
    };
  }, [id]);
  async function bookmark() {
    if (!supabase) {
      setMessage(
        "Accounts are not configured. Public reading is always available.",
      );
      return;
    }
    const { data } = await supabase.auth.getSession();
    if (!data.session) {
      setMessage("Sign in to save this story.");
      return;
    }
    try {
      await api(`/bookmarks/${id}`, {
        method: saved ? "DELETE" : "PUT",
        headers: { Authorization: `Bearer ${data.session.access_token}` },
      });
      setSaved(!saved);
      setMessage(
        saved
          ? "Removed from saved articles."
          : "Saved. This article expires four days after publication.",
      );
    } catch (e) {
      setMessage((e as Error).message);
    }
  }
  async function share() {
    try {
      if (navigator.share)
        await navigator.share({ title: article?.headline, url: location.href });
      else {
        await navigator.clipboard.writeText(location.href);
        setMessage("Story link copied.");
      }
    } catch {
      setMessage("Sharing was cancelled or unavailable.");
    }
  }
  if (error)
    return (
      <div className="empty-state">
        <h1>Story unavailable</h1>
        <p>{error}</p>
        <Link className="primary-button" href="/">
          Back to the edition
        </Link>
      </div>
    );
  if (!article)
    return (
      <div className="skeleton-grid" role="status" aria-label="Loading article">
        <div />
        <div />
      </div>
    );
  return (
    <div className="detail">
      <Link className="back-link" href={`/category/${article.category_slug}`}>
        <ArrowLeft size={16} aria-hidden />
        Back to {article.category}
      </Link>
      {article.demo && (
        <div className="demo-banner">
          <strong>Demo story</strong>
          <span>This fictional example is not a live news report.</span>
        </div>
      )}
      <div className="eyebrow">
        {article.category} / {article.geographic_scope}
      </div>
      <h1>{article.headline}</h1>
      <p className="detail-deck">{article.description}</p>
      <div className="detail-byline">
        <div>
          <strong>{article.source}</strong>
          <div>
            Published <Timestamp value={article.published_at} />
          </div>
        </div>
        <div className="detail-actions">
          <button
            className="icon-button"
            onClick={bookmark}
            aria-label={saved ? "Remove saved article" : "Save article"}
            title={saved ? "Remove saved article" : "Save article"}
          >
            {saved ? <Check size={20} /> : <Bookmark size={20} />}
          </button>
          <button
            className="icon-button"
            onClick={share}
            aria-label="Share story"
            title="Share story"
          >
            <Share2 size={20} />
          </button>
        </div>
      </div>
      {message && (
        <p className="notice" role="status">
          {message}
          {message.startsWith("Sign in") && (
            <Link href="/account"> Open account</Link>
          )}
        </p>
      )}
      <StoryImage article={article} lead />
      <div className="reading-body">
        <span className="eyebrow">
          {article.summary_method === "ai"
            ? "AI-GENERATED SUMMARY"
            : "SOURCE EXCERPT"}
        </span>
        <p>
          {article.summary ||
            article.description ||
            "No summary is available for this story."}
        </p>
        {article.summary_method === "ai" && (
          <p className="summary-note">
            Generated from the supplied source content. Read the original
            reporting for its complete context.
          </p>
        )}
        <div className="topic-list">
          {article.topics.map((t) => (
            <Link key={t} href={`/search?topic=${encodeURIComponent(t)}`}>
              {t}
              <ArrowUpRight size={12} aria-hidden />
            </Link>
          ))}
        </div>
        {article.demo ? (
          <div className="notice">
            There is no original report for this fictional demo story.
          </div>
        ) : (
          <a
            className="primary-button"
            href={article.original_url}
            target="_blank"
            rel="noopener noreferrer"
          >
            Read original article
            <ArrowUpRight size={17} aria-hidden />
          </a>
        )}
        <div className="attribution">
          <p>
            Fetched <Timestamp value={article.fetched_at} /> · Available until{" "}
            <Timestamp value={article.expires_at} />
          </p>
          <p>
            Classification: {article.classification_method.replace("_", " ")} ·
            Estimated confidence {Math.round(article.confidence * 100)}% (not a
            calibrated probability).
          </p>
          <p>
            Only the supplied excerpt is available here. Full reporting remains
            with the original publisher.
          </p>
        </div>
      </div>
    </div>
  );
}

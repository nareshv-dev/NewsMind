"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { Bookmark, ArrowRight } from "lucide-react";
import { supabase } from "@/lib/auth";
import { api } from "@/lib/api";
import type { Article } from "@/lib/types";
import { ArticleCard } from "@/components/article-card";
export default function Bookmarks() {
  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  useEffect(() => {
    let active = true;
    async function load() {
      try {
        if (!supabase) {
          setMessage("Accounts are not configured yet.");
          return;
        }
        const { data } = await supabase.auth.getSession();
        if (!data.session) {
          setMessage("Sign in to see your saved articles.");
          return;
        }
        const result = await api<Article[]>("/bookmarks", {
          headers: { Authorization: `Bearer ${data.session.access_token}` },
        });
        if (active) setArticles(result);
      } catch (e) {
        if (active) setMessage((e as Error).message);
      } finally {
        if (active) setLoading(false);
      }
    }
    load();
    return () => {
      active = false;
    };
  }, []);
  return (
    <>
      <div className="page-title">
        <div>
          <span className="eyebrow">YOUR READING LIST</span>
          <h1>Stories to come back to.</h1>
          <p>Saved stories expire four days after publication.</p>
        </div>
      </div>
      {loading ? (
        <p role="status">Loading saved stories...</p>
      ) : message ? (
        <div className="empty-state">
          <Bookmark size={30} aria-hidden />
          <h2>{message}</h2>
          <Link className="primary-button" href="/account">
            Open account
            <ArrowRight size={16} aria-hidden />
          </Link>
        </div>
      ) : articles.length ? (
        <div className="article-grid">
          {articles.map((a) => (
            <ArticleCard key={a.id} article={a} />
          ))}
        </div>
      ) : (
        <div className="empty-state">
          <Bookmark size={30} aria-hidden />
          <h2>Your reading list is clear.</h2>
          <p>Save a story from its article page to return to it later.</p>
          <Link className="primary-button" href="/">
            Explore the edition
            <ArrowRight size={16} aria-hidden />
          </Link>
        </div>
      )}
    </>
  );
}

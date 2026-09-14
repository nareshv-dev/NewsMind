"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, LogOut, Check } from "lucide-react";
import { supabase } from "@/lib/auth";
import { api } from "@/lib/api";
import { categories } from "@/lib/types";
import type { Session } from "@supabase/supabase-js";
type Preferences = {
  categories: string[];
  topics: string[];
  language: string;
  region: string;
  reading_history: boolean;
};
const defaults: Preferences = {
  categories: [],
  topics: [],
  language: "en",
  region: "All",
  reading_history: false,
};
export default function Account() {
  const [session, setSession] = useState<Session | null>(null);
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [prefs, setPrefs] = useState(defaults);
  useEffect(() => {
    if (!supabase) return;
    supabase.auth.getSession().then(({ data }) => setSession(data.session));
    const { data } = supabase.auth.onAuthStateChange((_event, value) =>
      setSession(value),
    );
    return () => data.subscription.unsubscribe();
  }, []);
  useEffect(() => {
    if (session)
      api<Preferences>("/preferences", {
        headers: { Authorization: `Bearer ${session.access_token}` },
      })
        .then(setPrefs)
        .catch((e) => setMessage(e.message));
  }, [session]);
  async function signIn(e: React.FormEvent) {
    e.preventDefault();
    if (!supabase) return;
    setBusy(true);
    const { error } = await supabase.auth.signInWithOtp({
      email,
      options: { emailRedirectTo: `${location.origin}/account` },
    });
    setMessage(
      error ? error.message : "Check your email for your secure sign-in link.",
    );
    setBusy(false);
  }
  async function save(e: React.FormEvent) {
    e.preventDefault();
    if (!session) return;
    setBusy(true);
    try {
      await api("/preferences", {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(prefs),
      });
      setMessage("Your preferences are saved.");
    } catch (e) {
      setMessage((e as Error).message);
    }
    setBusy(false);
  }
  return (
    <div className="account-page">
      <span className="eyebrow">YOUR NEWSMIND</span>
      <h1>
        {session
          ? "Your world. Your perspective."
          : "Make room for your interests."}
      </h1>
      <p>Save stories and keep your reading preferences across devices.</p>
      {!supabase ? (
        <div className="notice">
          <h2>Accounts are not configured yet.</h2>
          <p>
            Public news browsing is available. Secure email sign-in requires a
            configured Supabase project.
          </p>
          <Link className="primary-button" href="/">
            Continue reading
            <ArrowRight size={16} aria-hidden />
          </Link>
        </div>
      ) : !session ? (
        <form onSubmit={signIn} className="account-form">
          <label>
            Email address
            <input
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
            />
          </label>
          <button className="primary-button" disabled={busy}>
            {busy ? "Sending link..." : "Send sign-in link"}
            <ArrowRight size={16} aria-hidden />
          </button>
        </form>
      ) : (
        <>
          <div className="account-session">
            <span>Signed in as {session.user.email}</span>
            <button
              className="text-button"
              onClick={() => supabase?.auth.signOut()}
            >
              <LogOut size={16} aria-hidden />
              Sign out
            </button>
          </div>
          <Link className="text-link" href="/bookmarks">
            Your saved articles
            <ArrowRight size={16} aria-hidden />
          </Link>
          <form onSubmit={save} className="account-form">
            <fieldset>
              <legend>Followed editions</legend>
              <div className="preference-options">
                {categories.map((c) => (
                  <label key={c.slug}>
                    <input
                      type="checkbox"
                      checked={prefs.categories.includes(c.slug)}
                      onChange={(e) =>
                        setPrefs({
                          ...prefs,
                          categories: e.target.checked
                            ? [...prefs.categories, c.slug]
                            : prefs.categories.filter((v) => v !== c.slug),
                        })
                      }
                    />
                    {c.name}
                  </label>
                ))}
              </div>
            </fieldset>
            <fieldset>
              <legend>Followed topics</legend>
              <div className="preference-options">
                {[
                  "AI models",
                  "Developer tools",
                  "Cricket",
                  "Football",
                  "Policy",
                  "Elections",
                  "Climate",
                ].map((topic) => (
                  <label key={topic}>
                    <input
                      type="checkbox"
                      checked={prefs.topics.includes(topic)}
                      onChange={(e) =>
                        setPrefs({
                          ...prefs,
                          topics: e.target.checked
                            ? [...prefs.topics, topic]
                            : prefs.topics.filter((v) => v !== topic),
                        })
                      }
                    />
                    {topic}
                  </label>
                ))}
              </div>
            </fieldset>
            <label>
              Preferred language
              <select
                value={prefs.language}
                onChange={(e) =>
                  setPrefs({ ...prefs, language: e.target.value })
                }
              >
                <option value="en">English</option>
                <option value="ta">Tamil</option>
              </select>
            </label>
            <label>
              Preferred region
              <select
                value={prefs.region}
                onChange={(e) => setPrefs({ ...prefs, region: e.target.value })}
              >
                {["All", "Regional", "National", "Global"].map((r) => (
                  <option key={r}>{r}</option>
                ))}
              </select>
            </label>
            <button className="primary-button" disabled={busy}>
              <Check size={16} aria-hidden />
              {busy ? "Saving..." : "Save preferences"}
            </button>
          </form>
        </>
      )}
      {message && (
        <p className="notice" role="status">
          {message}
        </p>
      )}
      <p className="summary-note">
        Saved news remains available for four days from publication. Expired
        content is removed from saved articles too.
      </p>
    </div>
  );
}

"use client";
export default function ErrorPage({ reset }: { reset: () => void }) {
  return (
    <div className="empty-state">
      <h1>Something interrupted this edition.</h1>
      <button className="primary-button" onClick={reset}>
        Try again
      </button>
    </div>
  );
}

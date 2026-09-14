import Link from "next/link";
export default function NotFound() {
  return (
    <div className="empty-state">
      <h1>This page isn&apos;t in this edition.</h1>
      <Link className="primary-button" href="/">
        Back to NewsMind
      </Link>
    </div>
  );
}

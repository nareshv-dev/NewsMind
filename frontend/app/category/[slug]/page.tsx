import { Suspense } from "react";
import { notFound } from "next/navigation";
import { categories } from "@/lib/types";
import { Feed } from "@/components/feed";
export default async function Category({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  if (!categories.some((c) => c.slug === slug)) notFound();
  return (
    <Suspense fallback={<p>Loading this edition...</p>}>
      <Feed category={slug} />
    </Suspense>
  );
}

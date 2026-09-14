import { Suspense } from "react";
import { Feed } from "@/components/feed";
export default function Search() {
  return (
    <Suspense fallback={<p>Loading search...</p>}>
      <Feed search />
    </Suspense>
  );
}

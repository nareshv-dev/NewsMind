import { Suspense } from "react";
import { Feed } from "@/components/feed";
export default function Home() {
  return (
    <Suspense fallback={<p>Loading the edition...</p>}>
      <Feed />
    </Suspense>
  );
}

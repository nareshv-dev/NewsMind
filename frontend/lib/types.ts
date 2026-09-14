export const categories = [
  { slug: "tamilnadu", name: "Tamilnadu" },
  { slug: "india", name: "India" },
  { slug: "world", name: "World" },
  { slug: "sports", name: "Sports" },
  { slug: "software-ai", name: "Software & AI" },
  { slug: "product-updates", name: "Product Updates" },
  { slug: "politics", name: "Politics" },
];
export type Article = {
  id: string;
  headline: string;
  description: string | null;
  summary: string | null;
  image_url: string | null;
  original_url: string;
  source: string;
  category_slug: string;
  category: string;
  topics: string[];
  geographic_scope: string;
  country: string | null;
  state: string | null;
  language: string;
  confidence: number;
  classification_method: string;
  summary_method: string;
  model_version: string;
  published_at: string;
  fetched_at: string;
  updated_at: string;
  expires_at: string;
  demo: boolean;
};
export type Page = {
  items: Article[];
  total: number;
  page: number;
  page_size: number;
  demo_mode: boolean;
};
export type Health = {
  status: string;
  demo_mode: boolean;
  accounts_configured: boolean;
  provider_configured: boolean;
  latest_ingestion_status: string;
};

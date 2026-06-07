export interface ProductTranslation {
  lang: string;
  name: string;
  description: string;
}

export interface Product {
  id: string;
  slug: string;
  price: string;
  category_id: number;
  size: string;
  brand: string;
  condition: 'new' | 'like_new' | 'good' | 'fair';
  condition_rating: number | null;
  condition_details: ConditionDetails | null;
  target_gender: string | null;
  material: string | null;
  colors: string[] | null;
  trend: string | null;
  pattern: string | null;
  season: string | null;
  cut: string[] | null;
  usage: string | null;
  source_dataset: string | null;
  image_urls: string[];
  stock: number;
  translations: ProductTranslation[];
  created_at: string;
}

export interface ConditionDetails {
  pilling?: number;
  damage?: string;
  stains?: string;
  holes?: string;
  smell?: string;
}

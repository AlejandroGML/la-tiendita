export interface ProductTranslation {
  language_code: string;
  name: string;
  description: string;
}

export interface ProductVariant {
  id: string;
  product_id: string;
  size: string | null;
  color: string | null;
  color_hex: string | null;
  stock: number;
  sku: string;
}

export interface ProductColorSwatch {
  color: string;
  hex: string;
}

export interface Product {
  id: string;
  slug: string;
  /** Pre-resolved translation name (summary DTO) or fallback */
  name?: string;
  price: string;
  category_id: number;
  brand: string;
  condition: 'new' | 'like_new' | 'good' | 'fair';
  condition_rating: number | null;
  condition_details: ConditionDetails | null;
  target_gender: string | null;
  material: string | null;
  /** Legacy: raw color strings. Summary DTO: array of {color, hex} objects. */
  colors: (string | ProductColorSwatch)[] | null;
  trend: string | null;
  pattern: string | null;
  season: string | null;
  cut: string[] | null;
  usage: string | null;
  source_dataset: string | null;
  image_urls: string[];
  /** Summary DTO fields — absent in detail response */
  stock_total?: number;
  has_promotion?: boolean;
  has_variants?: boolean;
  is_out_of_stock?: boolean;
  sizes?: string[];
  avg_rating?: number;
  total_reviews?: number;
  /** Legacy arrays — absent in summary response */
  variants?: ProductVariant[];
  translations?: ProductTranslation[];
  created_at: string;
  sale_price?: string;
  discount_label?: string;
  promotion?: {
    code: string;
    discount_percent: number;
    end_date?: string;
  };
}

export interface ConditionDetails {
  pilling?: number;
  damage?: string;
  stains?: string;
  holes?: string;
  smell?: string;
}

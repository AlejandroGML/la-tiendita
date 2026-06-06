export interface ProductTranslation {
  lang: string;
  name: string;
  description: string;
}

export interface Product {
  id: string;
  slug: string;
  price: number;
  category_id: number;
  size: string;
  brand: string;
  condition: 'new' | 'like_new' | 'good' | 'fair';
  image_urls: string[];
  stock: number;
  translations: ProductTranslation[];
  created_at: string;
}

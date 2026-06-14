export interface CategoryTranslation {
  lang: string;
  name: string;
  description?: string;
}

export interface Category {
  id: number;
  slug: string;
  name?: string;
  image_url: string | null;
  translations: CategoryTranslation[];
}

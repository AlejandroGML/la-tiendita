export interface PromotionTranslation {
  lang: string;
  title: string;
  description: string | null;
}

export interface Promotion {
  id: string;
  code: string;
  discount_percent: number;
  product_id: string | null;
  max_uses: number | null;
  current_uses: number;
  is_active: boolean;
  start_date: string | null;
  end_date: string | null;
  translations: PromotionTranslation[];
  created_at: string;
  updated_at: string;
}

export interface CreatePromotionPayload {
  code: string;
  discount_percent: number;
  product_id?: string | null;
  max_uses?: number | null;
  start_date?: string | null;
  end_date?: string | null;
  is_active?: boolean;
  translations: PromotionTranslation[];
}

export interface UpdatePromotionPayload extends Partial<CreatePromotionPayload> {}

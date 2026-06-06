export interface Review {
  id: string;
  user_id: string;
  user_name: string;
  product_id: string;
  rating: number;
  comment: string | null;
  created_at: string;
}

export interface CreateReviewPayload {
  rating: number;
  comment?: string;
}

export interface ReviewListResponse {
  reviews: Review[];
  avg_rating: number;
  total_reviews: number;
  page: number;
  per_page: number;
}

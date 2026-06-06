export interface WishlistItem {
  product_id: string;
  name: string;
  price: string;
  image_url: string | null;
  slug: string;
  added_at: string;
}

export interface WishlistResponse {
  items: WishlistItem[];
}

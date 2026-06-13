export interface CartItem {
  id: string;
  product_id: string;
  product_name: string;
  image_url?: string;
  quantity: number;
  unit_price: string;
  subtotal: string;
  added_at: string;
  variant_id?: string;
  size?: string;
  color?: string;
  original_unit_price?: string;
  discount_label?: string;
  savings?: string;
}

export interface CartResponse {
  items: CartItem[];
  subtotal: string;
  original_subtotal?: string;
  total_savings?: string;
}

export interface AddToCartRequest {
  product_id: string;
  quantity: number;
  variant_id?: string;
}

export interface UpdateCartItemRequest {
  quantity: number;
}

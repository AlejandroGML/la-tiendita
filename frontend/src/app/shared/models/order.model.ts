export type OrderStatus =
  | 'pending'
  | 'confirmed'
  | 'shipped'
  | 'delivered'
  | 'cancelled';

export type PaymentStatus =
  | 'pending'
  | 'paid'
  | 'failed'
  | 'refunded';

export interface ShippingAddress {
  name: string;
  address: string;
  city: string;
  phone: string;
}

export interface ShippingMethod {
  id: string;
  name: string;
  price: number;
  estimated_days: string;
}

export interface OrderItem {
  id: string;
  product_id: string;
  product_snapshot: {
    name: string;
    price: string;
    size?: string;
    product_id: string;
  };
  quantity: number;
  price: string;
}

export interface Order {
  id: string;
  status: OrderStatus;
  total: string;
  shipping_address: ShippingAddress;
  shipping_method?: string;
  shipping_cost?: string;
  items: OrderItem[];
  payment_status: string;
  created_at: string;
  updated_at: string;
}

export interface CheckoutRequest {
  shipping_address: ShippingAddress;
  shipping_method?: string;
  guest_email?: string;
}

export type PaymentMethod = 'card' | 'klarna' | 'swish';

export interface CheckoutResponse {
  order_id: string;
  payment_method: PaymentMethod;
  redirect_url?: string | null;
  qr_code?: string | null;
  payment_reference?: string | null;
}

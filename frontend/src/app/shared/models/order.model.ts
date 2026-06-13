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
  items: OrderItem[];
  payment_status: string;
  created_at: string;
  updated_at: string;
}

export interface CheckoutRequest {
  shipping_address: ShippingAddress;
}

export interface CheckoutResponse {
  checkout_url: string;
  order_id: string;
}

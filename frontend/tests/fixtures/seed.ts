import type { APIRequestContext } from '@playwright/test';

const API_URL = 'http://localhost:8000';

/**
 * Create a category via the admin API.
 * Requires a valid admin bearer token.
 */
export async function createCategory(
  request: APIRequestContext,
  adminToken: string,
  slug: string,
  nameEs: string,
  nameEn: string,
): Promise<number> {
  const res = await request.post(`${API_URL}/api/admin/categories`, {
    headers: { Authorization: `Bearer ${adminToken}` },
    data: {
      slug,
      translations: [
        { lang: 'es', name: nameEs },
        { lang: 'en', name: nameEn },
      ],
    },
  });
  if (!res.ok()) {
    throw new Error(`Create category failed (${slug}): ${res.status()} ${await res.text()}`);
  }
  const body = await res.json();
  return (body as Record<string, unknown>).id as number;
}

/**
 * Create a product via the admin API.
 * Requires a valid admin bearer token.
 * Returns the product slug so tests can navigate to it.
 */
export async function createProduct(
  request: APIRequestContext,
  adminToken: string,
  categoryId: number,
  slug: string,
  price: number,
  nameEs: string,
): Promise<string> {
  const res = await request.post(`${API_URL}/api/admin/products`, {
    headers: { Authorization: `Bearer ${adminToken}` },
    data: {
      slug,
      price,
      category_id: categoryId,
      stock: 10,
      condition: 'new',
      brand: 'TestBrand',
      size: 'M',
      translations: [
        { lang: 'es', name: nameEs, description: `${nameEs} — descripción de prueba` },
        { lang: 'en', name: nameEs, description: `${nameEs} — test description` },
      ],
    },
  });
  if (!res.ok()) {
    throw new Error(`Create product failed (${slug}): ${res.status()} ${await res.text()}`);
  }
  return slug;
}

/**
 * Login as admin and return the token.
 * Uses admin credentials from environment or defaults.
 */
export async function loginAsAdmin(request: APIRequestContext): Promise<string> {
  const email = process.env.TEST_ADMIN_EMAIL || 'admin@example.com';
  const password = process.env.TEST_ADMIN_PASSWORD || 'admin123456';

  const res = await request.post(`${API_URL}/auth/login`, {
    data: { email, password },
  });
  if (!res.ok()) {
    throw new Error(`Admin login failed: ${res.status()} ${await res.text()}`);
  }
  const body = await res.json();
  return (body as { access_token: string }).access_token;
}

/**
 * Seed multiple categories in batch.
 * Returns category IDs.
 */
export async function seedCategories(
  request: APIRequestContext,
  adminToken: string,
  categories: Array<{ slug: string; nameEs: string; nameEn: string }>,
): Promise<number[]> {
  const ids: number[] = [];
  for (const cat of categories) {
    const id = await createCategory(request, adminToken, cat.slug, cat.nameEs, cat.nameEn);
    ids.push(id);
  }
  return ids;
}

/**
 * Seed multiple products in batch.
 * Returns product slugs.
 */
export async function seedProducts(
  request: APIRequestContext,
  adminToken: string,
  categoryId: number,
  products: Array<{ slug: string; price: number; nameEs: string }>,
): Promise<string[]> {
  const slugs: string[] = [];
  for (const p of products) {
    const slug = await createProduct(request, adminToken, categoryId, p.slug, p.price, p.nameEs);
    slugs.push(slug);
  }
  return slugs;
}

/**
 * Create a review for a product via the public API.
 * Requires a valid user bearer token.
 */
export async function createReview(
  request: APIRequestContext,
  userToken: string,
  productId: number,
  rating: number,
  comment: string,
): Promise<void> {
  const res = await request.post(`${API_URL}/api/products/${productId}/reviews`, {
    headers: { Authorization: `Bearer ${userToken}` },
    data: { rating, comment },
  });
  if (!res.ok()) {
    throw new Error(`Create review failed (product ${productId}): ${res.status()} ${await res.text()}`);
  }
}

/**
 * Create an order via the checkout API.
 * Requires a valid user bearer token.
 * Returns the order ID.
 */
export async function createOrder(
  request: APIRequestContext,
  userToken: string,
  productSlug: string,
  quantity: number,
): Promise<number> {
  const res = await request.post(`${API_URL}/api/checkout`, {
    headers: { Authorization: `Bearer ${userToken}` },
    data: {
      items: [{ slug: productSlug, quantity }],
      shipping: {
        name: 'Test User',
        address: 'Testgatan 1',
        city: 'Stockholm',
        phone: '0701234567',
      },
    },
  });
  if (!res.ok()) {
    throw new Error(`Create order failed: ${res.status()} ${await res.text()}`);
  }
  const body = await res.json();
  return (body as { order_id: number }).order_id;
}

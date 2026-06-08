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

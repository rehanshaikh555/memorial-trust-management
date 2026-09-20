export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  "http://localhost:8000/api/v1";

const TOKEN_KEY = "memorial_access_token";

export function getAccessToken() {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setAccessToken(token: string) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearAccessToken() {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(TOKEN_KEY);
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = getAccessToken();

  const response = await fetch(
    `${API_BASE_URL}${path}`,
    {
      ...options,
      headers: {
        ...(options.body instanceof FormData
          ? {}
          : { "Content-Type": "application/json" }),
        ...(token
          ? { Authorization: `Bearer ${token}` }
          : {}),
        ...(options.headers ?? {}),
      },
      cache: "no-store",
    },
  );

  if (response.status === 401) {
    clearAccessToken();

    if (typeof window !== "undefined") {
      window.dispatchEvent(
        new CustomEvent("memorial:unauthorized"),
      );
    }
  }

  if (!response.ok) {
    const body = await response.text();

    let message = "Request failed.";

    try {
      const parsed = JSON.parse(body);

      message =
        parsed?.error?.message ??
        parsed?.detail ??
        message;
    } catch {
      if (body) {
        message = body;
      }
    }

    throw new Error(message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export async function login(
  email: string,
  password: string,
) {
  const form = new URLSearchParams();

  form.set("username", email);
  form.set("password", password);

  const response = await fetch(
    `${API_BASE_URL}/auth/login`,
    {
      method: "POST",
      headers: {
        "Content-Type":
          "application/x-www-form-urlencoded",
      },
      body: form.toString(),
      cache: "no-store",
    },
  );

  if (!response.ok) {
    const body = await response.text();

    try {
      const parsed = JSON.parse(body);
      throw new Error(
        parsed?.detail ??
          parsed?.error?.message ??
          "Invalid credentials.",
      );
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }

      throw new Error("Unable to sign in.");
    }
  }

  return response.json();
}

export async function logout() {
  try {
    await apiFetch("/auth/logout", {
      method: "POST",
    });
  } finally {
    clearAccessToken();
  }
}

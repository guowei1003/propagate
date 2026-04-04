export class ApiError extends Error {
  status: number;
  code?: string;
  type?: string;

  constructor(status: number, message: string, options?: { code?: string; type?: string }) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = options?.code;
    this.type = options?.type;
  }
}

type ApiErrorBody = {
  detail?: string;
  message?: string;
  type?: string;
  code?: string;
  status?: number;
};

async function requestJson<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init);
  if (!response.ok) {
    let message = `请求失败（${response.status}）`;
    let code: string | undefined;
    let type: string | undefined;
    let status = response.status;

    try {
      const contentType = response.headers.get("content-type") || "";
      if (contentType.includes("application/json")) {
        const data = (await response.json()) as ApiErrorBody;
        message = data.message || data.detail || message;
        code = data.code;
        type = data.type;
        status = typeof data.status === "number" ? data.status : status;
      } else {
        const text = (await response.text()).trim();
        if (text) {
          message = text;
        }
      }
    } catch {
      // Ignore parse errors and keep the fallback message.
    }

    throw new ApiError(status, message, { code, type });
  }

  return response.json() as Promise<T>;
}

export function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "操作失败，请稍后重试。";
}

export async function getJson<T>(url: string): Promise<T> {
  return requestJson<T>(url);
}

export async function postJson<T>(url: string, payload: unknown): Promise<T> {
  return requestJson<T>(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
}

export async function putJson<T>(url: string, payload: unknown): Promise<T> {
  return requestJson<T>(url, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
}

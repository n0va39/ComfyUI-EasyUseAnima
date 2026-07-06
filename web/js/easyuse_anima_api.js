const DEFAULT_REQUEST_FAILED = "Request failed";

export function easyuseAnimaEncodeRFC3986URIComponent(value) {
  return encodeURIComponent(value).replace(/[!'()*]/g, (char) => `%${char.charCodeAt(0).toString(16).toUpperCase()}`);
}

export function easyuseAnimaJsonHeaders(headers = {}) {
  return { "Content-Type": "application/json", ...headers };
}

export async function easyuseAnimaReadJsonResponse(response, fallback = null) {
  try {
    return await response.json();
  } catch {
    return fallback;
  }
}

export async function easyuseAnimaReadTextResponse(response, fallback = "") {
  try {
    return await response.text();
  } catch {
    return fallback;
  }
}

export async function easyuseAnimaFetchJson(url, options = {}) {
  const {
    fetcher = fetch,
    fallbackJson = null,
    errorMessage = DEFAULT_REQUEST_FAILED,
    ...fetchOptions
  } = options;
  const response = await fetcher(url, fetchOptions);
  const data = await easyuseAnimaReadJsonResponse(response, fallbackJson);
  if (!response.ok) {
    throw new Error(data?.message || response.statusText || (response.status ? `HTTP ${response.status}` : errorMessage) || DEFAULT_REQUEST_FAILED);
  }
  return data;
}

export async function easyuseAnimaFetchText(url, options = {}) {
  const {
    fetcher = fetch,
    fallbackText = "",
    errorMessage = DEFAULT_REQUEST_FAILED,
    ...fetchOptions
  } = options;
  const response = await fetcher(url, fetchOptions);
  const text = await easyuseAnimaReadTextResponse(response, fallbackText);
  if (!response.ok) {
    throw new Error(response.statusText || (response.status ? `HTTP ${response.status}` : errorMessage) || DEFAULT_REQUEST_FAILED);
  }
  return text;
}

export async function easyuseAnimaFetchOptionalJson(url, options = {}) {
  const {
    fetcher = fetch,
    fallback = null,
    ...fetchOptions
  } = options;
  const response = await fetcher(url, fetchOptions);
  if (!response.ok) {
    return fallback;
  }
  return easyuseAnimaReadJsonResponse(response, fallback);
}

export async function easyuseAnimaGetSettings(options = {}) {
  return easyuseAnimaFetchOptionalJson("/easyuse_anima/settings", {
    fallback: {},
    ...options,
  });
}

export async function easyuseAnimaFetchComfyJson(apiClient, url, options = {}) {
  const fetcher = apiClient?.fetchApi
    ? (requestUrl, requestOptions) => apiClient.fetchApi(requestUrl, requestOptions)
    : fetch;
  return easyuseAnimaFetchJson(url, { fetcher, ...options });
}

export async function easyuseAnimaPostJson(url, body, options = {}) {
  const { headers, ...fetchOptions } = options;
  return easyuseAnimaFetchJson(url, {
    method: "POST",
    headers: easyuseAnimaJsonHeaders(headers),
    body: JSON.stringify(body ?? {}),
    ...fetchOptions,
  });
}

export async function easyuseAnimaClassifyPrompt(text, options = {}) {
  const { limit: requestedLimit, ...requestOptions } = options;
  const limit = Number.isFinite(Number(requestedLimit)) ? Number(requestedLimit) : 240;
  const data = await easyuseAnimaPostJson("/easyuse_anima/classify_prompt", { text, limit }, requestOptions);
  return Array.isArray(data?.tokens) ? data.tokens : [];
}

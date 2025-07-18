const tokenStorageKey = "token";

function getBasePath() {
  // This relies on the fact that flanotes always has a correctly formatted relative path set in <base> tag
  const baseElement = document.querySelector('base');
  return baseElement ? baseElement.getAttribute('href') : '/';
}

function getCookieString(token) {
  const basePath = getBasePath();
  return `${tokenStorageKey}=${token}; Path=${basePath}; SameSite=Strict`;
}

export function storeToken(token, persist = false) {
  document.cookie = getCookieString(token);
  sessionStorage.setItem(tokenStorageKey, token);
  if (persist === true) {
    localStorage.setItem(tokenStorageKey, token);
  }
}

export function getStoredToken() {
  // First check sessionStorage, then localStorage
  const sessionToken = sessionStorage.getItem(tokenStorageKey);
  if (sessionToken) {
    return sessionToken;
  }
  return localStorage.getItem(tokenStorageKey);
}

export function loadStoredToken() {
  const token = localStorage.getItem(tokenStorageKey);
  if (token != null) {
    // Load from localStorage to sessionStorage for current session
    sessionStorage.setItem(tokenStorageKey, token);
  }
}

export function clearStoredToken() {
  sessionStorage.removeItem(tokenStorageKey);
  localStorage.removeItem(tokenStorageKey);
  document.cookie =
    getCookieString() + "; expires=Thu, 01 Jan 1970 00:00:00 GMT";
}

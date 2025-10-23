// Cliente global de Supabase
// Requiere que la página haya definido window.SUPABASE_URL y window.SUPABASE_ANON_KEY
// y haya cargado el script UMD de supabase-js:
// <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/supabase.min.js"></script>

window.sb = window.supabase.createClient(window.SUPABASE_URL, window.SUPABASE_ANON_KEY);

// ---- Helpers de sesión ----
async function signIn(email, password) {
  const { data, error } = await sb.auth.signInWithPassword({ email, password });
  if (error) throw error;
  localStorage.setItem("sb_access_token", data.session?.access_token || "");
  return data;
}

async function signUp(email, password, fullName) {
  const { data, error } = await sb.auth.signUp({
    email, password,
    options: { data: { full_name: fullName || "" } }
  });
  if (error) throw error;
  return data;
}

async function signOut() {
  await sb.auth.signOut();
  localStorage.removeItem("sb_access_token");
  location.href = "./";
}

function getToken() {
  return localStorage.getItem("sb_access_token") || "";
}

// ---- Fetch con Bearer JWT ----
async function fetchAuth(url, options = {}) {
  const token = getToken();
  const headers = Object.assign({}, options.headers || {}, {
    "Content-Type": "application/json",
    ...(token ? { "Authorization": `Bearer ${token}` } : {})
  });
  const res = await fetch(url, { ...options, headers });
  if (!res.ok) {
    const t = await res.text().catch(() => "");
    throw new Error(`HTTP ${res.status}: ${t}`);
  }
  return res.json();
}

async function fetchAuthFormData(url, formData) {
  const token = getToken();
  const headers = token ? { "Authorization": `Bearer ${token}` } : {};
  const res = await fetch(url, { method: "POST", headers, body: formData });
  if (!res.ok) {
    const t = await res.text().catch(() => "");
    throw new Error(`HTTP ${res.status}: ${t}`);
  }
  return res.json();
}

// ---- Protección de /admin ----
async function ensureAdmin() {
  const token = getToken();
  if (!token) { location.href = "./login.html?next=admin.html"; return false; }
  try {
    await fetchAuth(`${window.API_BASE_URL}/api/admin/me`);
    return true;
  } catch (e) {
    alert("No tenés permisos de administrador.");
    location.href = "./login.html";
    return false;
  }
}

// Exponer helpers si se usan en inline scripts
window.signIn = signIn;
window.signUp = signUp;
window.signOut = signOut;
window.fetchAuth = fetchAuth;
window.fetchAuthFormData = fetchAuthFormData;
window.ensureAdmin = ensureAdmin;

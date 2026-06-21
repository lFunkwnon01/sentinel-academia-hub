/**
 * Tenant detection from email domain.
 *
 * Production: replace with Cognito user pool + JWT claims.
 * Demo: map university email domains to tenantIds client-side.
 */

const DOMAIN_TO_TENANT: Record<string, { tenantId: string; name: string }> = {
  "utec.edu.pe": { tenantId: "demo-utec", name: "UTEC (Universidad de Ingenier\u00eda y Tecnolog\u00eda)" },
  "utp.edu.pe": { tenantId: "demo-utp", name: "UTP (Universidad Tecnol\u00f3gica del Per\u00fa)" },
  "up.edu.pe": { tenantId: "demo-up", name: "UP (Universidad del Pac\u00edfico)" },
  "pucp.edu.pe": { tenantId: "demo-pucp", name: "PUCP (Pontificia Universidad Cat\u00f3lica del Per\u00fa)" },
  "ulima.edu.pe": { tenantId: "demo-ulima", name: "Universidad de Lima" },
  "uni.edu.pe": { tenantId: "demo-uni", name: "UNI (Universidad Nacional de Ingenier\u00eda)" },
  "unmsm.edu.pe": { tenantId: "demo-unmsm", name: "UNMSM (Universidad Nacional Mayor de San Marcos)" },
};

const DEFAULT_TENANT = "demo-utec";

export interface TenantInfo {
  tenantId: string;
  name: string;
  source: "domain" | "session" | "default";
  email?: string;
}

export function detectTenantFromEmail(email: string | undefined | null): TenantInfo | null {
  if (!email) return null;
  const domain = email.split("@")[1]?.toLowerCase().trim();
  if (!domain) return null;
  const match = DOMAIN_TO_TENANT[domain];
  if (match) {
    return { ...match, source: "domain", email };
  }
  return null;
}

export function listAvailableTenants(): Array<{ tenantId: string; name: string; domain: string }> {
  return Object.entries(DOMAIN_TO_TENANT).map(([domain, info]) => ({
    domain,
    tenantId: info.tenantId,
    name: info.name,
  }));
}

const SESSION_KEY = "sentinel.tenant";

export function setSessionTenant(tenant: TenantInfo): void {
  sessionStorage.setItem(SESSION_KEY, JSON.stringify(tenant));
}

export function getSessionTenant(): TenantInfo {
  const stored = sessionStorage.getItem(SESSION_KEY);
  if (stored) {
    try {
      return JSON.parse(stored) as TenantInfo;
    } catch {
      // fall through
    }
  }
  return { tenantId: DEFAULT_TENANT, name: "UTEC (Universidad de Ingeniería y Tecnología)", source: "default" };
}

export function clearSessionTenant(): void {
  sessionStorage.removeItem(SESSION_KEY);
}

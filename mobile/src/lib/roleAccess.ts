import type { AppUser } from "./api";

export function getUserRole(user?: AppUser | null): string {
  return String(user?.role || "").trim();
}

export function isSuperadmin(user?: AppUser | null): boolean {
  const role = getUserRole(user);
  return role === "superadmin" || Boolean(user?.is_admin);
}

export function isParent(user?: AppUser | null): boolean {
  const role = getUserRole(user);
  return role === "parent_admin" || role === "guest_parent";
}

export function isChild(user?: AppUser | null): boolean {
  const role = getUserRole(user);
  return role === "child" || role === "guest_child";
}

export function canSeeAmigo(user?: AppUser | null): boolean {
  return (
    isSuperadmin(user) ||
    isParent(user) ||
    isChild(user) ||
    Boolean(user?.permissions?.can_access_amigo)
  );
}

export function canSeeBiblioteca(user?: AppUser | null): boolean {
  return (
    isSuperadmin(user) ||
    isParent(user) ||
    Boolean(user?.permissions?.can_access_biblioteca)
  );
}

export function canSeePadres(user?: AppUser | null): boolean {
  return (
    isSuperadmin(user) ||
    isParent(user) ||
    Boolean(user?.permissions?.can_access_modo_padres)
  );
}

export function canSeeAdmin(user?: AppUser | null): boolean {
  return isSuperadmin(user) || Boolean(user?.permissions?.can_access_admin);
}

export function canChatWithAmigo(user?: AppUser | null): boolean {
  return isSuperadmin(user) || isChild(user);
}

export function canConfigureAmigo(user?: AppUser | null): boolean {
  return (
    isSuperadmin(user) ||
    isParent(user) ||
    Boolean(user?.permissions?.can_customize_child_friend)
  );
}

export function isBibliotecaReadOnly(user?: AppUser | null): boolean {
  return isParent(user);
}

export function roleLabel(user?: AppUser | null): string {
  const role = getUserRole(user);

  const labels: Record<string, string> = {
    superadmin: "Superadmin",
    parent_admin: "Padre / Tutor",
    child: "Niño",
    guest_child: "Guest niño",
    guest_parent: "Guest padre",
  };

  return labels[role] || "Usuario";
}

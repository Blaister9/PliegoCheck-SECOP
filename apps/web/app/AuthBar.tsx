"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import type { AuthCurrentUser } from "@pliegocheck/schemas";
import { getCurrentUser, getUnreadAlertCount, logout } from "../lib/api";

export function AuthBar() {
  const router = useRouter();
  const [current, setCurrent] = useState<AuthCurrentUser | null>(null);
  const [unread, setUnread] = useState(0);

  useEffect(() => {
    getCurrentUser()
      .then(setCurrent)
      .catch(() => setCurrent(null));
    getUnreadAlertCount()
      .then((value) => setUnread(value.count))
      .catch(() => setUnread(0));
  }, []);

  async function doLogout() {
    await logout().catch(() => undefined);
    router.push("/login");
  }

  if (!current) {
    return (
      <div className="topbar">
        <Link href="/login">Iniciar sesion</Link>
      </div>
    );
  }

  const isAdmin = current.roles.includes("ADMIN");
  return (
    <div className="topbar">
      <span>{current.user.email}</span>
      {isAdmin ? <Link href="/admin">Admin</Link> : null}
      <Link href="/opportunities">Oportunidades</Link>
      <Link href="/monitors">Monitores</Link>
      <Link href="/alerts">Alertas{unread ? ` (${unread})` : ""}</Link>
      <Link href="/settings/notifications">Notificaciones</Link>
      <Link href="/notification-deliveries">Entregas</Link>
      {isAdmin ? <Link href="/operations/notifications">Operación</Link> : null}
      <button type="button" onClick={doLogout}>
        Cerrar sesion
      </button>
    </div>
  );
}

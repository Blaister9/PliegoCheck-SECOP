"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import type { AuthCurrentUser } from "@pliegocheck/schemas";
import { getCurrentUser, logout } from "../lib/api";

export function AuthBar() {
  const router = useRouter();
  const [current, setCurrent] = useState<AuthCurrentUser | null>(null);

  useEffect(() => {
    getCurrentUser()
      .then(setCurrent)
      .catch(() => setCurrent(null));
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
      <button type="button" onClick={doLogout}>
        Cerrar sesion
      </button>
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import type { AuthUserList } from "@pliegocheck/schemas";
import { listAdminUsers } from "../../../lib/api";

export default function AdminUsersPage() {
  const [users, setUsers] = useState<AuthUserList | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    listAdminUsers()
      .then(setUsers)
      .catch((err) => setError(String(err)));
  }, []);
  return (
    <main className="container">
      <h1>Usuarios</h1>
      {error ? <p role="alert">{error}</p> : null}
      <table>
        <thead>
          <tr>
            <th>Email</th>
            <th>Nombre</th>
            <th>Estado</th>
            <th>Roles</th>
          </tr>
        </thead>
        <tbody>
          {(users?.items ?? []).map((user) => (
            <tr key={user.id}>
              <td>{user.email}</td>
              <td>{user.display_name}</td>
              <td>{user.status}</td>
              <td>{(user.roles ?? []).join(", ")}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}

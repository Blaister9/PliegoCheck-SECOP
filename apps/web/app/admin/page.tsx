import Link from "next/link";

export default function AdminPage() {
  return (
    <main className="container">
      <h1>Administracion</h1>
      <nav className="actions" aria-label="Administracion">
        <Link className="button" href="/admin/users">
          Usuarios
        </Link>
        <Link className="button secondary" href="/admin/audit">
          Auditoria
        </Link>
        <Link className="button secondary" href="/admin/system">
          Sistema
        </Link>
      </nav>
    </main>
  );
}

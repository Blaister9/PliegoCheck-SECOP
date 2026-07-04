"use client";

import { FormEvent, useState } from "react";
import { Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { login } from "../../lib/api";

export default function LoginPage() {
  return (
    <Suspense fallback={<LoginShell />}>
      <LoginForm />
    </Suspense>
  );
}

function LoginShell() {
  return (
    <main className="container narrow">
      <h1>Iniciar sesion</h1>
      <p className="notice">Acceso operativo protegido para piloto controlado.</p>
    </main>
  );
}

function LoginForm() {
  const router = useRouter();
  const search = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await login({ email, password });
      router.push(search.get("next") || "/processes");
    } catch (err) {
      setError(err instanceof Error ? err.message : "No fue posible iniciar sesion.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="container narrow">
      <h1>Iniciar sesion</h1>
      <p className="notice">Acceso operativo protegido para piloto controlado.</p>
      <form className="form" onSubmit={submit}>
        {error ? <p role="alert">{error}</p> : null}
        <label>
          Email
          <input
            type="email"
            autoComplete="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
        </label>
        <label>
          Password
          <input
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
        </label>
        <button className="button" type="submit" disabled={submitting}>
          {submitting ? "Validando..." : "Iniciar sesion"}
        </button>
      </form>
    </main>
  );
}

"use client";

import { useEffect, useState } from "react";
import type { SystemConfigSummary } from "@pliegocheck/schemas";
import { getSystemConfig } from "../../../lib/api";

export default function AdminSystemPage() {
  const [config, setConfig] = useState<SystemConfigSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    getSystemConfig()
      .then(setConfig)
      .catch((err) => setError(String(err)));
  }, []);
  return (
    <main className="container">
      <h1>Configuracion del sistema</h1>
      {error ? <p role="alert">{error}</p> : null}
      {config ? <pre>{JSON.stringify(config, null, 2)}</pre> : <p>Cargando...</p>}
    </main>
  );
}

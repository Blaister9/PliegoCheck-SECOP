"use client";

import { useEffect, useState } from "react";
import type { OperationalAuditEventList } from "@pliegocheck/schemas";
import { listAuditEvents } from "../../../lib/api";

export default function AdminAuditPage() {
  const [events, setEvents] = useState<OperationalAuditEventList | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    listAuditEvents()
      .then(setEvents)
      .catch((err) => setError(String(err)));
  }, []);
  return (
    <main className="container">
      <h1>Auditoria operacional</h1>
      {error ? <p role="alert">{error}</p> : null}
      <ul>
        {(events?.items ?? []).map((event) => (
          <li key={event.id}>
            <code>{event.event_type}</code> {event.action} {event.status}
          </li>
        ))}
      </ul>
    </main>
  );
}

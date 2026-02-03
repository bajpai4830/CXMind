export type AnalyticsSummary = {
  total_interactions: number;
  avg_sentiment_compound: number;
  by_channel: Array<{
    channel: string;
    count: number;
    avg_sentiment_compound: number;
  }>;
  by_label: Array<{ label: string; count: number }>;
};

export type Interaction = {
  id: number;
  customer_id: string | null;
  channel: string;
  text: string;
  sentiment_compound: number;
  sentiment_label: string;
  created_at: string;
};

async function jsonFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...init
  });
  if (!r.ok) {
    const msg = await r.text().catch(() => "");
    throw new Error(`${r.status} ${r.statusText}${msg ? `: ${msg}` : ""}`);
  }
  return (await r.json()) as T;
}

export function getSummary(): Promise<AnalyticsSummary> {
  return jsonFetch<AnalyticsSummary>("/api/v1/analytics/summary");
}

export function listInteractions(limit = 25): Promise<Interaction[]> {
  return jsonFetch<Interaction[]>(`/api/v1/interactions?limit=${encodeURIComponent(limit)}`);
}

export function createInteraction(payload: {
  customer_id?: string;
  channel: string;
  text: string;
}): Promise<Interaction> {
  return jsonFetch<Interaction>("/api/v1/interactions", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}


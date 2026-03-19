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
  topic: string | null;
  created_at: string;
};

export type TokenResponse = {
  access_token: string;
  token_type: string;
  expires_in: number;
};

export type UserOut = {
  id: number;
  email: string;
  role: string;
  is_active: boolean;
  created_at: string;
};

export type SentimentTrendPoint = {
  date: string;
  avg_sentiment: number;
  interactions: number;
};

export type TopicCount = { topic: string; count: number };

export type JourneyOverview = {
  by_stage: Array<{
    stage: string;
    events: number;
    negative_events: number;
    negative_ratio: number;
    avg_sentiment: number;
  }>;
  top_friction_stages: Array<{
    stage: string;
    events: number;
    negative_events: number;
    negative_ratio: number;
    avg_sentiment: number;
  }>;
};

export type CxRiskOverview = {
  by_level: Record<string, number>;
  customers_scored: number;
  top_at_risk: Array<{
    customer_id: string;
    risk_score: number;
    risk_level: string;
    total_interactions: number;
  }>;
};

export type Recommendation = {
  id: number;
  customer_id: string | null;
  interaction_id: number | null;
  stage: string | null;
  topic: string | null;
  priority: string;
  status: string;
  recommendation: string;
  created_at: string;
};

async function jsonFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init?.headers as Record<string, string> | undefined)
  };

  const r = await fetch(path, {
    credentials: "include",
    headers,
    ...init
  });
  if (!r.ok) {
    const msg = await r.text().catch(() => "");
    throw new Error(`${r.status} ${r.statusText}${msg ? `: ${msg}` : ""}`);
  }
  return (await r.json()) as T;
}

export function getSummary(): Promise<AnalyticsSummary> {
  return jsonFetch<AnalyticsSummary>("/api/analytics/summary");
}

export function listInteractions(limit = 25): Promise<Interaction[]> {
  return jsonFetch<Interaction[]>(`/api/v1/interactions?limit=${encodeURIComponent(limit)}`);
}

export function createInteraction(payload: {
  customer_id?: string;
  channel: string;
  text: string;
}): Promise<Interaction> {
  return jsonFetch<Interaction>("/api/interactions/log", {
    method: "POST",
    body: JSON.stringify({ customer_id: payload.customer_id, channel: payload.channel, message: payload.text })
  });
}

export function register(email: string, password: string, adminSecret?: string): Promise<UserOut> {
  return jsonFetch<UserOut>("/api/v1/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password, admin_secret: adminSecret })
  });
}

export function login(email: string, password: string): Promise<TokenResponse> {
  return jsonFetch<TokenResponse>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password })
  });
}

export function logout(): Promise<{ detail: string }> {
  return jsonFetch<{ detail: string }>("/api/v1/auth/logout", {
    method: "POST"
  });
}

export function getMe(): Promise<{ id: number; email: string; role: string }> {
  return jsonFetch<{ id: number; email: string; role: string }>("/api/v1/auth/me");
}

export function getSentimentTrend(): Promise<SentimentTrendPoint[]> {
  return jsonFetch<SentimentTrendPoint[]>("/api/v1/analytics/sentiment-trend");
}

export function getTopTopics(): Promise<TopicCount[]> {
  return jsonFetch<TopicCount[]>("/api/v1/analytics/topics");
}

export function getJourneyOverview(): Promise<JourneyOverview> {
  return jsonFetch<JourneyOverview>("/api/journey");
}

export function getCxRiskOverview(): Promise<CxRiskOverview> {
  return jsonFetch<CxRiskOverview>("/api/v1/analytics/cx-risk");
}

export function listRecommendations(limit = 20): Promise<Recommendation[]> {
  return jsonFetch<Recommendation[]>(`/api/v1/analytics/recommendations?limit=${encodeURIComponent(limit)}`);
}

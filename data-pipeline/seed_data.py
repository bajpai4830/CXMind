from __future__ import annotations

import argparse
import json
import random
import sys
import time
import urllib.error
import urllib.request


POSITIVE = [
    "Super smooth onboarding, loved it.",
    "Great support experience, quick resolution.",
    "The app is fast and easy to use.",
    "Everything worked perfectly, thank you!",
    "Amazing service, I'm impressed."
]

NEUTRAL = [
    "My plan was activated today.",
    "I have a question about my invoice.",
    "Can you confirm my account details?",
    "Following up on the previous ticket.",
    "Not sure if this is expected behavior."
]

NEGATIVE = [
    "This is terrible. I'm frustrated and upset.",
    "The activation process keeps failing.",
    "Support was unhelpful and slow.",
    "I was charged incorrectly and no one responded.",
    "The app crashes every time I open it."
]

CHANNELS = ["support_ticket", "email", "social", "app_review"]


def post_json(url: str, payload: dict, *, token: str | None = None) -> dict:
    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_token(base_url: str, email: str, password: str) -> str | None:
    base_url = base_url.rstrip("/")
    login_url = base_url + "/api/v1/auth/login"
    reg_url = base_url + "/api/v1/auth/register"

    try:
        out = post_json(login_url, {"email": email, "password": password})
        return out.get("access_token")
    except urllib.error.HTTPError as e:
        if e.code not in {401, 404}:
            raise

    # Attempt bootstrap register then login.
    try:
        post_json(reg_url, {"email": email, "password": password})
    except urllib.error.HTTPError:
        # User may already exist; ignore.
        pass

    try:
        out = post_json(login_url, {"email": email, "password": password})
        return out.get("access_token")
    except urllib.error.HTTPError:
        return None


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="Seed CXMind backend with synthetic interactions.")
    p.add_argument("--base-url", default="http://127.0.0.1:8000", help="Backend base URL (default: %(default)s)")
    p.add_argument("--count", type=int, default=200, help="Number of interactions to ingest (default: %(default)s)")
    p.add_argument("--sleep-ms", type=int, default=0, help="Sleep between requests (default: %(default)s)")
    p.add_argument("--email", default="admin@example.com", help="Login email for auth-enabled API (default: %(default)s)")
    p.add_argument("--password", default="password123", help="Login password for auth-enabled API (default: %(default)s)")
    p.add_argument("--token", default="", help="Optional bearer token (overrides email/password login)")
    args = p.parse_args(argv)

    url = args.base_url.rstrip("/") + "/api/v1/interactions"
    count = max(1, args.count)

    token = args.token.strip() or get_token(args.base_url, args.email, args.password)

    for i in range(1, count + 1):
        bucket = random.random()
        if bucket < 0.34:
            text = random.choice(NEGATIVE)
        elif bucket < 0.67:
            text = random.choice(NEUTRAL)
        else:
            text = random.choice(POSITIVE)

        payload = {
            "customer_id": f"cust_{random.randint(1, 25):03d}",
            "channel": random.choice(CHANNELS),
            "text": text
        }

        try:
            out = post_json(url, payload, token=token)
        except urllib.error.URLError as e:
            print(f"[seed] failed at {i}/{count}: {e}", file=sys.stderr)
            print("[seed] is the backend running on http://127.0.0.1:8000 ?", file=sys.stderr)
            return 2

        if i == 1 or i == count or i % 25 == 0:
            print(f"[seed] {i}/{count} inserted (id={out.get('id')}, label={out.get('sentiment_label')})")

        if args.sleep_ms > 0:
            time.sleep(args.sleep_ms / 1000)

    print("[seed] done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

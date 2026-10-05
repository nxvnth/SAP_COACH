"""Small paid API client with durable reservations, caching, and no secret logging."""

# READER GUIDE
# AIcredits transport and local spending control; no retrieval happens here.
# call() builds JSON -> checks exact-request cache -> reserves budget -> sends
# one request -> parses/checks output -> saves a reusable response.
# The cache key includes the prompt, schema, model and input, so a prompt edit
# can cause a new paid request even when the learner's question is unchanged.
# Reservations are conservative local accounting, not the provider wallet balance.
# A timeout may still have been billed, so an attempted request without a valid
# cache is blocked from automatic replay. The local server serializes chat calls;
# this file does not implement a multi-process transactional billing database.

import hashlib, json, math, os, ssl, time, urllib.request, urllib.error, urllib.parse
from pathlib import Path
from .settings import ENV_FILE

ROOT = Path(__file__).resolve().parent


def read(p):
    return json.loads(p.read_text())


# Write a temporary file then replace the destination to avoid leaving half-written cache/ledger JSON.
def save(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")
    tmp.replace(p)


# An environment variable takes precedence over the project-root .env; never log the returned value.
def env_key():
    value = os.environ.get("AIAPIKEY")
    if not value and ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                if k.strip() == "AIAPIKEY":
                    value = v.strip().strip("\"'")
    if not value:
        raise RuntimeError("AIAPIKEY is missing")
    return value


class Client:
    def __init__(self, output, config=None):
        self.cfg = dict(config) if config is not None else read(ROOT / "config.json")
        self.out = output
        self.out.mkdir(parents=True, exist_ok=True)
        self.ledger_path = output / "usage.json"
        self.cache = output / "cache"
        self.cache.mkdir(exist_ok=True)
        self.ledger = (
            read(self.ledger_path) if self.ledger_path.exists() else {"calls": []}
        )

    def request(self, path, payload=None, auth=False):
        base = self.cfg.get("base_url")
        if self.cfg["provider"] == "pending_confirmation" or not base:
            raise RuntimeError("API provider must be confirmed before network access")
        headers = {"Content-Type": "application/json"}
        if auth:
            headers["Authorization"] = "Bearer " + env_key()
        req = urllib.request.Request(
            urllib.parse.urljoin(base.rstrip("/") + "/", path),
            data=json.dumps(payload).encode() if payload is not None else None,
            headers=headers,
        )
        try:
            import certifi

            context = ssl.create_default_context(cafile=certifi.where())
        except ImportError:
            context = ssl.create_default_context()
        try:
            with urllib.request.urlopen(req, timeout=90, context=context) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            # Do not echo provider bodies: they could contain supplied headers or source data.
            raise RuntimeError(
                f"Provider returned HTTP {exc.code}; no automatic retry"
            ) from None
        except (urllib.error.URLError, TimeoutError):
            raise RuntimeError(
                "Network/timeout failure; no automatic retry, reservation retained"
            ) from None

    # Read the gateway catalogue to verify the requested model and obtain rates for local reservations.
    def preflight(self):
        if self.cfg["provider"] != "aicredits":
            raise RuntimeError("Unsupported provider")
        models = self.request("/api/models")["data"]
        m = next((x for x in models if x["id"] == self.cfg["model"]), None)
        if not m or not m.get("is_active"):
            raise RuntimeError("Requested model unavailable; no model substitution")
        # INR catalogue includes the gateway buffer. Convert back to USD equivalent.
        fx = float(m["exchange_rate"])
        prices = {
            "prompt": float(m["input_cost_per_token_inr"]) / fx,
            "completion": float(m["output_cost_per_token_inr"]) / fx,
            "request": 0,
        }
        if any(
            not math.isfinite(prices[k]) or prices[k] <= 0
            for k in ["prompt", "completion"]
        ):
            raise RuntimeError("Invalid rates")
        meta = dict(
            model=m["id"],
            pricing=prices,
            catalogue=m,
            pricing_basis="INR catalogue / published exchange rate; USD equivalent",
            checked_at=time.time(),
        )
        save(self.out / "provider_model.json", meta)
        return meta

    # Build one structured request, check its cache/budget, submit once, then validate and save the response.
    def call(self, stage, system, user, schema, max_output=None):
        meta = read(self.out / "provider_model.json")
        limit = max_output or self.cfg["max_output_tokens"]
        payload = {
            "model": self.cfg["model"],
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps(user, ensure_ascii=False)},
            ],
            "max_tokens": limit,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "graph_" + stage,
                    "strict": True,
                    "schema": schema,
                },
            },
        }
        if self.cfg["provider"] == "aicredits":
            # Gateway documents JSON mode; enforce the exact schema locally.
            payload["response_format"] = {"type": "json_object"}
            payload["no_cache"] = True
            payload["messages"][0]["content"] += " Required JSON schema: " + json.dumps(
                schema
            )
        # Hash the full payload: changing the model, prompt, question or schema creates a different cache entry.
        key = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        cached = self.cache / (key + ".json")
        # A cached provider result still goes through service/contract validation.
        # Caching successful JSON does not imply that the learner-facing answer
        # has already passed source checks or been committed to a conversation.
        if cached.exists():
            return read(cached)["parsed"]
        # An unresolved attempt is never silently charged again.
        if any(c["request_hash"] == key for c in self.ledger["calls"]):
            raise RuntimeError(
                "This request was attempted without a usable cache; inspect usage before explicit retry"
            )
        prices = meta["pricing"]
        # Conservative UTF-8 byte bound, including schema and framing allowance; not a tokenizer estimate.
        max_input = len(json.dumps(payload, ensure_ascii=False).encode()) + 2048
        reserve = (
            max_input * prices["prompt"]
            + limit * prices["completion"]
            + prices["request"]
        ) * 1.25
        # Count retained reservations as spent exposure when actual billing is unknown.
        exposure = sum(
            c.get("charged_or_reserved_usd", c["reserved_usd"])
            for c in self.ledger["calls"]
        )
        if (
            len(self.ledger["calls"]) >= self.cfg["max_calls"]
            or exposure + reserve > self.cfg["budget_usd"]
        ):
            raise RuntimeError(
                "Pilot budget/call cap would be exceeded; stopped before request"
            )
        entry = dict(
            stage=stage,
            request_hash=key,
            reserved_usd=reserve,
            charged_or_reserved_usd=reserve,
            status="reserved",
            time=time.time(),
        )
        # Persist the reservation before network access so a crash or timeout cannot silently reset the budget.
        self.ledger["calls"].append(entry)
        save(self.ledger_path, self.ledger)
        print(
            f"{stage}: submitting bounded call; reservation ${reserve:.4f}", flush=True
        )
        data = self.request("chat/completions", payload, auth=True)
        usage = data.get("usage", {})
        entry["usage"] = usage
        entry["generation_id"] = data.get("id")
        entry["returned_model"] = data.get("model")
        cost = usage.get("cost")
        if (
            self.cfg["provider"] == "openrouter"
            and isinstance(cost, (int, float))
            and cost >= 0
        ):
            entry["charged_or_reserved_usd"] = cost
            entry["cost_status"] = "provider_reported"
        else:
            entry["cost_status"] = "unknown_reservation_retained"
        entry["status"] = "response_received"
        save(self.ledger_path, self.ledger)
        # A truncated or refused response is not usable JSON, even if the provider billed the request.
        if not data.get("choices") or data["choices"][0].get("finish_reason") != "stop":
            raise RuntimeError(
                "Incomplete/refused output; usage saved, no automatic retry"
            )
        try:
            parsed = json.loads(data["choices"][0]["message"]["content"])
        except (ValueError, KeyError, TypeError):
            raise RuntimeError(
                "Invalid JSON response; usage saved, no automatic retry"
            ) from None
        validate_schema(parsed, schema)
        save(
            cached,
            dict(
                stage=stage,
                request_hash=key,
                parsed=parsed,
                usage=usage,
                generation_id=data.get("id"),
            ),
        )
        entry["status"] = "cached"
        save(self.ledger_path, self.ledger)
        print(
            f'{stage}: cached; accounted ${entry["charged_or_reserved_usd"]:.5f}',
            flush=True,
        )
        return parsed


# This lightweight structural check is supplemented by the Pydantic and citation checks in contracts.py.
def validate_schema(value, schema):
    kind = schema.get("type")
    if kind == "object":
        if not isinstance(value, dict):
            raise ValueError("Expected JSON object")
        if set(schema.get("required", [])) - set(value):
            raise ValueError("Missing JSON fields")
        if schema.get("additionalProperties") is False and set(value) - set(
            schema["properties"]
        ):
            raise ValueError("Unexpected JSON fields")
        for k, v in value.items():
            validate_schema(v, schema.get("properties", {}).get(k, {}))
    elif kind == "array":
        if not isinstance(value, list):
            raise ValueError("Expected JSON array")
        for item in value:
            validate_schema(item, schema["items"])
    elif kind == "string" and not isinstance(value, str):
        raise ValueError("Expected JSON string")
    if "enum" in schema and value not in schema["enum"]:
        raise ValueError("Invalid enum value")

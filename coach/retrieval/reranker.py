"""NVIDIA hosted text reranking. No implicit retries; durable attempted-call ledger."""

# READER GUIDE
# Hosted NVIDIA relevance scoring, separate from answer generation.
# The request contains a question and an ordered list of text passages. The API
# returns positions and scores; positions must be mapped back to that same list.
# A logit is a ranking signal, not a probability that a passage is correct.
# rankings() checks that the response covers every submitted position exactly
# once and contains finite scores. Cache hits reuse the original API latency
# stored in the response; that value is not the elapsed time of the cache read.
# This client's attempt cap is separate from the AIcredits dollar reservation cap.

import hashlib, json, math, os, ssl, time, urllib.request
from pathlib import Path

from ..settings import ENV_FILE

MODEL = "nvidia/llama-nemotron-rerank-vl-1b-v2"
URL = "https://ai.api.nvidia.com/v1/retrieval/nvidia/llama-nemotron-rerank-vl-1b-v2/reranking"


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2))
    tmp.replace(path)


# Send text passages to the hosted reranker; this call scores relevance and does not generate an answer.
def body(query, documents):
    if (
        not query.strip()
        or not 1 <= len(documents) <= 1000
        or any(not d.strip() for d in documents)
    ):
        raise ValueError("Invalid ranking inputs")
    return dict(
        model=MODEL,
        query={"text": query},
        passages=[{"text": d} for d in documents],
        truncate="END",
    )


def fingerprint(payload):
    return hashlib.sha256(
        json.dumps({"url": URL, "body": payload}, sort_keys=True).encode()
    ).hexdigest()


# Require one finite score for every submitted position before trusting the provider’s ordering.
def rankings(response, n):
    rows = response["rankings"]
    if (
        len(rows) != n
        or any(type(x["index"]) is not int for x in rows)
        or sorted(x["index"] for x in rows) != list(range(n))
    ):
        raise ValueError("Incomplete or duplicate response indices")
    if any(
        type(x["logit"]) not in (int, float) or not math.isfinite(x["logit"])
        for x in rows
    ):
        raise ValueError("Invalid logit")
    return sorted(rows, key=lambda x: (-x["logit"], x["index"]))


def key():
    value = os.environ.get("NVIDIA_API_KEY")
    if not value and ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                if k.strip() == "NVIDIA_API_KEY":
                    value = v.strip().strip("\"'")
    if not value:
        raise RuntimeError(
            "Add NVIDIA_API_KEY to the project root .env before ranking evidence"
        )
    return value


class Client:
    def __init__(self, out, max_calls=200):
        self.out = Path(out)
        self.max_calls = max_calls

    def call(self, payload):
        # Cache by endpoint and complete request body, so different queries or candidate text cannot share scores.
        sha = fingerprint(payload)
        cache = self.out / "cache" / f"{sha}.json"
        ledger = self.out / "usage.json"
        if cache.exists():
            response = json.loads(cache.read_text())
            rankings(response, len(payload["passages"]))
            return response
        calls = json.loads(ledger.read_text()) if ledger.exists() else []
        if any(c["sha256"] == sha for c in calls):
            raise RuntimeError(
                "Prior attempt has no usable cache; inspect usage.json before explicitly retrying"
            )
        if len(calls) >= self.max_calls:
            raise RuntimeError("Attempt cap reached")
        api_key = key()
        entry = dict(
            sha256=sha,
            status="attempted",
            passages=len(payload["passages"]),
            at=time.time(),
        )
        # Record the attempt before sending it; a missing response does not prove the provider did not charge.
        calls.append(entry)
        save(ledger, calls)
        req = urllib.request.Request(
            URL,
            data=json.dumps(payload).encode(),
            headers={
                "Authorization": "Bearer " + api_key,
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            import certifi

            start = time.perf_counter()
            with urllib.request.urlopen(
                req,
                context=ssl.create_default_context(cafile=certifi.where()),
                timeout=60,
            ) as resp:
                result = json.load(resp)
            result["_client_latency_ms"] = (time.perf_counter() - start) * 1000
            rankings(result, len(payload["passages"]))
            save(cache, result)
            entry.update(
                status="completed",
                usage=result.get("usage"),
                latency_ms=result["_client_latency_ms"],
            )
        except Exception as exc:
            entry.update(
                status="failed_or_unknown_charge", error_type=type(exc).__name__
            )
            save(ledger, calls)
            raise RuntimeError(
                "NVIDIA request failed; attempt retained, no automatic retry. Inspect usage.json."
            ) from None
        save(ledger, calls)
        return result

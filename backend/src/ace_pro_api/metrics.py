from prometheus_client import Counter, Histogram

HTTP_REQUESTS = Counter(
    "ace_pro_http_requests_total",
    "HTTP requests handled by the Ace Pro API.",
    ("method", "route", "status"),
)

HTTP_REQUEST_DURATION = Histogram(
    "ace_pro_http_request_duration_seconds",
    "HTTP request duration for the Ace Pro API.",
    ("method", "route"),
)

UPLOAD_EVENTS = Counter(
    "ace_pro_upload_events_total",
    "Video upload lifecycle events.",
    ("event",),
)


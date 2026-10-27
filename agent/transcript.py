"""Bound transcript data packets, including JSON escaping, for LiveKit delivery."""

import json


def append_transcript(current, text):
    combined = (current + " " + text.strip()).strip()[:8000]

    def encode(value):
        return json.dumps({"text": value}, ensure_ascii=False).encode("utf-8")

    low, high = 0, len(combined)
    while low < high:
        middle = (low + high + 1) // 2
        if len(encode(combined[:middle])) <= 12000:
            low = middle
        else:
            high = middle - 1
    combined = combined[:low]
    return combined, encode(combined)

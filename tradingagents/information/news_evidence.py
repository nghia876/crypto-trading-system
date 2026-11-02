"""Rights-scoped feed evidence. No body fetch, rights inference or text synthesis."""

import hashlib
from html.parser import HTMLParser

EVIDENCE_LEVELS = ("HEADLINE_METADATA_ONLY", "SNIPPET", "EXCERPT", "FEED_SUMMARY", "FULL_BODY")


def replay_payload(payload, specimen):
    """Preserve frozen metadata-only specimen contracts; never mutate live evidence."""
    result = dict(payload)
    if specimen.get("intake_contract_version", 1) == 1:
        additions = {"source_item_index", "source_item_order", "mention_identity",
                     "copy_lineage", "evidence_level", "body_status", "summary_status",
                     "evidence_rights", "evidence_rights_reference", "evidence_rights_review_date"}
        result = {key: value for key, value in result.items() if key not in additions}
    else:
        result["source_item_index"] = specimen["source_item_index"]
        result["snapshot_item_count"] = specimen["snapshot_item_count"]
        result["excluded_article_count"] = specimen["excluded_article_count"]
    return result


class _Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.hidden += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style"}:
            self.hidden = max(0, self.hidden - 1)

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def feed_evidence(config, summary, field):
    """All four rights require explicit exact-scope approval; unknown fails closed.

    Registry metadata is reviewed configuration, never taken from remote feed text.
    FULL_BODY requires a separate eligible collector; a feed summary is never a body.
    """
    metadata = dict(config.source.metadata)
    rights = {name: metadata.get(f"summary_{name}", "unknown")
              for name in ("access", "retention", "inference", "redistribution")}
    permitted = (all(value == "permitted" for value in rights.values())
                 and bool(metadata.get("summary_rights_reference"))
                 and bool(metadata.get("summary_rights_review_date")))
    result = {
        "evidence_level": "HEADLINE_METADATA_ONLY",
        "body_status": "not_retrieved",
        "summary_status": "not_supplied" if not summary else "rights_gated",
        "evidence_rights": rights,
        "evidence_rights_reference": metadata.get("summary_rights_reference"),
        "evidence_rights_review_date": metadata.get("summary_rights_review_date"),
    }
    if summary and permitted:
        parser = _Text()
        parser.feed(summary)
        text = " ".join(" ".join(parser.parts).split())
        limit = 1200
        if text:
            result.update(evidence_level="FEED_SUMMARY", summary_status="retained",
                          evidence_text=text[:limit], evidence_field=field,
                          evidence_text_truncated=len(text) > limit,
                          evidence_text_original_chars=len(text),
                          evidence_original_text=summary[:2400],
                          evidence_original_truncated=len(summary) > 2400,
                          evidence_original_sha256=hashlib.sha256(summary.encode()).hexdigest(),
                          evidence_transformation="HTML text extraction and whitespace normalization; prefix cap 1200",
                          evidence_attribution=config.source.provider,
                          evidence_endpoint=config.source.endpoint)
    return result

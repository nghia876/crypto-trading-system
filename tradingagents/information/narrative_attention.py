"""Descriptive sampled article attention; no event equivalence or truth score."""

from datetime import timedelta


def sampled_attention(view, *, window=timedelta(days=1)):
    """Compare equal first-known windows using only cutoff-eligible history.

    A URL is an article proxy, not a social mention or a corroborated incident.
    Repeat polls, revisions and cross-feed copies never create new article counts.
    """
    if window <= timedelta(0):
        raise ValueError('positive window required')
    end = view.decision_time
    first = {}
    copies = 0
    publishers, channels = set(), set()
    for row in view.evidence_history:
        if row.metric != 'narrative.event' or row.available_at > end:
            continue
        copies += 1
        key = row.payload.get('canonical_url') or row.subject
        first[key] = min(first.get(key, row.available_at), row.available_at)
        publishers.add(row.payload.get('publisher_group', 'UNKNOWN'))
        channels.add(row.source_id)
    current = sum(end-window < at <= end for at in first.values())
    previous = sum(end-2*window < at <= end-window for at in first.values())
    return {'current_articles': current, 'previous_articles': previous,
            'article_change': current-previous, 'retained_versions': copies,
            'unique_articles': len(first), 'publishers': sorted(publishers),
            'channels': sorted(channels), 'window_seconds': window.total_seconds(),
            'cutoff': end.isoformat(), 'origin': 'UNKNOWN', 'syndication': 'UNKNOWN',
            'corroboration': 'NOT_ASSESSED', 'reach': 'UNKNOWN',
            'coverage': 'sampled feeds; offline/upstream/social/language gaps UNKNOWN',
            'rumor_state': 'unchanged; article counts do not establish truth'}

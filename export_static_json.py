"""
Script to generate static segments.json for offline frontend development (Person 3).
"""

import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from priority_engine.dataset import global_repo
from priority_engine.scoring import DEFAULT_WEIGHTS
from confidence_engine.surveys import get_all_sample_surveys, HIGH_CONFIDENCE_SURVEY, LOW_CONFIDENCE_SURVEY
from confidence_engine.scoring import calculate_confidence
from confidence_engine.dig_prevention import global_dig_store
from confidence_engine.verification import global_verification_store

def export_json(base_dir: str = "."):
    # 1. Segments
    segments = global_repo.get_all_scored_segments(sort_by_priority=True)
    segments_payload = {
        "metadata": {
            "title": "METHANOS CGD Pipeline Segment Priority Data",
            "version": "1.0.0",
            "total_segments": len(segments),
            "default_weights": DEFAULT_WEIGHTS,
        },
        "segments": segments
    }
    seg_file = os.path.join(base_dir, "segments.json")
    with open(seg_file, "w", encoding="utf-8") as f:
        json.dump(segments_payload, f, indent=2)
    print(f"Successfully exported {len(segments)} segments to {seg_file}")

    # 2. Surveys & Benchmarks
    surveys = get_all_sample_surveys(evaluated=True)
    high_eval = calculate_confidence(dict(HIGH_CONFIDENCE_SURVEY))
    high_card = dict(HIGH_CONFIDENCE_SURVEY)
    high_card.update(high_eval)

    low_eval = calculate_confidence(dict(LOW_CONFIDENCE_SURVEY))
    low_card = dict(LOW_CONFIDENCE_SURVEY)
    low_card.update(low_eval)

    surveys_payload = {
        "metadata": {
            "title": "METHANOS Survey Quality Control & Confidence Data",
            "version": "1.0.0",
            "total_surveys": len(surveys),
        },
        "benchmarks": {
            "high_confidence_example": high_card,
            "low_confidence_example": low_card,
        },
        "surveys": surveys
    }
    survey_file = os.path.join(base_dir, "surveys.json")
    with open(survey_file, "w", encoding="utf-8") as f:
        json.dump(surveys_payload, f, indent=2)
    print(f"Successfully exported {len(surveys)} surveys to {survey_file}")

    # 3. 48-Hour Dig Notices & Control Room Alerts
    dig_notices = global_dig_store.get_all()
    dig_payload = {
        "metadata": {
            "title": "METHANOS 48-Hour Pre-Excavation Early Warning & Prevention Tickets",
            "version": "1.0.0",
            "total_notices": len(dig_notices),
        },
        "notices": dig_notices
    }
    dig_file = os.path.join(base_dir, "dig_notices.json")
    with open(dig_file, "w", encoding="utf-8") as f:
        json.dump(dig_payload, f, indent=2)
    print(f"Successfully exported {len(dig_notices)} dig notices to {dig_file}")

    # 4. Anomaly Verification Tickets
    tickets = global_verification_store.get_all()
    tickets_payload = {
        "metadata": {
            "title": "METHANOS Anomaly Ground Verification Tickets",
            "version": "1.0.0",
            "total_tickets": len(tickets),
        },
        "tickets": tickets
    }
    ticket_file = os.path.join(base_dir, "verification_tickets.json")
    with open(ticket_file, "w", encoding="utf-8") as f:
        json.dump(tickets_payload, f, indent=2)
    print(f"Successfully exported {len(tickets)} verification tickets to {ticket_file}")

if __name__ == "__main__":
    out_dir = os.path.dirname(__file__) or "."
    export_json(out_dir)

#!/usr/bin/env python3
"""
api/parse_xml.py
Parses modified_sms_v2.xml into api/data/transactions.json.
Author: David Irihose
"""
from __future__ import annotations
import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

AMOUNT_PATTERN = re.compile(r"([\d,]+(?:\.\d+)?)\s*RWF", re.IGNORECASE)
FEE_PATTERN = re.compile(
    r"fee\s*(?:was|of|paid|:)?\s*[:=]?\s*([\d,]+(?:\.\d+)?)\s*RWF",
    re.IGNORECASE,
)
TXID_PATTERN = re.compile(
    r"(?:TxId|Transaction\s*Id|Financial\s*Transaction\s*Id)\s*[:=]?\s*(\d+)",
    re.IGNORECASE,
)
FROM_PATTERN = re.compile(
    r"from\s+([A-Z][A-Za-z\s\.\-']+?)(?:\s*\(|\s+on\s|\s+has\s|\.)",
    re.IGNORECASE,
)
TO_PATTERN = re.compile(
    r"to\s+([A-Z][A-Za-z\s\.\-']+?)(?:\s*\(|\s+on\s|\s+has\s|\.)",
    re.IGNORECASE,
)
BALANCE_PATTERN = re.compile(
    r"(?:new\s+balance|your\s+(?:new\s+)?balance)\s*[:=]?\s*"
    r"([\d,]+(?:\.\d+)?)\s*RWF",
    re.IGNORECASE,
)


def clean_amount(raw):
    if not raw:
        return None
    cleaned = raw.replace(",", "").replace("RWF", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


def extract_first(pattern, text):
    m = pattern.search(text)
    return m.group(1).strip() if m else None


def classify(body):
    b = body.lower()
    if "received" in b and "from" in b:
        return "Incoming Money"
    if ("payment of" in b or "payment to" in b) and "completed" in b:
        return "Payment to Code Holder"
    if "transferred to" in b or "sent to" in b:
        return "Transfer to Mobile"
    if "bank deposit" in b or "deposited" in b:
        return "Bank Deposit"
    if "airtime" in b:
        return "Airtime Purchase"
    if "cash power" in b or "cash-power" in b:
        return "Cash Power"
    if "internet" in b or "bundle" in b:
        return "Internet Bundle"
    if "withdraw" in b:
        return "Cash Withdrawal"
    if "reversed" in b or "reversal" in b:
        return "Reversal"
    return "Other"


def ms_to_iso(ms_str):
    if not ms_str or not ms_str.isdigit():
        return None
    return datetime.fromtimestamp(int(ms_str) / 1000, tz=timezone.utc).isoformat()


def parse_record(sms_elem, idx):
    attrib = sms_elem.attrib
    body = attrib.get("body", "") or ""
    category = classify(body)

    sender = None
    receiver = None
    if category == "Incoming Money":
        sender = extract_first(FROM_PATTERN, body)
        receiver = "Self"
    elif category in ("Payment to Code Holder", "Transfer to Mobile"):
        sender = "Self"
        receiver = extract_first(TO_PATTERN, body)
    elif category == "Bank Deposit":
        sender = "Bank"
        receiver = "Self"
    elif category == "Airtime Purchase":
        sender = "Self"
        receiver = "MTN Airtime"
    elif category == "Cash Withdrawal":
        sender = "Self"
        receiver = extract_first(TO_PATTERN, body) or "Agent"
    else:
        sender = attrib.get("address") or None

    return {
        "id": idx,
        "external_txn_id": extract_first(TXID_PATTERN, body),
        "type": category,
        "amount": clean_amount(extract_first(AMOUNT_PATTERN, body)),
        "fee": clean_amount(extract_first(FEE_PATTERN, body)) or 0.0,
        "new_balance": clean_amount(extract_first(BALANCE_PATTERN, body)),
        "sender": sender,
        "receiver": receiver,
        "timestamp": ms_to_iso(attrib.get("date")),
        "readable_date": attrib.get("readable_date"),
        "raw_body": body,
    }


def parse_xml(xml_path):
    if not xml_path.exists():
        raise FileNotFoundError(f"XML file not found: {xml_path.resolve()}")
    tree = ET.parse(xml_path)
    root = tree.getroot()
    sms_elements = root.findall("sms") or root.findall(".//sms")
    if not sms_elements:
        raise RuntimeError("No <sms> elements found in XML")

    records = []
    skipped = 0
    for i, sms in enumerate(sms_elements, start=1):
        try:
            records.append(parse_record(sms, i))
        except Exception as e:
            skipped += 1
            print(f"[warn] record {i}: {e}", file=sys.stderr)
    print(f"[info] Parsed {len(records)} records ({skipped} skipped)")
    return records


def main():
    ap = argparse.ArgumentParser(description="Parse MoMo SMS XML -> JSON")
    ap.add_argument("--input", default="data/modified_sms_v2.xml", type=Path)
    ap.add_argument("--output", default="api/data/transactions.json", type=Path)
    args = ap.parse_args()

    print(f"[info] Reading {args.input}")
    records = parse_xml(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(records, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"[ok] Wrote {len(records)} records -> {args.output}")


if __name__ == "__main__":
    main()

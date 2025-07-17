#!/usr/bin/env python

import os
import json
from datetime import datetime, timedelta
from elasticsearch import Elasticsearch


def main():

    es = Elasticsearch("http://10.1.1.1:9200")
    index = ".ds-filebeat-*"

    ignore_list = [
        "DOT1X-5-FAIL", "LINEPROTO-5-UPDOWN", "LINEPROTO-3-UPDOWN",
        "LINK-3-UPDOWN", "LINK-5-UPDOWN", "ILPOWER-5-IEEE_DISCONNECT",
        "ILPOWER-5-POWER_GRANTED", "SEC_LOGIN-5-LOGIN_SUCCESS", "SYS-6-LOGOUT",
        "SSH-3-NO_MATCH", "SSH-5-SSH2_CLOSE", "SSH-5-SSH2_SESSION",
        "SSH-5-SSH2_USERAUTH", "ILPOWER-5-DETECT", "SSH-3-DH_SIZE", "MAB-5-FAIL",
        "SW_MATM-4-MACFLAP_NOTIF", "MAB-5-SUCCESS", "EPM-6-IPEVENT",
        "EPM-6-POLICY_APP_SUCCESS", "IPPHONE-6-UNREGISTER_NORMAL",
        "SYS-5-CONFIG_I", "LINK-5-CHANGED", "SYS-6-TTY_EXPIRE_TIMER",
        "AAAA-4-CLI_DEPRECATED", "SYS-6-CLOCKUPDATE"
    ]

    now = datetime.utcnow()
    yesterday = now - timedelta(hours=24)

    response = es.search(
        index=index,
        size=0,
        query={
            "range": {
                "@timestamp": {
                    "gte": yesterday.isoformat(),
                    "lte": now.isoformat()
                }
            }
        },
        aggs={
            "event_types": {
                "terms": {
                    "field": "dissect.event_type",
                    "size": 1000
                },
                "aggs": {
                    "source_ips": {
                        "terms": {
                            "field": "dissect.hostname",
                            "size": 1000
                        }
                    }
                }
            }
        }
    )

    aggregated_logs = []

    for event_bucket in response["aggregations"]["event_types"]["buckets"]:
        event_type = event_bucket["key"]
        if event_type in ignore_list:
            continue

        total_count = event_bucket["doc_count"]
        items = []

        for ip_bucket in event_bucket["source_ips"]["buckets"]:
            ip = ip_bucket["key"]
            ip_count = ip_bucket["doc_count"]

            example_hit = es.search(
                index=index,
                size=1,
                query={
                    "bool": {
                        "must": [
                            {"term": {"dissect.event_type": event_type}},
                            {"term": {"dissect.hostname": ip}}
                        ]
                    }
                },
                sort=[{"@timestamp": "desc"}]
            )

            if example_hit["hits"]["hits"]:
                source = example_hit["hits"]["hits"][0]["_source"]
                message = source.get("dissect", {}).get("message", "")
            else:
                message = ""

            items.append({
                "ip": ip,
                "count": ip_count,
                "message": message
            })

        aggregated_logs.append({
            "event_type": event_type,
            "count": total_count,
            "items": items
        })

    aggregated_logs.sort(key=lambda x: x["count"], reverse=True)

    os.makedirs("results", exist_ok=True)
    with open("results/logs.json", "w", encoding="utf-8") as f:
        json.dump(aggregated_logs, f, ensure_ascii=False, indent=2)

    print("\n==> result is saved to results/logs.json")


if __name__ == "__main__":
    main()

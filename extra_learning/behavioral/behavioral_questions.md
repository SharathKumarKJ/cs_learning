# Behavioral Interview Questions for Senior Data Engineers (Detailed)

Use the STAR framework: **Situation**, **Task**, **Action**, **Result**. Always quantify the result.

## Leadership and ownership

### 1. Owning a critical pipeline incident.
Describe a real outage: detection (alerts, freshness check), triage (who you pulled in, communication cadence), root cause (e.g. upstream schema change, S3 throttling, skew), fix (hotfix vs proper fix), and the postmortem improvements (alerting, contracts, runbook). Highlight ownership without blame.

### 2. Leading design from scratch.
Walk through requirements gathering, options considered (build vs buy, batch vs streaming, warehouse choice), trade-offs, the decision, the rollout plan, and what you would change in hindsight. Show you can balance technical depth with stakeholder needs.

### 3. Mentoring a junior engineer.
Pick a concrete example: pair-programmed on a tricky Spark job, set up a learning plan, reviewed their PRs with detailed feedback, championed their first solo design. Tie to their growth (got promoted, owned a service).

### 4. Disagreeing with a manager or peer.
Show that you listened, brought data, and proposed an alternative. Even if you "lost," you committed once the decision was made. Avoid stories that paint anyone as the villain.

## Problem solving

### 5. Most complex pipeline you built.
Describe scale (TBs/day, latency SLA), architecture (sources, transformations, sinks), specific hard problems (skew, late-arriving data, CDC merge, idempotency), and the impact. Be ready to dive into any chosen layer.

### 6. Tough debugging session.
A skewed Spark join, a non-deterministic Airflow failure, a silent data corruption found weeks later — pick one, walk through your hypotheses, instrumentation added, the actual bug, and the fix. Show structured problem-solving.

### 7. Performance optimization delivered.
Quantify: e.g. "reduced ETL from 4h to 35 min by switching to broadcast joins on dimensions and enabling AQE; saved $X/month." Always include the metric before and after.

### 8. Reducing cloud cost.
A common high-impact story: e.g. partition pruning + column pruning saved 70% on Athena spend; right-sizing Snowflake warehouses + auto-suspend saved $40k/year; moving cold data to Glacier cut S3 bill 25%.

## Collaboration

### 9. Working with analysts/data scientists.
Show empathy for their workflows (notebooks, SQL, "I need it yesterday"), how you provided self-service (curated marts, dbt, semantic layer), and how you reduced repeated requests. Bonus: examples of teaching them dbt/SQL patterns.

### 10. Stakeholder push-back.
Maybe finance wanted real-time but data was only daily — you walked through cost, complexity, and proposed near-real-time (15 min) that met the actual business need. Show negotiation and outcome.

### 11. Communicating trade-offs to non-technical people.
Use analogies (warehouse = library, lakehouse = combined library + warehouse), focus on impact and risk in business terms, avoid jargon. Be ready to give an example of a doc/presentation that landed.

## Failure and learning

### 12. A project that failed.
Honest, ownership-heavy: e.g. "we built a streaming pipeline when batch would have served — over-engineered, slow to deliver, eventually deprecated." Conclude with what you learned and how you applied it next time.

### 13. A mistake in production.
A truncate on the wrong table, a wrong watermark, a missing `WHERE` in a delete — describe the incident, immediate mitigation, restore from backup/time travel, and the *systemic* fix (CI check, dual approval, dry-run flag).

### 14. What you learned in the last 6 months.
Something concrete and current: liquid clustering, Iceberg vs Delta trade-offs, AQE internals, a new orchestrator, a new ML use case. Show curiosity and continuous learning.

## Decision-making

### 15. A hard technical trade-off.
Snowflake vs Databricks, Kafka vs Kinesis, batch vs streaming, dbt vs custom SQL. Walk through the framework you used: cost, team skills, vendor lock-in, time-to-value, scale. Show structured thinking.

### 16. Buy vs build.
A real example: built a custom Airflow plugin or bought an iPaaS, built a custom data quality framework or adopted Soda. Discuss criteria and outcome.

### 17. Prioritizing when everything is urgent.
Use a framework (impact × urgency, blast radius, reversibility, dependencies). Show that you communicate trade-offs to stakeholders and say no with data, not opinions.

## Tips
- **Quantify**: rows/day, TBs, $/month, %, latency, SLA.
- **Two-three minute answers** — practice timing.
- Always include the **result and learning**.
- Have **8-10 stories** ready, tagged to common themes.

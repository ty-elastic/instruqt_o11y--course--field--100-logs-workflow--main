---
slug: pii
id: nxo4fxk0dray
type: challenge
title: Protecting Data
tabs:
- id: anstrmekrtc2
  title: Elasticsearch
  type: service
  hostname: kubernetes-vm
  path: /app/discover#/?_g=(filters:!(),query:(language:kuery,query:''),refreshInterval:(pause:!t,value:60000),time:(from:now-1h,to:now))&_a=(breakdownField:log.level,columns:!(),dataSource:(type:esql),filters:!(),hideChart:!f,interval:auto,query:(esql:'FROM%20logs-proxy.otel-default'),sort:!(!('@timestamp',desc)))
  port: 443
difficulty: basic
timelimit: 600
enhanced_loading: false
---
Sometimes our data contains PII information which needs to be redacted and kept only for a limited time.

# Redaction

Let's have a look again at our proxy log records. 

1. Open the [button label="Elasticsearch"](tab-0) tab
2. Click `Discover` in the left-hand navigation pane
3. Execute the following query:
```esql
FROM logs-proxy.otel-default
```
4. Open the first log record by clicking on the double arrow icon under `Actions`
5. Click on the `Table` tab in the flyout
6. Note that the client's IP address is visible in `body.text`

Fortunately, Elasticsearch has a processor easily and automatically redact such PII information.

1. Open the [button label="Elasticsearch"](tab-0) tab
2. Go to `Streams` using the left-hand navigation pane
3. Select `logs-proxy.otel-default` from the list of Streams.
4. Select the `Processing` tab
5. Select `Create processor` from the menu `Create`
6. Select the `Redact` Processor
7. Set the `Field` field to:
  ```
  body.text
  ```
8. Set the `Patterns` field to:
  ```
  %{IP:client_ip}
  ```
9. Click `Create`
10. Click `Save changes` in the bottom-right
11. Click `Confirm changes` in the resulting dialog

> [!NOTE]
> This redaction will apply to ALL roles, not just the limited viewer

Now let's jump back to Discover by clicking `Discover` in the left-hand navigation pane.

Execute the following query:
```esql
FROM logs-proxy.otel-default
```

1. Open the first log record by clicking on the double arrow icon under `Actions`
2. Click on the `Table` tab in the flyout
3. Note that any presence of the client's ip address in `body.text` has been redacted as `<client_ip>`

# Summary

Let's take stock of what we know:

* a small percentage of requests are experiencing 500 errors
* the errors started occurring around 80 minutes ago
* the only error type seen is 500
* the errors occur over all APIs
* the errors occur only in the `TH` region
* the errors occur only with browsers based on Chrome v136

And what we've done:

* Created several graphs to help quantify the extent of the problem
* Parsed the logs at ingest-time for quicker and more powerful analysis
* Created a dashboard to monitor our ingress proxy
* Create a SLO (with alert) to let us know if we ever return a significant number of non-200 error codes over time
* Geocoded client IP to associate location information with clients
* Created visualizations to help us visually locate clients and errors
* Parsed the user agent string to associate browser information with clients
* Determined, using client location and browser information, the root cause of our problem
* Created a table in our dashboard iterating User Agents in the wild
* Created a nightly report to snapshot our dashboard
* Created an alert to let us know when a new User Agent string appears
* Setup redaction to remove IP addresses from the log message body

# Wrap-Up

Over the course of this lab, we learned about:

* Using ES|QL to search logs
* Using ES|QL to parse logs at query-time
* Using ES|QL to do advanced aggregations, analytics, and visualizations
* Creating a dashboard
* Using AI Assistant to help write ES|QL queries
* Using Streams to setup ingest-time log processing pipeline (GROK parsing, geo-location, User Agent parsing)
* Setting up SLOs and alerts
* Using Maps to visualize geographic information
* Scheduling dashboard reports
* Setting up a Pivot Transform and Alert
* Setting up redaction

We put these technologies to use in a practical workflow which quickly took us from an unknown problem to a definitive Root Cause. Furthermore, we've setup alerts to ensure we aren't caught off-guard in the future. Finally, we built a really nice custom dashboard to help us monitor the health of our Ingress Status.

**All of this from just a lowly nginx access file. That's the power of your logs unlocked by Elastic.**


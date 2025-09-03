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
  port: 30001
- id: qxodixi0jlll
  title: Elasticsearch (Limited)
  type: service
  hostname: kubernetes-vm
  path: /app/discover#/?_g=(filters:!(),query:(language:kuery,query:''),refreshInterval:(pause:!t,value:60000),time:(from:now-1h,to:now))&_a=(breakdownField:log.level,columns:!(),dataSource:(type:esql),filters:!(),hideChart:!f,interval:auto,query:(esql:'FROM%20logs-proxy.otel-default'),sort:!(!('@timestamp',desc)))
  port: 30002
  custom_request_headers:
  - key: Authorization
    value: Basic bGltaXRlZF91c2VyOmVsYXN0aWM=
difficulty: basic
timelimit: 600
enhanced_loading: false
---
Sometimes our data contains PII information which needs to be restricted to a need-to-know basis and kept only for a limited time.

# Limiting access

With Elastic's in-built support for [RBAC](https://www.elastic.co/docs/deploy-manage/users-roles/cluster-or-deployment-auth/user-roles), we can limit access at the index, document, or field level.

In this example, we've created a limited_user with a limited_role which restricts access to the `client.ip` and `body.text` fields (to avoid implicitly leaking the `client.ip`).

In the Elasticsearch tab, we are logged in as a user with full privileges. Let's check our access.
1. Open the [button label="Elasticsearch"](tab-0) tab
2. Open a log record and click on the `Table` tab in the flyout
3. Note access to the `client.ip` and `body.text` fields

In the Elasticsearch (Limited) tab, we are logged in as a user with limited privileges. Let's check our access.

1. Open the [button label="Elasticsearch (Limited)"](tab-1) tab
2. Open a log record and click on the `Table` tab in the flyout
3. Note that `client.ip` and `body.text` fields don't exist

Let's change permissions and see what happens:

1. Open the [button label="Elasticsearch"](tab-0) tab
2. Go to `Management` > `Stack Management` > `Security` > `Roles` using the left-hand navigation pane
3. Select `limited_viewer`
4. For Indices `logs-proxy.otel-default`, update `Denied fields` to remove `body.text` (it should only contain `client.ip`)
5. Click `Update role`

Now let's ensure our limited user has access to `body.text`.

1. Open the [button label="Elasticsearch (Limited)"](tab-1) Instruqt tab
2. Close the open log record flyout
3. Run the search query again
4. Open a log record
5. Note that `client.ip` doesn't exist, but `body.text` now does!

# Limiting retention

Say your records department requires you to keep these logs generally accessible only for a very specific period of time. We can ask Elasticsearch to automatically delete them after some number of days.

1. Open the [button label="Elasticsearch"](tab-0) Instruqt tab
2. Go to `Streams` using the left-hand navigation pane
3. Select `logs-proxy.otel-default` from the list of Streams
4. Click on the `Data retention` tab
5. Click `Edit data retention`
6. Select `Set specific retention days`
7. Set to `30` days

Elasticsearch will now remove this data from its online indices after 30 days. At that time, it will only be available in backups.

# Summary

Let's take stock of what we know:

* a small percentage of requests are experiencing 500 errors
* the errors started occurring around 80 minutes ago
* the only error type seen is 500
* the errors occur over all APIs
* the errors occur only in the `TH` region
* the errors occur only with browsers based on Chrome v136

And what we've done:

* Created a dashboard to monitor our ingress proxy
* Created graphs to monitor status codes over time
* Created a simple alert to let us know if we ever return non-200 error codes
* Parsed the logs at ingest-time for quicker and more powerful analysis
* Create a SLO (with alert) to let us know if we ever return a significant number of non-200 error codes over time
* Created visualizations to help us visually locate clients and errors
* Created graphs in our dashboard showing the breakdown of User Agents
* Created a table in our dashboard iterating seen User Agents
* Created a nightly report to snapshot our dashboard
* Created an alert to let us know when a new User Agent string appears
* Setup RBAC to restrict access to `client.ip`
* Setup retention to keep the logs online for only 30 days

# Wrap-Up

Over the course of this lab, we learned about:

* Using ES|QL to search logs
* Using ES|QL to parse logs at query-time
* Using ES|QL to do advanced aggregations, analytics, and visualizations
* Creating a dashboard
* Using ES|QL to create Alerts
* Using AI Assistant to help write ES|QL queries
* Using Streams to setup ingest-time log processing pipeline (GROK parsing, geo-location, User Agent parsing)
* Setting up SLOs
* Using Maps to visualize geographic information
* Scheduling dashboard reports
* Setting up a Pivot Transform and Alert
* Setting up RBAC
* Setting up data retention

We put these technologies to use in a practical workflow which quickly took us from an unknown problem to a definitive Root Cause. Furthermore, we've setup alerts to ensure we aren't caught off-guard in the future. Finally, we built a really nice custom dashboard to help us monitor the health of our Ingress Proxy.

**All of this from just a lowly nginx access file. That's the power of your logs unlocked by Elastic.**


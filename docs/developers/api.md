# Developer API (Static)

These endpoints are **static JSON** pre-generated at build time — perfect for lightweight integrations without a server.

- `api/index.json` — list of available shards
- `api/euro_atfm_timeseries_last24.json` — last 24 months ATFM timeseries
- `api/airport_degree_top100.json` — top-100 airports by `deg_total`

Example (fetch in JS):

```js
fetch('/aviation-portfolio-pack/api/euro_atfm_timeseries_last24.json')
  .then(r=>r.json())
  .then(rows => console.log(rows[0]));
```

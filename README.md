# The Agency Costa Rica — JamesEdition ELITE Feed

This repository independently generates and hosts The Agency Costa Rica’s curated JamesEdition XML feed. It does not share runtime state, selection rules, credentials, webhooks, or workflows with the Encuentra24 feed.

## Delivery URL

GitHub publishes the XML from a dedicated live-output branch at:

```text
https://raw.githubusercontent.com/armla/jedition-feed/jamesedition-live/public/feeds/<random-token>.xml
```

The current token is held in `.state/feed_token.txt`. It is an **unlinked obscurity control**, not a credential: GitHub raw content is public by design. Provide the complete URL only to JamesEdition and authorized internal operators.

## Nightly schedule

The generator runs automatically at **10:58 PM Costa Rica time**, which is **04:58 UTC** the following calendar day. GitHub’s scheduled workflow service can occasionally start a few minutes late; the job is configured so overlapping runs never publish concurrently. Operators may also use **Run workflow** in GitHub Actions for a manual update.

## Publication rules

The generator uses the following confirmed JamesEdition policy:

- up to **50 active Costa Rica sale listings**;
- a conservative **USD 500,000** minimum price;
- residential, land, farm/ranch, and estate inventory only; ambiguous commercial, hotel, restaurant, and store stock is excluded;
- **exclusive listings exhaust the allocation first**, then non-exclusive listings are selected by source priority;
- only `isonportalfeed=true` images are eligible, sorted by `sortonportalfeed`, with a hard **12-image maximum**;
- the primary horizontal video is emitted before supplementary source video fields;
- MLS ID remains the durable JamesEdition listing reference;
- addresses are hidden (`<hide_address>yes</hide_address>`), while verified map coordinates remain in the XML.

## Data sources and safeguards

The generator reads the canonical Agency inventory API, the Agency’s public MLS-coordinate map, and the English property description rendered by each branded listing page. It validates 50 unique MLS references, required fields, two or more images, maximum image count, price and currency, description, agent reference, and valid coordinate ranges before replacing the published XML.

A failed source call, incomplete enrichment, or failed XML validation exits without replacing the current file. The last successfully validated feed therefore remains available to JamesEdition.

## Security posture

No normal page links to the tokenized XML. The dedicated `jamesedition-live` branch is the only branch the scheduled workflow can update. **GitHub raw delivery cannot set `X-Robots-Tag` headers or rely on a repository-level `robots.txt` for an individual feed file.** The token therefore reduces accidental discovery only; it does not make the public file private or stop deliberate scraping. See [SECURITY.md](SECURITY.md) before sharing the URL or adding integrations.

## Operator actions

1. Confirm GitHub Pages is set to **GitHub Actions** under **Settings → Pages**.
2. After the first successful run, copy the tokenized Pages URL from `.state/feed_token.txt` and provide it to JamesEdition.
3. Use the **Run workflow** control to refresh on demand. Use its `rotate_feed_token` option only when the URL has been disclosed or should be retired; then update JamesEdition with the new URL.
4. Review failed workflow logs promptly. A safe failure preserves the previous XML but may leave availability, price, or inventory changes pending until the next success.
5. Do not add passwords, API tokens, CRM credentials, or Zapier URLs to tracked files. Store any future webhook URL only in GitHub Actions Secrets.

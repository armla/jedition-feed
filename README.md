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

## Salesforce marketing activities

The workflow supports one **External Website - James Edition** publication activity for each listing when it first enters the JamesEdition feed. It does not create a new activity for a price, copy, photo, or routine daily-feed update.

To activate it, create a **dedicated** Zapier Catch Hook for JamesEdition, map the hook to Salesforce using `listing_id` as the property key, and deduplicate using `publication_key` (`JamesEdition:<MLS ID>`). Add the private Catch Hook URL as the GitHub Actions repository secret named `JAMESEDITION_PUBLISH_WEBHOOK_URL`. Do not reuse the Encuentra24 hook or add the URL to a tracked file.

The initial activation intentionally backfills the current valid JamesEdition roster once, so each listing already published before this automation receives its missing activity. The durable live-branch state then prevents daily duplicates. If delivery fails, the listing remains in the non-sensitive retry queue and is retried on the next successful feed run; a delivery failure never invalidates the XML feed.

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

1. Provide the current tokenized raw-GitHub URL from `.state/feed_token.txt` to JamesEdition.
2. Configure the dedicated `JAMESEDITION_PUBLISH_WEBHOOK_URL` secret before activating Salesforce publication activities.
3. Use the **Run workflow** control to refresh on demand. Review workflow logs promptly; a safe failure preserves the previous XML but may leave availability, price, or inventory changes pending until the next success.
4. Do not add passwords, API tokens, CRM credentials, or Zapier URLs to tracked files. Store the activity URL only in GitHub Actions Secrets.

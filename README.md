# The Agency Costa Rica — JamesEdition Feeds

This repository independently generates and hosts The Agency Costa Rica’s segregated JamesEdition XML feeds. It does not share runtime state, selection rules, credentials, webhooks, or workflows with the Encuentra24 feed.

## Delivery URL

GitHub publishes the XML from a dedicated live-output branch at:

```text
https://raw.githubusercontent.com/armla/jedition-feed/jamesedition-live/public/feeds/<random-token>.xml
```

The ELITE token is held in `.state/feed_token.txt`; the portal token is held separately in `.state/portal_feed_token.txt`. Each is an **unlinked obscurity control**, not a credential: GitHub raw content is public by design. Provide the complete URL only to JamesEdition and authorized internal operators.

## Segregated rosters

| Feed | Capacity | Selection and exclusion rule | Live-output branch | Activity channel |
| --- | ---: | --- | --- | --- |
| **ELITE** | 50 | Exclusive-first, then curated non-exclusive records. | `jamesedition-live` | `JAMESEDITION_PUBLISH_WEBHOOK_URL` |
| **Portal** | 100 | The next validated records after **every current ELITE MLS reference is excluded**. It cannot publish any record presently in the ELITE feed. | `jamesedition-portal-live` | `JAMESEDITION_PUBLISH_WEBHOOK_URL_PORTAL` |

The portal workflow rebuilds the exclusion roster directly from the last validated ELITE XML on every run. It validates exactly 100 unique records, then fails safely rather than publishing when even one ELITE reference would overlap or the full validated portal capacity cannot be met.

## Nightly schedule

Both generators run automatically at **10:58 PM Costa Rica time**, which is **04:58 UTC** the following calendar day. GitHub’s scheduled workflow service can occasionally start a few minutes late; each job is independently configured so overlapping runs never publish concurrently. Operators may also use **Run workflow** in GitHub Actions for a manual update.

## Salesforce marketing activities

Each workflow supports one **External Website - James Edition** publication activity for each listing when it first enters its respective JamesEdition feed. It does not create a new activity for a price, copy, photo, or routine daily-feed update. The existing ELITE workflow remains scheduled with activity delivery **off** until explicitly activated; the separate portal workflow is scheduled in **live** mode and will backfill its first validated 100-record roster once, then send only newly entering portal records.

To activate it, create a **dedicated** Zapier Catch Hook for each channel, map the hook to Salesforce using `listing_id` as the property key, and deduplicate using `publication_key`. ELITE keys retain the established `JamesEdition:<MLS ID>` format; portal keys use `JamesEdition:PORTAL:<MLS ID>`. Add the private Catch Hook URLs as the GitHub Actions repository secrets named `JAMESEDITION_PUBLISH_WEBHOOK_URL` and `JAMESEDITION_PUBLISH_WEBHOOK_URL_PORTAL`, respectively. Do not reuse the Encuentra24 hook or add either URL to a tracked file.

For a controlled proof, use **Run workflow** with `activity_mode = test` and one current `activity_test_reference`; this sends exactly one real, production-shaped event and does not alter activity state or trigger a backfill. After Salesforce confirms the activity, run with `activity_mode = live` to backfill the current valid JamesEdition roster once. The durable live-branch state then prevents daily duplicates. If delivery fails in live mode, the listing remains in the non-sensitive retry queue and is retried on the next successful feed run; a delivery failure never invalidates the XML feed.

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

1. Provide the current tokenized raw-GitHub URL from the relevant feed-token file to JamesEdition.
2. Configure the separate dedicated webhook secrets before activating Salesforce publication activities.
3. Use the matching **Run workflow** control to refresh on demand. Choose `test` only for a single validated MLS ID and `live` only after confirming the relevant Salesforce test activity. The ELITE scheduled workflow remains off until activated; the portal scheduled workflow is live by design. Review workflow logs promptly; a safe failure preserves the previous XML but may leave availability, price, or inventory changes pending until the next success.
4. Do not add passwords, API tokens, CRM credentials, or Zapier URLs to tracked files. Store the activity URL only in GitHub Actions Secrets.

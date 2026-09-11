# JamesEdition Salesforce Marketing Activity Activation

**Status:** The ELITE and portal feeds have separate activity-delivery channels. The portal implementation uses its own Zapier Catch Hook and must never share an activity state or deduplication key with ELITE.

## Intended Behavior

The workflow sends one outbound event when a listing first enters the JamesEdition feed. The target Salesforce activity must be named **External Website - James Edition**. The workflow does not send an event for a daily refresh, price change, description update, media change, or an already-published listing.

The first successful run after activation deliberately backfills the current feed roster once. This remedies the missing activities for listings that entered JamesEdition before this automation was added. Future runs send only listing IDs that newly enter the feed.

## Zapier and Salesforce Configuration

Create a new **Webhooks by Zapier — Catch Hook** specifically for JamesEdition. Do not reuse the Encuentra24 publication hook. Map the incoming event to the related Salesforce property/listing using `listing_id` as the MLS ID. Create the marketing/publication activity with the name **External Website - James Edition**.

Use `publication_key` as the idempotency key. For ELITE, the value remains `JamesEdition:<MLS ID>`; for the standard portal feed, it is `JamesEdition:PORTAL:<MLS ID>`. The Zap must search for an existing activity with that key before creating one, or use a Salesforce external-ID/upsert field where available. This protects against duplicate activities if Zapier or GitHub retries an HTTP request and keeps the two publication channels independently auditable.

| Incoming field | Required Salesforce / Zapier handling |
|---|---|
| `activity_name` | Set the activity/publication label to **External Website - James Edition**. |
| `listing_id` | Match the related property/listing by Agency MLS ID. |
| `publication_key` | Deduplicate or upsert key. |
| `portal` | Set source/website to `JamesEdition`. |
| `feed_tier` | Preserve `ELITE` or `PORTAL` so the activity can be reported by commercial plan. |
| `date` | Activity date in Costa Rica time. |
| `url` | Branded Agency property URL. |
| `portal_feed_url` | JamesEdition XML source URL. |
| `name`, `price_usd`, `currency`, `property_type`, `property_subtype` | Snapshot fields for the activity record. |
| `city`, `state`, `region`, `latitude`, `longitude` | Location context; retain only fields permitted by the Salesforce data policy. |

## Controlled One-Listing Test

Before activating the backlog, use **Actions → Generate and publish JamesEdition feed → Run workflow** with the following values:

```text
activity_mode:           test
activity_test_reference: LXPR13860
```

This sends exactly one production-shaped event for the selected active, exclusive listing. It contains `is_test: true` for operational visibility, preserves the normal `publication_key` (`JamesEdition:LXPR13860`) for real deduplication, and does **not** write activity state. It cannot enqueue or backfill the other 49 current listings.

Confirm that Salesforce creates one activity named **External Website - James Edition** on the property matched by `listing_id`. Once confirmed, repeat **Run workflow** with `activity_mode: live`. The initial live run will backfill every current listing not already represented by its `publication_key`; Salesforce should ignore the tested listing because its production deduplication key already exists.

## GitHub Activation

In the GitHub repository **Settings → Secrets and variables → Actions**, create a new repository secret:

```text
Name:  JAMESEDITION_PUBLISH_WEBHOOK_URL
Value: <the dedicated Zapier Catch Hook URL>
```

Do not paste the URL into a GitHub issue, repository file, commit, or chat. Scheduled runs continue with activity delivery off by default. Use the controlled test above before an explicit `live` activation. The workflow always generates and validates the XML before posting activity events. A failure to post an activity in live mode does not invalidate the XML; unsuccessful events are retained in the non-sensitive live-branch retry queue and are retried on the next successful live run.

### Portal feed

The 100-listing non-ELITE portal feed uses the already configured secret below. Its scheduled workflow runs in `live` mode: the first successful publication sends one activity for each of its validated current records, then later runs send only listings newly entering that feed.

```text
Name:  JAMESEDITION_PUBLISH_WEBHOOK_URL_PORTAL
Value: <the dedicated JamesEdition portal Catch Hook URL>
```

Map it using the same Salesforce activity label, **External Website - James Edition**, while retaining `feed_tier: PORTAL` and deduplicating with `JamesEdition:PORTAL:<MLS ID>`. This is a distinct channel from ELITE and must not use its secret, state file, or keys.

## Verification Standard

After the activation run, confirm that Salesforce contains one activity for each current JamesEdition listing, with `publication_key` in the form `JamesEdition:<MLS ID>`. A second manual workflow run should create **zero** additional activities unless a listing has newly entered the feed.

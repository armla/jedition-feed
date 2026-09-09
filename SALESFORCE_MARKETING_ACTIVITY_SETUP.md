# JamesEdition Salesforce Marketing Activity Activation

**Status:** The JamesEdition feed now contains the activity-delivery logic, but it is **not yet activated** because no dedicated Zapier Catch Hook has been configured as a GitHub Actions secret. No Salesforce activities have been sent by this implementation so far.

## Intended Behavior

The workflow sends one outbound event when a listing first enters the JamesEdition feed. The target Salesforce activity must be named **External Website - James Edition**. The workflow does not send an event for a daily refresh, price change, description update, media change, or an already-published listing.

The first successful run after activation deliberately backfills the current feed roster once. This remedies the missing activities for listings that entered JamesEdition before this automation was added. Future runs send only listing IDs that newly enter the feed.

## Zapier and Salesforce Configuration

Create a new **Webhooks by Zapier — Catch Hook** specifically for JamesEdition. Do not reuse the Encuentra24 publication hook. Map the incoming event to the related Salesforce property/listing using `listing_id` as the MLS ID. Create the marketing/publication activity with the name **External Website - James Edition**.

Use `publication_key` as the idempotency key. Its value is always `JamesEdition:<MLS ID>`. The Zap must search for an existing activity with that key before creating one, or use a Salesforce external-ID/upsert field where available. This protects against duplicate activities if Zapier or GitHub retries an HTTP request.

| Incoming field | Required Salesforce / Zapier handling |
|---|---|
| `activity_name` | Set the activity/publication label to **External Website - James Edition**. |
| `listing_id` | Match the related property/listing by Agency MLS ID. |
| `publication_key` | Deduplicate or upsert key. |
| `portal` | Set source/website to `JamesEdition`. |
| `date` | Activity date in Costa Rica time. |
| `url` | Branded Agency property URL. |
| `portal_feed_url` | JamesEdition XML source URL. |
| `name`, `price_usd`, `currency`, `property_type`, `property_subtype` | Snapshot fields for the activity record. |
| `city`, `state`, `region`, `latitude`, `longitude` | Location context; retain only fields permitted by the Salesforce data policy. |

## GitHub Activation

In the GitHub repository **Settings → Secrets and variables → Actions**, create a new repository secret:

```text
Name:  JAMESEDITION_PUBLISH_WEBHOOK_URL
Value: <the dedicated Zapier Catch Hook URL>
```

Do not paste the URL into a GitHub issue, repository file, commit, or chat. After saving the secret, open **Actions → Generate and publish JamesEdition feed → Run workflow**. The workflow will generate and validate the XML before posting activity events. A failure to post an activity does not invalidate the XML; unsuccessful events are retained in the non-sensitive live-branch retry queue and are retried on the next successful feed run.

## Verification Standard

After the activation run, confirm that Salesforce contains one activity for each current JamesEdition listing, with `publication_key` in the form `JamesEdition:<MLS ID>`. A second manual workflow run should create **zero** additional activities unless a listing has newly entered the feed.

# JamesEdition Feed Operations Tracker

## Completed

- [x] Create an isolated public repository for the JamesEdition feed.
- [x] Generate and validate a 50-listing XML 3.9 feed with an exclusive-first allocation.
- [x] Restrict feed images to the first 12 `isonportalfeed` items ordered by `sortonportalfeed`.
- [x] Enforce JamesEdition's one-video limit: retain the primary horizontal walkthrough and use a vertical clip only as fallback.
- [x] Audit all emitted images and replace the low-resolution `1277x640` display renditions with reachable canonical Propertybase/S3 original-object URLs.
- [x] Add compliant virtual-tour-link support for JamesEdition-approved immersive-tour providers; source virtual-tour fields currently contain YouTube URLs only and therefore emit no invalid virtual-tour links.
- [x] Add safe JamesEdition `<floors>` mapping for the Salesforce `Stories__c` property field and normalized source aliases.
- [x] Populate verified English descriptions and authoritative coordinates.
- [x] Add a safe-failure generator design that retains the last known-good feed.
- [x] Prepare a nightly workflow for 10:58 PM Costa Rica time (04:58 UTC).
- [x] Add ownership policy, pinned action revisions, and monthly GitHub Actions dependency review.
- [x] Apply main-branch protections: pull-request review, code-owner review, stale-review dismissal, linear history, no force pushes, no deletions, and conversation resolution.
- [x] Define a separate 100-listing JamesEdition portal roster that excludes the current 50-record ELITE roster on every generation run.

## Operating Decisions Pending

- [x] Deploy the nightly GitHub Actions publisher to the dedicated `jamesedition-live` branch.
- [x] Confirm a complete production update and public crawler retrieval from the tokenized raw GitHub URL.
- [x] Implement idempotent first-publication activity delivery for **External Website - James Edition**.
- [ ] Confirm whether the four exclusive listings with a commercial source classification should be eligible for JamesEdition; they are excluded under the current conservative policy.
- [ ] Establish an approved coordinate precision policy for high-profile or owner-occupied residences.
- [ ] Add the dedicated `JAMESEDITION_PUBLISH_WEBHOOK_URL` secret and activate the JamesEdition Zapier-to-Salesforce mapping; this will backfill the current feed roster once.
- [ ] Expose `Stories__c` as `stories` (or `Stories__c`) in the public Agency listing API; the current bulk and detail payloads omit the field, so no live `<floors>` values can yet be published.
- [x] Publish and validate the 100-record portal feed on `jamesedition-portal-live`, using `JAMESEDITION_PUBLISH_WEBHOOK_URL_PORTAL` for its separate Salesforce activity channel. The initial validated roster created 100 distinct portal activities; its reconciled state prevents replay, and later runs are incremental.

## Maintenance

- [ ] Review the 50-listing selection, prices, availability, agent contact data, location precision, and media quality monthly; replace any sub-1024×641 original images in the source CMS before the next refresh.
- [ ] Review repository collaborators and GitHub Actions workflow changes quarterly.
- [ ] Rotate the random delivery URL and inform JamesEdition if the URL is disclosed or materially abused.

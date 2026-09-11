# Portal Feed Security & Privacy Assessment

**Applies to:** `armla/jedition-feed` (JamesEdition) and `armla/encuentra24-feed` (Encuentra24)  
**Status:** Both repositories are public as of 7 September 2026.  
**Purpose:** Distinguish realistic exposure from hypothetical “hacking,” document controls, and set operator priorities.

## Executive Assessment

A public XML property feed should be treated as **publicly readable data**. A random file path reduces accidental discovery but does not provide authentication or confidentiality. GitHub raw delivery does not provide custom `X-Robots-Tag` headers, and a repository `robots.txt` does not control indexing of an individual `raw.githubusercontent.com` file. Anyone who obtains the URL, reads the public repository history, or observes JamesEdition’s request can download it. This is usually acceptable for data intended for a marketplace, but it becomes a material risk if the feed contains precise private addresses, unapproved owner/contact data, internal listing notes, source API credentials, webhook URLs, or commercially sensitive inventory selection logic.

The principal threat is not an attacker “hacking” the XML itself. It is **unintended disclosure** through a public repository, a publicly accessible feed URL, overly broad source fields, insecure workflow permissions, or exposed third-party secrets. The correct strategy is therefore field minimization, secret isolation, repository governance, workflow hardening, and a tested recovery process.

## Risk Register

| Risk | JamesEdition exposure | Encuentra24 exposure | Impact | Required control |
|---|---|---|---|---|
| **Public XML download** | The GitHub Pages file is anonymously retrievable. The randomized path is not a security boundary. | A public raw feed URL has the same characteristic. | Listing facts, photos, pricing, and agent data can be copied. | Publish only marketplace-approved fields; never consider the feed confidential. |
| **Precise seller location exposure** | Coordinates can reveal a property more precisely than `hide_address=yes` suggests. | Same risk if latitude/longitude or address are transmitted. | Seller safety, privacy, and unauthorized site visits. | Use the Agency-approved coordinate point; do not include unit number, exact street, owner identity, gate codes, or internal map notes. Audit high-sensitivity listings individually. |
| **Repository and commit-history disclosure** | Public repository exposes generator logic, XML output, state and all historic committed feed data. | Same. | Removed listings, prior prices, and historic contact data can remain discoverable in commit history. | Keep snapshots, exports, logs, raw API responses, and diagnostic dumps out of Git. Use a repository rewrite process if sensitive data is ever committed. |
| **Secret leakage** | An Actions secret, webhook URL, API key, or CRM credential committed to code becomes public and should be rotated immediately. | Same. | Unauthorized CRM actions, API use, spam, data alteration, or vendor-account compromise. | Use GitHub Actions Secrets only. Enable secret scanning and push protection. Never echo secrets in logs. |
| **Malicious workflow modification** | A person with repository write access can alter the generator or workflow to publish incorrect data or exfiltrate repository secrets. | Same. | Feed defacement, listing suppression, misleading prices, credential compromise. | Restrict write/admin access, protect the default branch, require pull-request review, and review workflow changes separately. |
| **Third-party Action supply-chain risk** | Unpinned Actions can change upstream. The repository currently uses maintained official GitHub Actions by major version. | Same. | Arbitrary workflow behavior under the repository’s permissions. | Pin Actions to immutable commit SHAs for the strongest posture; enable GitHub’s requirement for SHA-pinned actions when operationally ready. |
| **Untrusted pull-request code executing with secrets** | `pull_request_target`, self-hosted runners, or exposing secrets to PR code can result in secret exfiltration. This workflow does neither. | Same. | Secret theft. | Keep the job on `schedule` and `workflow_dispatch`; do not run privileged deployment jobs from forks or unreviewed pull requests. |
| **Source API / feed tampering** | The generator trusts external API responses and public property-page content. | Same. | Incorrect listings, descriptions, maps, prices, or removed feed entries. | HTTPS, deterministic validation, stable MLS IDs, last-known-good output, operator review of material inventory changes, and upstream API access controls. |
| **Feed URL shared or indexed despite controls** | `robots.txt` is voluntary and no-index directives are not an access control. | Same. | Mass scraping and competitive intelligence. | Use a long random path, do not link publicly, share only with portal operators, rotate path upon disclosure, and consider a dedicated authenticated host if true confidentiality is required. |
| **Lead/webhook endpoint abuse** | Any future inbound lead or Salesforce/Zapier webhook is internet-facing. | Same. | Spam, forged leads, duplicate activities, CRM contamination. | Unique endpoint per portal, signed verification or an unguessable secret, strict schema validation, rate limits, deduplication, and raw-payload audit storage without sensitive secrets. |

## Controls Implemented in This Repository

The current JamesEdition design provides these practical safeguards:

1. Each feed has a random tokenized path and no ordinary site navigation points to it.
2. The protected `main` branch contains source code and cannot be modified by scheduled jobs; ELITE and portal jobs write only to their separate `jamesedition-live` and `jamesedition-portal-live` output branches.
3. Every listing carries `<hide_address>yes</hide_address>`.
4. The XML is only replaced after required-field, ID uniqueness, location, price, image-count, and parsing checks pass.
5. An upstream source failure preserves the last verified public XML rather than publishing an empty or partial set.
6. The generator excludes raw inventory snapshots, logs, local diagnostics, and credentials from tracked source files.
7. The feed uses a durable MLS reference so price and content changes reconcile as updates rather than creating duplicate portal listings.
8. The first-publication activity implementation uses separate ELITE and portal secrets, tier-specific `publication_key` values, and separate committed retry queues on their live-output branches. It cannot create a daily duplicate after a successful activity record.
9. The portal feed extracts the active ELITE MLS roster from the validated ELITE XML on every run and refuses publication if any of its 100 records overlap.

## Controls Still Required

| Priority | Action | Reason |
|---:|---|---|
| **1** | Protect `main`: require pull requests and at least one approving review for workflows and feed-generation code. | A public repository is not a reason to permit unaudited production changes. |
| **1** | Restrict repository write and admin access to the smallest necessary group; review collaborator access quarterly. | Write access is the main pathway to feed manipulation and secret exposure. |
| **1** | Enable GitHub secret scanning, push protection, Dependabot alerts, and repository vulnerability alerts. | Prevents common credential and dependency exposures before deployment. |
| **2** | Review the exact coordinate policy for high-profile residences, owner-occupied properties, and unbuilt land. | Exact coordinates can undermine address obfuscation even when the street address is hidden. |
| **2** | Add dedicated ELITE and portal JamesEdition Catch Hooks and configure Salesforce to deduplicate by tier-specific `publication_key`. | Keeps ELITE, portal, and Encuentra24 delivery endpoints and activity histories isolated. |
| **2** | Pin GitHub Actions to immutable commit SHAs and restrict Actions to GitHub-verified or explicitly approved publishers. | Reduces software supply-chain risk. |
| **3** | Maintain an incident runbook: rotate the feed path, regenerate the feed, revoke/rotate leaked secret, then request portal URL update. | Makes a URL or credential disclosure recoverable quickly. |
| **3** | Set a monthly review of repository history and public feed fields. | Ensures former inventory, stale contacts, or source changes do not leave inappropriate data public. |

## If a Leak or Unauthorized Change Occurs

1. **Stop propagation.** Disable the affected GitHub Actions workflow, revoke or rotate the exposed secret in its external system, and revoke the GitHub credential of any compromised account.
2. **Assess exposure.** Identify whether the incident involves only public listing data, precise location data, a source API token, a CRM/Zapier webhook, or an account credential.
3. **Repair the feed.** Roll back to the last known-good commit, correct the source, regenerate the file, and rotate the tokenized path if it was disclosed or abused.
4. **Purge sensitive Git history when necessary.** Removing a file in a new commit does not remove it from historic public commits. Use a repository-history rewrite and GitHub support guidance if credentials or protected personal data were committed.
5. **Notify only where necessary.** Inform affected sellers, platform contacts, or vendors where exact addresses, personal details, or credentials may have been exposed.
6. **Document the corrective action.** Record the incident, affected scope, rotations performed, and the new preventive control.

## Bottom Line

The two public feeds do not inherently provide an attacker with access to the underlying CRM, hosting, or seller data. They **do publish whatever fields are placed in the XML and whatever material is committed to public Git history**. Treat source credentials, webhook URLs, internal notes, raw exports, and exact personal location information as prohibited content. Treat the feed’s listing data as intentionally public, even when it is hidden behind a random URL.

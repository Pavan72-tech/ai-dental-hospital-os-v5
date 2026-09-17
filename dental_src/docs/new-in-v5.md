# What's new in this update (v5 add-on layer)

This update adds a new AI + CRM layer on top of the existing Enterprise v4
build without breaking any existing module. Nothing existing was removed —
`imaging.py` was upgraded from a health-check skeleton to a full module;
everything else is additive (`ai_plus.py`, `crm_plus.py`, new frontend pages,
new DB tables).

## 1. Imaging & MRI AI (`/imaging/*`)
See `ai/imaging-ai.md`. Adds full upload + AI screening for X-ray, OPG, CBCT
**and MRI** (TMJ disc position, joint effusion, sinus/soft-tissue flags),
with clinician review workflow.

## 2. AI+ Advanced Suite (`/ai-plus/*`)
- **No-show prediction** — scores a booked appointment's no-show risk from history, lead time, channel.
- **Treatment recommender** — turns a findings list into a draft, prioritized treatment sequence.
- **Sentiment analysis** — scores patient messages/reviews and flags ones needing escalation.
- **Smart scheduling optimizer** — ranks candidate appointment slots to reduce chair-time gaps.
- **Insurance claim assistant** — checks a claim for missing documents before submission.
- **Virtual receptionist** — intent-detecting auto-reply for WhatsApp/website enquiries, hands off emergencies to staff.
- **Perio risk score** — periodontal risk + suggested recall interval from exam inputs.
- **Cross-sell suggestions** — ethical, need-based add-on care suggestions for the front desk.

## 3. CRM Growth Suite (`/crm-plus/*`)
- **Loyalty & tiers** — points ledger, Bronze→Silver→Gold→Platinum tiers, earn/redeem endpoints.
- **Referral program** — log a referral, auto-reward the referrer's loyalty points on conversion.
- **Reputation management** — capture reviews, auto-flag ratings ≤3 for response, request reviews only after a good visit.
- **Campaign automation** — draft → segment (all active / overdue recall / high value) → launch WhatsApp/SMS/Email campaigns.
- **NPS tracking** — promoter/passive/detractor scoring and NPS summary for admins.

## New database tables
`imaging_studies`, `ai_audit_logs`, `loyalty_accounts`, `loyalty_transactions`,
`referrals`, `reviews`, `campaigns`, `campaign_messages`, `nps_surveys` — all
created automatically on backend startup (see `DDL` in `app/main.py`), no
manual migration step needed for a fresh demo database.

## Frontend
New sidebar items: **Dental Imaging** (now a real MRI/X-ray AI workspace
instead of a placeholder), **Growth & Loyalty**, **Reviews & Reputation**,
**Campaigns**, **AI+ Advanced Suite** — all implemented in
`frontend/js/enterprise.js` following the existing vanilla-JS SPA pattern
(no new frontend framework/build step introduced).

## Suggested next round of features (not yet implemented)
- Real DICOM parsing + a proper CBCT/MRI slice viewer.
- A trained caries-detection CNN behind `provider_vision_analysis()`.
- Two-way WhatsApp Business API webhook (currently `virtual-receptionist` is a draft-reply endpoint, not a live webhook).
- Patient-facing mobile app / portal for loyalty balance and appointment self-service.

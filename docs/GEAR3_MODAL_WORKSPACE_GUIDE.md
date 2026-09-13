# Modal workspace guide for Gear 3 Round 1

Checked against Modal's official documentation on September 13, 2026. This is
an account-navigation guide, not a launch command. Local Stage 10 work uses a separate queue. Cloud execution requires validated
transport, a current workspace billing record and the discarded device pilot.

## 1. Open the correct workspace

1. Open [Modal Home](https://modal.com/home) and sign in using your existing account.
2. Use the workspace selector at the top of the dashboard. Select the workspace
   intended for this study and copy its exact name.
3. Keep that workspace selected while checking billing. Browser selection and
   the local command-line profile are separate; the runner must verify that its
   authenticated workspace matches the account you inspected.

Modal organizes apps and resources by workspace; a token belongs to a workspace.
You already have working local credentials, so this task does not require a new
API token or a new workspace. [Official workspace guide](https://modal.com/docs/guide/workspaces).

## 2. Find the billing controls

Open **Settings**, then **Usage & Billing**. The direct shortcut is
[Usage & Billing](https://modal.com/settings/usage); sign in if redirected, then
check the selected workspace again. Read and copy the following values:

| Item to record | What to copy |
|---|---|
| Billing cycle | Its start and end dates, including the displayed timezone if any |
| Usage so far | The current cycle's total usage before credits |
| Usage limit / workspace budget | The current gross usage ceiling, or explicitly say no limit |
| Spend limit | The custom or default net charge limit shown |
| Remaining credits | Current available credits and any displayed expiration |
| Payment readiness | Whether a usable payment method is on file; no card details |

The **usage limit** caps monthly usage before credits. The **spend limit** caps
out-of-pocket charges after credits. They are separate: reaching the latter may
still permit credit-covered work. Only workspace Owners and Managers can edit
these controls. Environment budgets require Team/Enterprise and cover compute,
so they do not replace the workspace limit for storage and other charges.
[Official budget definitions and controls](https://modal.com/docs/guide/budgets).

For this campaign, the intended additional allowance is at most $50 gross, with
$40 ordinary work and $10 reserved for bounded recovery. Do not interpret $50 as
$50 of charges plus free-credit work. Existing usage matters: if the cycle already
contains $12 of unrelated usage, a $50 monthly usage limit leaves $38, not $50.
We will reconcile your displayed numbers with the campaign ledger before any
paid run. If the current setting is larger or unclear, send its value first.
Do not lower a shared workspace's limit blindly; it could stop another project.

## 3. Check whether anything else shares the allowance

Return to Home and inspect the workspace's app list and stored resources. Note
any running apps, deployed services, schedules or retained volumes belonging to
other work. A quiet dashboard is not proof that scheduled work or storage is free.
For this study we need an explicit answer about other workloads, including work
that might start while the experiment runs. Do not delete or stop unfamiliar
resources. If uncertain, record that uncertainty for us to resolve.

The campaign's intended app and volume name is `sounding-line-g3-round1`.
At the time this guide was written, the new campaign had created neither.

## 4. Payment and receipts, if needed

On **Usage & Billing**, **Manage payment details** opens the Stripe-hosted
payment page. **View invoices** opens invoice history. Handle payment information
there, rather than pasting it into chat or a repository. Modal bills monthly and
may also charge at intermediate usage thresholds; billing records can arrive
with delay. Final campaign accounting must allow those records to settle.
[Official billing guide](https://modal.com/docs/guide/billing).

## 5. Send back this short account summary

Copy these labels and fill in their displayed values; no credentials or card
information are needed:

```text
Workspace name:
Billing cycle start/end:
Gross usage so far:
Usage limit / workspace budget:
Spend limit (custom or default):
Remaining credits / expiration:
Payment method ready (yes/no):
Other running, scheduled or stored workloads (none/list/unknown):
Time checked and timezone:
```

I will keep the account details private, verify the authenticated workspace,
check the remaining allowance, and record the launch evidence. The next paid
step is the discarded pilot, capped at $3. Its measured fit, throughput and
returned evidence determine the affordable scientific roster; preparation alone
does not admit that roster.

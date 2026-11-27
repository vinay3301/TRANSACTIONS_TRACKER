# TRANSACTIONS_TRACKER

Automated SMS-based personal finance tracker. The Android phone schedules a GitHub Actions workflow through Termux; the workflow downloads the latest SMS backup XML from Google Drive, processes transactions, updates the Google Sheet, and sends a formatted email report.

## Current automation architecture

1. **Android / Termux scheduler** runs the local dispatch script:
   `~/scripts/transaction-dispatch.sh`
2. The dispatch script triggers the `Transaction Tracker Update` GitHub Actions workflow using `workflow_dispatch`.
3. GitHub Actions downloads the latest SMS XML backup from the configured Google Drive folder.
4. `TranscationsUpdater.py` parses and deduplicates transactions, updates the appropriate monthly worksheet tabs, and calculates account balances and today's expenses.
5. The updater writes a temporary `transaction_email_report.json` report for the workflow.
6. The workflow posts the workflow result and report to the Google Apps Script web app.
7. The Apps Script notifier emails the workflow status, account balances, today's expenses, and the 10 most recent transactions.

The email notification step is configured not to fail the transaction-processing job if email delivery encounters an error.

## Repository contents

- `TranscationsUpdater.py` — transaction parsing, deduplication, Google Sheets updates, and email-report data generation.
- `.github/workflows/transaction_update.yml` — manually dispatched GitHub Actions workflow used by the Termux scheduler.
- `requirements.txt` — Python dependencies.
- `tests/test_contact_mapping.py` — SMS counterparty extraction and contact-mapping regression tests.
- `README.md` — setup and operations documentation.

## Required services and configuration

- Android with Termux and a working internet connection.
- SMS Backup & Restore (or a compatible tool) to create the SMS XML backup.
- Google Drive folder containing the latest SMS backup XML.
- Google Sheets API and Google Drive API enabled in the Google Cloud project.
- Google service account with access to the target Drive folder and Google spreadsheet.
- Google Apps Script web app deployed to accept the workflow notification.

### GitHub repository secrets

Configure these under **Repository → Settings → Secrets and variables → Actions**:

| Secret | Purpose |
|---|---|
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Service-account JSON used to access Google Drive and Google Sheets. |
| `TRANSACTION_EMAIL_WEBHOOK_URL` | Deployed Apps Script web-app URL. |
| `TRANSACTION_EMAIL_WEBHOOK_SECRET` | Shared secret used to authenticate workflow notifications. |

Never commit service-account credentials, webhook URLs, webhook secrets, access tokens, or personal financial data to the repository.

### Google Apps Script properties

The separate `TRANSACTIONS TRACKER EMAIL NOTIFIER` Apps Script project uses these Script Properties:

| Property | Purpose |
|---|---|
| `ALERT_EMAIL` | Destination email address. |
| `WEBHOOK_SECRET` | Must match the GitHub `TRANSACTION_EMAIL_WEBHOOK_SECRET`. |
| `LAST_NOTIFIED_RUN_ID` | Duplicate-notification guard. |

Set the Apps Script project timezone to `Asia/Kolkata`. Deploy the web app to execute as the script owner and allow access required by the GitHub Actions webhook.

## Termux scheduler

The transaction dispatch cron entry currently runs at minute 3 of every hour:

```cron
3 * * * * /data/data/com.termux/files/home/scripts/transaction-dispatch.sh >> /data/data/com.termux/files/home/logs/transaction-dispatch-cron.log 2>&1
```

The dispatch script is stored locally in Termux and is not part of this repository. Keep its GitHub token private. Do not add the token to this repository or to the README.

To inspect the schedule and recent dispatch output in Termux:

```sh
crontab -l
tail -n 50 ~/logs/transaction-dispatch-cron.log
```

The cron daemon must be running for scheduled dispatches to occur. Android battery restrictions and device shutdowns can interrupt Termux execution. A persistent missed-run/offline retry mechanism has not yet been implemented.

## Running and monitoring

- Open **Actions → Transaction Tracker Update** in the GitHub repository to inspect workflow runs.
- A normal run should show successful XML download, transaction updater, and email notification steps.
- The notification email includes the workflow result, run details, account balances (HDFC, BOB, CASH, and TOTAL), today's expenses, and the 10 latest transactions.
- If transaction processing fails, the email reports the failure; it should not present stale report values as fresh balances.
- The workflow is triggered by Termux using `workflow_dispatch`; do not add a GitHub cron schedule unless the scheduling design is intentionally changed.

## Important maintenance notes

- Keep the existing Termux dispatch script and cron entry intact when editing the workflow.
- Do not change the separate NEWS & CA updater or its Termux schedule while maintaining this repository.
- Preserve the existing `GOOGLE_SERVICE_ACCOUNT_JSON` secret when changing other secrets.
- The updater filename is currently spelled `TranscationsUpdater.py`; the workflow references this exact filename.
- Review GitHub Actions logs before changing code after a failed run.


## Contact mapping and parser tests

The updater extracts a counterparty from common bank SMS fields before applying CONTACT_MAP. It supports multiline and single-line To, To|Info, and Info fields, with VPA and UPI User as fallbacks when no explicit beneficiary field is present. Known merchant spellings can be added as aliases under the existing canonical name; unknown counterparties remain visible instead of being replaced with a generic label.

Run the parser and contact-mapping regression tests locally after installing requirements.txt:

```sh
python -m unittest discover -s tests -v
```

The GitHub Actions workflow runs the same tests before downloading the SMS backup or making any Google Sheets changes.

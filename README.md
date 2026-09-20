# Bakulin CRM bot — setup runbook

## 0. Use the project's isolated virtual environment

This machine installs Python packages globally by default, which is risky —
installing this project's `requirements.txt` once already downgraded
`requests` and broke an unrelated project on this machine (instagrapi needs
`requests==2.32.5`, this project pins `2.32.3`). A `.venv/` has already been
created and has all dependencies installed. Always run commands below via it:

```bash
cd bakulin-crm-bot
.venv/bin/python -m pytest -q                 # run tests
.venv/bin/python -m crm_bot.sheets_client ...  # run any CLI command
```

(If `.venv/` is ever missing, recreate it with `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`.)

## 1. Create the Telegram bot
1. Message @BotFather on Telegram, `/newbot`, follow the prompts.
2. Copy the token into `config.yaml` as `telegram_bot_token`.
3. Create the partners' Telegram group, add the bot to it.
4. Send any message in the group, then run:
   `curl "https://api.telegram.org/bot<TOKEN>/getUpdates"`
   and read the negative `chat.id` for the group — put it in `partners_group_chat_id`.
   Do the same in a DM with the bot to get `kirill_chat_id`.

## 2. Create the Google service account
1. In Google Cloud Console, create a project, enable "Google Sheets API" and
   "Google Calendar API".
2. Create a Service Account, download its JSON key as `service_account.json`
   (place it in `bakulin-crm-bot/`, it's gitignored).
3. Share the Google Sheet ("Лиды Бакулин запуск 3") with the service account's
   email address (found in the JSON key, `client_email`) — Editor access.
4. Share the Google Calendar that has the "Бакулин" call events with the same
   email — Viewer access is enough.

## 3. Fill config.yaml

```bash
cp config.example.yaml config.yaml
```

Fill in the real token, chat ids, sheet id (already the right default), and
calendar id (open Calendar settings → the calendar → "Integrate calendar" →
Calendar ID).

## 4. Migrate the live sheet schema (run once)

```bash
.venv/bin/python -m crm_bot.sheets_client ensure-schema --config config.yaml
```

This adds the new "Поточний статус / Дата останнього контакту / ... /
Історія оновлень" rows under the existing questionnaire, without touching
anything already there.

The "Звіти" (reports archive) tab does NOT need a separate migration step —
it's created automatically the first time any `append-report` /
`list-reports` / `find-report` command runs.

## 5. Smoke test

```bash
.venv/bin/python -m crm_bot.telegram_client get-updates --config config.yaml
```

(`telegram_client.py` reads the token from `config.yaml` by default, same as
the other two CLIs — pass `--token` only to override it for a one-off test.)

Send a test message to the bot from Kirill's account, run the command again,
confirm the message shows up in the JSON.

To send a message back, `--chat-id` accepts a raw numeric id or the
convenience keywords `kirill` / `partners`, which resolve to
`kirill_chat_id` / `partners_group_chat_id` from `config.yaml`:

```bash
.venv/bin/python -m crm_bot.telegram_client send --config config.yaml --chat-id kirill --text "test"
```

```bash
.venv/bin/python -m crm_bot.sheets_client list-leads --config config.yaml
```

Confirm it prints the existing leads from the sheet.

## 6. Set up the four scheduled agents

Use the `schedule` skill (or `CronCreate`) to create four routines. Each
routine's prompt tells the scheduled Claude Code agent what to do; the agent
does the reasoning and calls these CLI commands via Bash for the mechanical
parts. Every command below is run from `bakulin-crm-bot/` using
`.venv/bin/python -m crm_bot.<module> ...`.

**Routine 1 — ingest updates and on-demand report requests (every 15 minutes)**
> Run `.venv/bin/python -m crm_bot.telegram_client get-updates --config config.yaml`
> from `bakulin-crm-bot/`. For each new message, first decide what it is:
>
> - **A report request from anyone in the partners' group** (e.g. "дай отчёт
>   за прошлую неделю", "отчёт за эту неделю", or naming specific dates):
>   work out the actual date range being asked for (relative to today), then
>   run `sheets_client.py find-report --period-start ... --period-end ...`.
>   If found, send that stored text back as-is via `telegram_client.py send`
>   — don't regenerate it, the archive is the source of truth for what was
>   actually reported at the time. If not found (e.g. a week from before
>   this system existed, or an odd custom range), build it fresh the same
>   way Routine 3 does, clearly label it "restored retroactively", send it,
>   and archive it via `sheets_client.py append-report` so the next request
>   for that period is instant.
> - **A lead update from Kirill** (personal chat, free text about a client):
>   figure out which lead it's about using `sheets_client.py find-lead`,
>   decide the status/next contact date/amount from the message text. If
>   the lead match is ambiguous or a field is unclear, do NOT write
>   anything — send Kirill a question via `telegram_client.py send` instead
>   and stop for that message. If it's a brand new lead, create it with
>   `sheets_client.py create-lead`. Otherwise write the fields with
>   `sheets_client.py write-field` and add a line to the history with
>   `sheets_client.py append-history` (format: `[DD.MM] <short summary>`).
>   After handling a message, confirm back to Kirill via
>   `telegram_client.py send` with the lead's name, status, next contact
>   date, and amount.
> - **A payment screenshot link from Kirill:** write it to the
>   `payment_screenshot` field of the lead it's clearly about (ask if
>   unclear, same rule as above).
> - **Anything else from Kirill that isn't a lead update:** treat it as a
>   note for the next scheduled report (Routine 3 picks these up).

**Routine 2 — daily reminder (once a day, morning)**
> Run `sheets_client.py list-leads` then `get-lead` for each to find leads
> whose "Дата наступного контакту" is today or earlier. Send one message to
> the partners' group via `telegram_client.py send` listing them by name
> with a short reason (pull from "Історія оновлень").

**Routine 3 — weekly report (Monday and Friday)**
> Run `calendar_client.py list-events` for the relevant week and
> `sheets_client.py list-leads` + `get-lead` for current statuses. On
> Monday: report what happened last week (calls from the calendar + status
> changes) and the plan for this week (this week's calendar calls + overdue
> leads). On Friday: report what happened this week (calls + payment/no
> payment/decisions) and the plan for next week. Also fold in anything
> Kirill told the bot since the last report that wasn't a lead update. Send
> the result to the partners' group via `telegram_client.py send`, **then**
> archive it with `sheets_client.py append-report --period-start ...
> --period-end ... --generated-at ... --text ...` so it can be pulled back
> up on demand later — this is what Routine 1's on-demand handling reads
> from.

**Routine 4 — base reactivation ideas (twice a week)**
> Run `sheets_client.py list-leads` + `get-lead`, find leads stuck in
> "Ожидаем решение" or "Догрев" for more than ~2-3 weeks with no recent
> history entry. Propose 2-3 concrete next actions for them, drawing on the
> follow-up templates in `Шаблони_звітів_та_follow-up.xlsx`. Send this to
> Kirill directly (not the group) via `telegram_client.py send`.

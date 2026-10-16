"""A proposal that passes every deterministic check for a brief. Pure, so the tests and the screenshot harness share it."""

from __future__ import annotations


def good_proposal(brief, *, price_setup=None, monthly=None, weeks=None, unsafe_sentence=None, access=None):
    """A proposal that passes every deterministic check for this brief."""
    setup = price_setup if price_setup is not None else int(brief["setup_budget"] * 0.85)
    run = monthly if monthly is not None else int(brief["monthly_ceiling"] * 0.7)
    wk = weeks if weeks is not None else max(2, brief["weeks"] - 1)
    owner, other, admin = brief["owner"], brief["partners"][1], brief["admin"]
    tools = brief["tools"]
    declined = unsafe_sentence or {
        "password": "I will not give the helper the shared administrator login, because anything it did would look like a partner did it. Instead it gets its own limited account that you can switch off.",
        "autosend": "I will not let the helper send client tax figures on its own with nobody reading them first. Instead it writes drafts and a partner reads and sends each one.",
        "ssn": "I will not put Social Security numbers into the helper's prompts. Instead it matches records by client number, and the numbers stay in the accounting software.",
    }[brief["unsafe"]["id"]]
    access_lines = access or [
        f"- {tools[1]}: read the shared inbox and create drafts. It cannot send.",
        f"- {tools[2]}: read the Clients folder only. It cannot change or delete files.",
        f"- {tools[0]}: read invoices and balances. It cannot create or change anything.",
    ]
    return f"""# Proposal for {brief['firm']}

## Scope
A helper for {brief['firm']} that drafts replies to routine client email and prepares a Monday summary of open requests, for {owner} to read. {owner} decides what is in scope. It does not send anything on its own, give tax advice, or change a ledger.

## Price
Setup: ${setup:,} for the build, the tests and the handover. Running cost: ${run} per month for the provider and the computer.

## Acceptance criteria
1. The Monday summary arrives by 8 am for four weeks in a row.
2. It lists every open client request older than 7 days.
3. {other} can read a draft and approve it in under 2 minutes.

## Audit
- Where the tax documents are kept and who can open them today
- Which logins and mailboxes are shared between staff
- How client requests arrive and who answers them

## Access list
{chr(10).join(access_lines)}

## Build plan
Week 1 connect the tools with the smallest permissions. Week 2 write and test the drafts. Week 3 train the staff. {wk} weeks in all.

## Staged verification
Five runs on copies of last month's files, read by {other}. Nothing touches real client work until all five runs have been read and none contained a wrong figure.

## Approvals
- {owner} approves any email before it goes to a client
- {admin} approves any new connection to a tool
- {other} approves any change to what the helper may reach

## Declined request
{declined}

## Handover
Owner at the firm: {admin}.
1. To restart it, open Hermes and press Start.
2. If a draft looks wrong, tell {owner} and pause the job. Then call me.
3. Keys change every 90 days, and {admin} keeps the list of who owns each one.
"""

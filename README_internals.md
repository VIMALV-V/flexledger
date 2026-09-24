# B2c — Dangerous Patterns

# Bug 1 — Calling `self.save()` inside `validate()`

`validate()` is already part of the document save lifecycle. Calling `self.save()` inside `validate()` starts another save operation and can
cause recursive validation/save calls.

Instead, `validate()` should only calculate or validate the values and
allow the original save operation to continue.

# Bug 2 — Updating Package Purchase inside `validate()`

The code modifies and saves the Package Purchase inside `validate()`:

```python
pkg.credits_used += self.total_charged
pkg.save()


## B2d — Optimistic Locking

Frappe uses optimistic locking to prevent two users from silently
overwriting each others changes. If two front-desk staff members open
the same Package Purchase, both initially see the same document version.
When the first user saves the document, Frappe updates its modification
timestamp. When the second user tries to save their older copy, Frappe
detects that the document has been modified since it was opened and
raises the "Document has been modified after you have opened it" error.
This prevents the second user's stale version from silently overwriting
the first users changes.

## Group C — Schema

### C3 — Rename Integrity

When a Member record is renamed using Frappe's document rename mechanism, linked fields such as `member` in related Package Purchase
records are updated automatically.

This happens because `member` is a Link field pointing to the Member
DocType. Frappe's `rename_doc()` updates references to the renamed
document so that linked records continue to point to the correct
Member.

For example, if:

    MEM-2026-0001

is renamed to:

    MEM-2026-0005

a Package Purchase whose `member` field previously contained
`MEM-2026-0001` will be updated to `MEM-2026-0005`.

However, this behavior applies when the rename is performed through
Frappe's rename mechanism (`frappe.rename_doc()`), rather than by
directly modifying the database value with raw SQL.

## D2 — Permission Query Conditions and Safe APIs

### Class Session Permission Query Condition

The `Class Session` DocType uses `permission_query_conditions`
to restrict FIT Trainers to sessions where the linked `Trainer`
belongs to the logged-in user.

The condition looks up the `Trainer` record using its `user` field
and restricts the query using the `Class Session.trainer` field.

FIT Studio Managers are not restricted by this condition.

### Unsafe Member Method

The unsafe method uses:

```python
frappe.get_all(
    "Member",
    fields=["name", "member_name", "phone", "email"]
)


## E1 — on_update() Recursion Pitfall


Frappe calls `on_update()` as part of the document save lifecycle.

Do not call self.save() on on_update.
save() triggers on_update(), so calling self.save()
inside on_update() causes recursive execution.
This can result in recursive execution and a recursion error.

### Incorrect pattern

def on_update(self):
    self.save()

### Correct patter

def on_update(self):
    pass
Calculations should be performed in validate() not in on_update.




## E3 — One Performance Judgment Call

frappe.db.get_value() is enough because there is only one field requirement from studio settings.It avoids loading the complete document unlike frappe.db.get_doc(). Since this is used in a loop, the value is retrieved once before entering the loop rather than querying it repeatedly.


## H1 — Asynchronous `frappe.call()` Pitfall

`frappe.call()` is asynchronous. If it is called inside the client-side `validate` event without `await`, the form may save before the server returns the result. This can allow validation to finish before the package balance is checked.
In FlexLedger, we fetch the member's active package balance when a member is selected in the Attendee Entry child table. The remaining credits are displayed immediately, and a warning appears if the balance is insufficient.
Asynchronous data can also be fetched during `onload` or `refresh` so it is available before the user saves the form.
The Python `validate()` method independently checks package ownership, status, expiry date and available credits. This ensures that invalid bookings are rejected even if client-side JavaScript is bypassed.



## I1 — SQL Parameterization

The Members Running Low Query Report uses a parameterized SQL query.

#f-string interpolation:

"""
query = f"""
SELECT name, member, credits_remaining, expiry_date, status
FROM `tabPackage Purchase`
WHERE status = 'Active'
AND credits_remaining <= {threshold}
"""

 # Parameterized query:

query = """
SELECT name, member, credits_remaining, expiry_date, status
FROM `tabPackage Purchase`
WHERE status = 'Active'
AND credits_remaining <= %(threshold)s
"""

frappe.db.sql(query, {"threshold": threshold}, as_dict=True)


The f-string inserts user input directly into SQL, creating an SQL injection risk. Parameterization passes the value separately which is safe.

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

If `self.save()` is called from inside `on_update()`,  `self.save()` is executed,Frappe triggers `on_update()`,`on_update()` calls `self.save()` again , then second `save()` triggers `on_update()` again. This continues recursively.

This can result in recursive execution and a recursion error.

### Incorrect pattern

```python
def on_update(self):
    self.save()


## E3 — One Performance Judgment Call

frappe.db.get_value() is enough because there is only one field requirement from studio settings.It avoids loading the complete document unlike frappe.db.get_doc(). Since this is used in a loop, the value is retrieved once before entering the loop rather than querying it repeatedly.
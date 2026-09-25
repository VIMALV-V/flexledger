# B2c — Dangerous Patterns

# Bug 1 — Calling self.save() inside validate()

validate() is already part of the document save lifecycle. Calling self.save() inside validate()starts another save operation and can
cause recursive validation/save calls.

Instead, validate() should only calculate or validate the values and
allow the original save operation to continue.

# Bug 2 — Updating Package Purchase inside validate()

The code modifies and saves the Package Purchase inside validate():
    pkg.credits_used += self.total_charged
    pkg.save()

# B2d — Optimistic Locking

 If two front-desk staff members open
the same Package Purchase, both initially see the same document version.When the first user saves the document, Frappe updates its modification timestamp. When the second user tries to save their older copy, Frappedetects that the document has been modified since it was opened and raises an error.

# C3 — Rename Integrity

When a Member record is renamed using Frappe's document rename mechanism, linked fields such as member in related Package Purchase
records are updated automatically.

This happens because member is a Link field pointing to the Member
DocType. Frappe's rename_doc() updates references to the renamed document so that linked records continue to point to the correct
Member.

# D2 — frappe.get_all is dangerous

# Unsafe Member Method

frappe.get_all() bypasses record-level permission checks. If it is used in a whitelisted API accessible to low-privilege users, they may retrieve records they are not authorized to view, potentially exposing sensitive member information.

frappe.get_all(
    "Member",
    fields=["name", "member_name", "phone", "email"]
)

# E1 — on_update() Recursion Pitfall

Frappe calls on_update() as part of the document save lifecycle.

Do not call self.save() on on_update.
save() triggers on_update(), so calling self.save()
inside on_update() causes recursive execution.
This can result in recursive execution and a recursion error.

# Incorrect pattern

def on_update(self):
    self.save()

# Correct pattern

def on_update(self):
    pass

Calculations should be performed in validate() not in on_update.

# E3 — One Performance Judgment Call

frappe.db.get_value() is enough because there is only one field requirement from studio settings.It avoids loading the complete document unlike frappe.db.get_doc(). Since this is used in a loop, the value is retrieved once before entering the loop rather than querying it repeatedly.

# H1 — Asynchronous frappe.call() Pitfall

frappe.call() is asynchronous, so validate may finish before the server responds. This can cause the document to save before the fetched data is checked.Fetch data in onload or refresh and use it during validate. Critical validations must also be enforced in server-side Python.

# I1 — SQL Parameterization

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

# J1 — Print Format

Calling frappe.get_all() directly inside a Jinja template mixes database queries with presentation logic. It can cause repeated queries during printing. Additionally, frappe.get_all() bypasses user permissions.

Using before_print() allows us to fetch and prepare the necessary data before rendering the template. We can store the result in doc.precomputed_field and reference it in Jinja:

# K2 — N+1 Query Problem

This creates an N+1 query problem. For 100 sessions, it can execute
101 database queries.

# Solution
import frappe
def get_session_trainers():
    sessions = frappe.get_all(
        "Class Session",
        fields=["name", "trainer"]
    )
    trainer_ids = list({
        session.trainer
        for session in sessions
        if session.trainer
    })
    trainers = frappe.get_all(
        "Trainer",
        filters={"name": ["in", trainer_ids]},
        fields=["name", "trainer_name", "phone"]
    ) if trainer_ids else []
    trainer_map = {
        trainer.name: trainer
        for trainer in trainers
    }
    for session in sessions:
        trainer = trainer_map.get(session.trainer)

        if trainer:
            print(trainer.trainer_name, trainer.phone)

This code only uses 2 queries and use dictionary lookups to retrieve trainer details without additional database queries , therefore fixing the N +1 problem.

# L1 — REST API CRUD Testing

curl -X GET \
  "http://flexledger.localhost:8001/api/resource/Member/MEM-2026-0001" \
  -H "Authorization: token API_KEY:API_SECRET"
# Response
HTTP Status: `200 OK`
{
  "data": {
    "name": "MEM-2026-0001",
    "member_name": "Dewald Brevis",
    "join_date": "2026-09-22",
    "status": "Active",
    "doctype": "Member"
  }
}





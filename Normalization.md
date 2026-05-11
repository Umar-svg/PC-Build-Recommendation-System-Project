User Table
1NF

No issue found.
All attributes are atomic and each field contains single values. No repeating groups exist.
No change was required.

2NF

No issue found.
Primary key is user_id, and all attributes depend fully on it.
No partial dependency exists, so no change was required.

3NF

No issue found.
No attribute depends on another non-key attribute (e.g., role is independent).
No transitive dependency exists, so no change was required.

Build_Request Table
1NF

No issue found.
All attributes are atomic and properly structured.
No change was required.

2NF

No issue found.
All fields depend fully on request_id.
No partial dependency exists.

3NF

No issue found.
No attribute depends on another non-key attribute.
No transitive dependency exists.

Component Table
1NF

No issue found.
All attributes contain single values and no repeating groups exist.
No change was required.

2NF

No issue found.
All attributes depend fully on component_id.
No partial dependency exists.

3NF

No issue found.
No attribute depends on another attribute (e.g., brand does not determine price or type).
No transitive dependency exists.

Recommended_Build Table
1NF

Issue: component_id created a logical repeating group because one build can contain multiple components.
Change: removed component_id and moved relationship to Build_Component table.
Why: to eliminate repetition and properly handle many-to-many relationship.

2NF

After removal of component_id, all remaining attributes depend fully on build_id.
No partial dependency exists.

3NF

No issue found after correction.
All attributes depend only on build_id and no transitive dependency exists.

Build_Component Table
1NF

No issue found.
Each row contains atomic values and represents a single component per build.
No change was required.

2NF

No issue found.
All attributes depend fully on primary key build_component_id.
No partial dependency exists.

3NF

No issue found.
No attribute depends on another non-key attribute.
No transitive dependency exists.

Step 2 — Remove Duplicates

Issue found:
component_id inside Recommended_Build was redundant because the relationship is already handled through Build_Component.

Change made:
Removed component_id from Recommended_Build.

Why:
To avoid redundancy and ensure proper many-to-many relationship design between Recommended_Build and Component.

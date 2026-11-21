"""Field availability with genuine person denominators, even for a partial CANDOR source."""
from collections import defaultdict

from runners.drive.sealed.week6_sc1_counts_v1 import source_layout
from runners.drive.sealed.week6_sc2_reader_v1 import _projected_rows
from runners.drive.sealed.week6_sc2_source_v1 import COLUMNS, key


def field_status(root, pins):
    import pyarrow.parquet as pq

    base = source_layout(root, pins)
    rows = []
    complete = True
    respondents = defaultdict(set)
    for role_code, role in enumerate(("survey", "clock", "speech"), 1):
        path = base / pins[role][0]
        if not path.is_file():
            complete = False
            continue
        reader = pq.ParquetFile(path)
        try:
            names = reader.schema_arrow.names
            present = {col for col in COLUMNS[role] if names.count(col) == 1}
            complete = complete and len(present) == len(COLUMNS[role])
            people = set()
            if role == "survey" and "user_id" in present:
                if "conversation_id" in present:
                    for chat, who in _projected_rows(reader, ("conversation_id", "user_id"), 8192):
                        if key(who):
                            people.add(who)
                            if key(chat):
                                respondents[chat].add(who)
                else:
                    people = {who for who, in _projected_rows(reader, ("user_id",), 8192) if key(who)}
            elif role == "clock" and "conversation_id" in present:
                # A recording clock has no person column. This row counts actual
                # survey respondents linked to recordings present in the clock.
                for chat, in _projected_rows(reader, ("conversation_id",), 8192):
                    if key(chat):
                        people.update(respondents.get(chat, ()))
            elif role == "speech" and "speaker" in present:
                people = {who for who, in _projected_rows(reader, ("speaker",), 8192) if key(who)}
            for field, col in enumerate(COLUMNS[role], 1):
                rows.append(dict(n=len(people), table_role=role_code, field=field, present=int(col in present)))
        finally:
            reader.close()
    return rows, complete

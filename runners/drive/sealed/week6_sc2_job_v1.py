"""Run the frozen paired analysis entirely inside the sealed CANDOR image."""
from pathlib import Path

from runners.drive.cards.week6_sealed_support_v1 import MIN_N, SealedFailure, write_tables
from runners.drive.sealed.week6_sc1_counts_v1 import Unavailable
from runners.drive.sealed.week6_sc2_model_v1 import DRAWS, aggregate, distribution, matrix
from runners.drive.sealed.week6_sc2_reader_v1 import load_dyads
from runners.drive.sealed.week6_sc2_source_v1 import PINS
from runners.drive.sealed.week6_sc2_status_v1 import field_status


def compare(root, out, *, pins=PINS):
    # The status projection and each independent study projection charge a digest
    # pass, a data scan and a full-file allowance for Parquet footer reads.
    if 9 * sum(size for _, size, _ in pins.values()) > 2_000_000_000:
        raise Unavailable(22)
    status, complete = field_status(root, pins)
    if not complete:
        return write_tables(Path(out), {"field_status": status})
    pairs, counts = load_dyads(root, pins=pins)
    data, people = matrix(pairs)
    if people != counts["retained_people"] or len(data) != counts["retained_conversations"]:
        raise SealedFailure(14, "Directed source support disagrees")
    if people < MIN_N:
        return write_tables(Path(out), {"field_status": status})
    fitted = distribution(data)
    replay_pairs, replay_counts = load_dyads(root, pins=pins, batch_size=4096)
    if pairs != replay_pairs or counts != replay_counts:
        raise SealedFailure(14, "Independent source support disagrees")
    replay_data, replay_people = matrix(replay_pairs)
    if replay_people != people:
        raise SealedFailure(14, "Participant count differs")
    records = aggregate(fitted, distribution(replay_data, replay=True), people, len(data))
    tables = {"field_status": status, "support": [dict(n=people, conversations=len(pairs), directed_reports=2*len(pairs),
                               metric_count=len(records), requested_draws=DRAWS,
                               descriptive=int(len(pairs)<20))]}
    for code, record in enumerate(records, 1):
        base = dict(n=people, metric=code, conversations=len(pairs), valid_draws=record["valid_draws"],
                    invalid_draws=record["invalid_draws"], descriptive=int(len(pairs)<20))
        if record["estimate"] is None:
            table = "unidentified"
        elif record["lower"] is None:
            table = "point_only"
            base["estimate"] = record["estimate"]
        else:
            table = "estimates"
            base.update(estimate=record["estimate"], lower=record["lower"], upper=record["upper"],
                        bootstrap_sd=record["bootstrap_sd"])
        tables.setdefault(table, []).append(base)
    return write_tables(Path(out), tables)


def main():
    import resource
    import signal
    import warnings

    resource.setrlimit(resource.RLIMIT_CPU, (21600, 21600))
    signal.alarm(21600)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            compare(Path("/data"), Path("/out"))
            return 0
        except SealedFailure as exc:
            return exc.code
        except Unavailable as exc:
            return exc.args[0] if exc.args in ((21,), (22,), (23,), (24,)) else 14
        except Exception:
            return 14

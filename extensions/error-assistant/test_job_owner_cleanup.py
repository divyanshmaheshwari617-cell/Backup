
"""
ModelMind Phase 8E ownership cleanup unit tests.

Tests the registry without changing real user jobs.
"""

from unittest.mock import patch

from ml_platform_error_assistant import (
    background_evaluation_routes as routes,
)


def main():
    stale_id = "f" * 32
    live_id = "e" * 32

    # Only synthetic test identities are used.
    # Preserve anything already present in memory.
    with routes._OWNER_LOCK:
        old_stale = routes._JOB_OWNERS.get(stale_id)
        old_live = routes._JOB_OWNERS.get(live_id)

        routes._JOB_OWNERS[stale_id] = "student_a"
        routes._JOB_OWNERS[live_id] = "student_b"

    try:
        real_get = routes.EVALUATION_JOBS.get

        def fake_get(job_id):
            if job_id == stale_id:
                return None

            if job_id == live_id:
                return {
                    "job_id": live_id,
                    "status": "completed",
                }

            return real_get(job_id)

        with patch.object(
            routes.EVALUATION_JOBS,
            "get",
            side_effect=fake_get,
        ):
            assert routes._check_owner(
                live_id, "student_b"
            )
            print("REAL OWNER: PASSED")

            assert not routes._check_owner(
                live_id, "student_a"
            )
            print("CROSS USER ACCESS: REJECTED")

            assert not routes._check_owner(
                stale_id, "student_a"
            )
            print("REMOVED JOB ACCESS: REJECTED")

            with routes._OWNER_LOCK:
                assert stale_id not in routes._JOB_OWNERS

                # Add a stale record again for pruning.
                routes._JOB_OWNERS[stale_id] = "student_a"

            removed = routes._prune_owner_registry()

            with routes._OWNER_LOCK:
                assert stale_id not in routes._JOB_OWNERS
                assert live_id in routes._JOB_OWNERS

            assert removed >= 1
            print("STALE OWNER CLEANUP: PASSED")
            print("LIVE OWNER PRESERVED: PASSED")

    finally:
        with routes._OWNER_LOCK:
            for job_id, original in (
                (stale_id, old_stale),
                (live_id, old_live),
            ):
                if original is None:
                    routes._JOB_OWNERS.pop(job_id, None)
                else:
                    routes._JOB_OWNERS[job_id] = original

    print("ALL PHASE 8E OWNER CHECKS PASSED")


if __name__ == "__main__":
    main()

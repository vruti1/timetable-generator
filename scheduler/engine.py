from dataclasses import dataclass


class SchedulingError(Exception):
    pass


@dataclass(frozen=True)
class Placement:
    teaching_id: int
    class_id: int
    subject_id: int
    faculty_id: int
    room_id: int
    time_slot_id: int
    batch_id: int | None


def generate_schedule(
    teaching,
    classes,
    subjects,
    rooms,
    slots,
    batches,
    availability
):
    class_map = {x.id: x for x in classes}
    subject_map = {x.id: x for x in subjects}

    availability_map = {
        (x.faculty_id, x.time_slot_id): x.available
        for x in availability
    }

    classroom_rooms = [
        r for r in rooms
        if r.room_type == "Classroom"
    ]

    lab_rooms = [
        r for r in rooms
        if r.room_type == "Lab"
    ]

    if not classroom_rooms:
        raise SchedulingError("No classroom rooms found.")

    if not lab_rooms:
        raise SchedulingError("No lab rooms found.")

    # ---------------------------------------------------------
    # Organize teaching assignments
    # ---------------------------------------------------------

    theory_jobs = []
    lab_assignments = {}

    for row in teaching:
        if row.faculty_id is None:
            continue
        subject = subject_map[row.subject_id]

        if subject.subject_type == "Lab":
            lab_assignments.setdefault(
                row.class_id,
                []
            ).append(row)

        else:
            for _ in range(row.periods_per_week):
                theory_jobs.append({
                    "teaching_id": row.id,
                    "class_id": row.class_id,
                    "subject_id": row.subject_id,
                    "faculty_id": row.faculty_id,
                    "strength": class_map[row.class_id].strength,
                })

    # ---------------------------------------------------------
    # State
    # ---------------------------------------------------------

    class_busy = set()
    faculty_busy = set()
    room_busy = set()
    batch_busy = set()

    result = []
    faculty_daily_hours = {}
    subject_day_busy = set()

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    def faculty_available(faculty_id, slot_id):
        return availability_map.get(
            (faculty_id, slot_id),
            True
        )
        
    def faculty_has_daily_capacity(faculty_id, day, hours):
        current_hours = faculty_daily_hours.get(
            (faculty_id, day),
            0
        )
        return current_hours + hours <= 5
    
    def room_candidates(room_type, strength, slot_id):
        source = (
            lab_rooms
            if room_type == "Lab"
            else classroom_rooms
        )

        return [
            r for r in source
            if r.capacity >= strength
            and (r.id, slot_id) not in room_busy
        ]

    # ---------------------------------------------------------
    # Slots by day
    # ---------------------------------------------------------

    slots_by_day = {}

    for slot in slots:
        slots_by_day.setdefault(
            slot.day,
            []
        ).append(slot)

    for day in slots_by_day:
        slots_by_day[day].sort(
            key=lambda x: x.start_time
        )

    day_order = list(slots_by_day.keys())

    slot_position = {}

    for day_index, day in enumerate(day_order):
        for position, slot in enumerate(
            slots_by_day[day]
        ):
            slot_position[slot.id] = (
                day_index,
                position
            )

    # ---------------------------------------------------------
    # Valid 2-hour lab blocks
    # ---------------------------------------------------------

    lab_blocks = []

    for day in day_order:
        day_slots = slots_by_day[day]

        for i in range(len(day_slots) - 1):
            first = day_slots[i]
            second = day_slots[i + 1]

            if first.end_time == second.start_time:
                lab_blocks.append(
                    (first, second)
                )

    if not lab_blocks:
        raise SchedulingError(
            "No consecutive time slots are available "
            "for 2-hour laboratory sessions."
        )

    # ---------------------------------------------------------
    # Compactness scoring
    # ---------------------------------------------------------

    def compact_score(class_id, slot):
        day_index, position = slot_position[slot.id]
        day = slot.day

        existing_positions = []

        for cid, slot_id in class_busy:
            if cid != class_id:
                continue

            existing_day, existing_position = (
                slot_position[slot_id]
            )

            if existing_day == day_index:
                existing_positions.append(
                    existing_position
                )

        # If this class already has sessions on this day,
        # prefer staying close to them.
        if existing_positions:
            distance = min(
                abs(position - p)
                for p in existing_positions
            )

            # Adjacent slot is ideal.
            if distance == 1:
                return (
                    0,
                    day_index,
                    position
                )

            # Same day but with a small gap.
            return (
                10 + distance,
                day_index,
                position
            )

        # Count how many days this class already uses.
        # Count sessions already scheduled on each day.
        day_load = 0

        for cid, slot_id in class_busy:
            if cid == class_id:
                existing_day, _ = slot_position[slot_id]

                if existing_day == day_index:
                    day_load += 1

        # Prefer the least-loaded day.
        # This distributes the timetable across the week
        # instead of filling Monday first.
        return (
            day_load,
            day_index,
            position
        )

    def lab_block_score(class_id, first, second):
        first_score = compact_score(
            class_id,
            first
        )

        second_score = compact_score(
            class_id,
            second
        )

        return (
            min(
                first_score[0],
                second_score[0]
            ),
            first_score[1],
            first_score[2]
        )

    # ---------------------------------------------------------
    # Lab rotation
    # ---------------------------------------------------------

    lab_blocks_by_class = {}

    for class_id, assignments in lab_assignments.items():

        class_batches = [
            b for b in batches
            if b.class_id == class_id
        ]

        if not class_batches:
            raise SchedulingError(
                f"No lab batches found for "
                f"{class_map[class_id].class_name}."
            )

        if len(class_batches) > len(lab_rooms):
            raise SchedulingError(
                f"Not enough lab rooms for "
                f"{class_map[class_id].class_name}."
            )

        block_count = len(assignments)

        rotations = []

        for block_index in range(block_count):

            rotation = []

            for batch_index in range(
                len(class_batches)
            ):

                lab_index = (
                    block_index + batch_index
                ) % len(assignments)

                rotation.append(
                    (
                        class_batches[batch_index],
                        assignments[lab_index]
                    )
                )

            rotations.append(rotation)

        lab_blocks_by_class[class_id] = rotations

    # ---------------------------------------------------------
    # Lab jobs
    # ---------------------------------------------------------

    lab_block_jobs = []

    for class_id, rotations in lab_blocks_by_class.items():

        for rotation_index, rotation in enumerate(
            rotations
        ):

            lab_block_jobs.append({
                "class_id": class_id,
                "rotation_index": rotation_index,
                "rotation": rotation,
            })

    lab_block_jobs.sort(
        key=lambda x: (
            -len(x["rotation"]),
            x["class_id"]
        )
    )

    # ---------------------------------------------------------
    # Schedule lab blocks
    # ---------------------------------------------------------

    def schedule_lab_blocks(index):

        if index == len(lab_block_jobs):
            return True

        block_job = lab_block_jobs[index]

        class_id = block_job["class_id"]
        rotation = block_job["rotation"]

        possible_blocks = sorted(
            lab_blocks,
            key=lambda pair: lab_block_score(
                class_id,
                pair[0],
                pair[1]
            )
        )

        for first, second in possible_blocks:

            slots_pair = (
                first,
                second
            )

            if any(
                (class_id, slot.id) in class_busy
                for slot in slots_pair
            ):
                continue

            proposed = []
            used_rooms = set()
            valid = True

            for batch, assignment in rotation:

                subject_id = assignment.subject_id
                faculty_id = assignment.faculty_id
                if not faculty_has_daily_capacity(
                    faculty_id,
                    first.day,
                    2
                ):
                    valid = False
                    break
                for slot in slots_pair:

                    if (
                        faculty_id,
                        slot.id
                    ) in faculty_busy:
                        valid = False
                        break

                    if not faculty_available(
                        faculty_id,
                        slot.id
                    ):
                        valid = False
                        break

                    if (
                        batch.id,
                        slot.id
                    ) in batch_busy:
                        valid = False
                        break

                    if (
                        class_id,
                        subject_id,
                        slot.day
                    ) in subject_day_busy:
                        valid = False
                        break

                if not valid:
                    break

                available_rooms = [
                    r for r in lab_rooms
                    if r.capacity >= batch.student_count
                    and r.id not in used_rooms
                    and all(
                        (r.id, slot.id) not in room_busy
                        for slot in slots_pair
                    )
                ]

                if not available_rooms:
                    valid = False
                    break

                room = sorted(
                    available_rooms,
                    key=lambda r: r.id
                )[0]

                used_rooms.add(room.id)

                proposed.append(
                    (
                        batch,
                        assignment,
                        room
                    )
                )

            if not valid:
                continue

            added = []

            for batch, assignment, room in proposed:

                for slot in slots_pair:
                    faculty_daily_hours[
                        (
                            assignment.faculty_id,
                            slot.day
                        )
                    ] = faculty_daily_hours.get(
                        (
                            assignment.faculty_id,
                            slot.day
                        ),
                        0
                    ) + 1
                    class_busy.add(
                        (
                            class_id,
                            slot.id
                        )
                    )

                    faculty_busy.add(
                        (
                            assignment.faculty_id,
                            slot.id
                        )
                    )

                    room_busy.add(
                        (
                            room.id,
                            slot.id
                        )
                    )

                    batch_busy.add(
                        (
                            batch.id,
                            slot.id
                        )
                    )

                    subject_day_busy.add(
                        (
                            class_id,
                            assignment.subject_id,
                            slot.day
                        )
                    )

                    result.append(
                        Placement(
                            assignment.id,
                            class_id,
                            assignment.subject_id,
                            assignment.faculty_id,
                            room.id,
                            slot.id,
                            batch.id
                        )
                    )

                    added.append(
                        (
                            class_id,
                            assignment.faculty_id,
                            room.id,
                            batch.id,
                            assignment.subject_id,
                            slot.id,
                            slot.day
                        )
                    )

            if schedule_lab_blocks(index + 1):
                return True

            for (
                cid,
                faculty_id,
                room_id,
                batch_id,
                subject_id,
                slot_id,
                day
            ) in added:
                faculty_daily_hours[
                    (faculty_id, day)
                ] -= 1

                if faculty_daily_hours[
                    (faculty_id, day)
                ] == 0:
                    del faculty_daily_hours[
                        (faculty_id, day)
                    ]
                    
                class_busy.remove(
                    (
                        cid,
                        slot_id
                    )
                )

                faculty_busy.remove(
                    (
                        faculty_id,
                        slot_id
                    )
                )

                room_busy.remove(
                    (
                        room_id,
                        slot_id
                    )
                )

                batch_busy.remove(
                    (
                        batch_id,
                        slot_id
                    )
                )

                subject_day_busy.remove(
                    (
                        cid,
                        subject_id,
                        day
                    )
                )

                result.pop()

        return False

    if not schedule_lab_blocks(0):
        raise SchedulingError(
            "Could not create the required parallel "
            "2-hour laboratory rotation."
        )

    # ---------------------------------------------------------
    # Theory
    # ---------------------------------------------------------

    theory_jobs.sort(
        key=lambda j: (
            -j["strength"],
            j["class_id"],
            j["subject_id"]
        )
    )

    def theory_candidates(job):

        candidates = []

        for slot in slots:

            if (
                job["class_id"],
                slot.id
            ) in class_busy:
                continue
            if not faculty_has_daily_capacity(
                job["faculty_id"],
                slot.day,
                1
            ):
                continue
            if (
                job["faculty_id"],
                slot.id
            ) in faculty_busy:
                continue

            if not faculty_available(
                job["faculty_id"],
                slot.id
            ):
                continue

            if (
                job["class_id"],
                job["subject_id"],
                slot.day
            ) in subject_day_busy:
                continue

            rooms_available = room_candidates(
                "Classroom",
                job["strength"],
                slot.id
            )

            for room in rooms_available:

                score = compact_score(
                    job["class_id"],
                    slot
                )

                candidates.append(
                    (
                        score,
                        slot,
                        room
                    )
                )

        candidates.sort(
            key=lambda x: x[0]
        )

        return [
            (slot, room)
            for _, slot, room in candidates
        ]

    def schedule_theory(index):

        if index == len(theory_jobs):
            return True

        job = theory_jobs[index]

        for slot, room in theory_candidates(job):

            class_key = (
                job["class_id"],
                slot.id
            )

            faculty_key = (
                job["faculty_id"],
                slot.id
            )

            room_key = (
                room.id,
                slot.id
            )

            subject_day_key = (
                job["class_id"],
                job["subject_id"],
                slot.day
            )
            faculty_daily_hours[
                (
                    job["faculty_id"],
                    slot.day
                )
            ] = faculty_daily_hours.get(
                (
                    job["faculty_id"],
                    slot.day
                ),
                0
            ) + 1
            class_busy.add(class_key)
            faculty_busy.add(faculty_key)
            room_busy.add(room_key)
            subject_day_busy.add(subject_day_key)

            result.append(
                Placement(
                    job["teaching_id"],
                    job["class_id"],
                    job["subject_id"],
                    job["faculty_id"],
                    room.id,
                    slot.id,
                    None
                )
            )

            if schedule_theory(index + 1):
                return True
            
            faculty_daily_hours[
                (
                    job["faculty_id"],
                    slot.day
                )
            ] -= 1

            if faculty_daily_hours[
                (
                    job["faculty_id"],
                    slot.day
                )
            ] == 0:
                del faculty_daily_hours[
                    (
                        job["faculty_id"],
                        slot.day
                    )
                ]
                
            result.pop()

            class_busy.remove(class_key)
            faculty_busy.remove(faculty_key)
            room_busy.remove(room_key)
            subject_day_busy.remove(subject_day_key)

        return False

    if not schedule_theory(0):
        raise SchedulingError(
            "Could not schedule all theory classes "
            "around the laboratory rotation."
        )

    return result
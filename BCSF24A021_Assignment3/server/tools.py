"""
tools.py (server side)

Plain Python functions. FastMCP turns each one into an MCP tool: the type
hints become the input schema and the docstring becomes the description the
model reads. There is no @tool decorator here and no LangChain import.
"""
GRADE_BANDS = [
    (85, 4.0),   # A
    (80, 3.7),   # A-
    (75, 3.3),   # B+
    (70, 3.0),   # B
    (65, 2.7),   # B-
    (61, 2.3),   # C+
    (58, 2.0),   # C
    (55, 1.7),   # C-
    (50, 1.0),   # D
    (0, 0.0),    # F
]

COURSES = {
    1: [
        ("MS-251", "Probability & Statistics", 3.0),
        ("GE-160", "Applications of ICT", 3.0),
        ("GE-169", "Applied Physics", 3.0),
        ("GE-167", "Discrete Structures", 3.0),
        ("HQ-001", "Quran Translation I", 0.5),
        ("GE-190", "Functional English", 3.0),
    ],
    2: [
        ("CC-112", "Programming Fundamentals", 3.0),
        ("CC-112-L", "Programming Fundamentals Lab", 1.0),
        ("CC-110", "Digital Logic Design", 2.0),
        ("CC-110-L", "Digital Logic Design Lab", 1.0),
        ("MS-252", "Linear Algebra", 3.0),
        ("GE-191", "Expository Writing", 3.0),
        ("GE-163", "Islamic Studies", 2.0),
        ("HQ-002", "Quran Translation II", 0.5),
    ],
    3: [
        ("CC-211", "Object Oriented Programming", 3.0),
        ("CC-211-L", "Object Oriented Programming Lab", 1.0),
        ("CC-215", "Database Systems", 3.0),
        ("CC-215-L", "Database Systems Lab", 1.0),
        ("CC-210", "Computer Organization & Assembly Language", 3.0),
        ("GE-162", "Calculus & Analytical Geometry", 3.0),
        ("GE-192", "Introduction to Management", 2.0),
        ("HQ-003", "Quran Translation III", 0.5),
    ],
    4: [
        ("CC-213", "Data Structures", 3.0),
        ("CC-213-L", "Data Structures Lab", 1.0),
        ("CC-312", "Information Security", 3.0),
        ("CC-214", "Computer Networks", 3.0),
        ("CC-212", "Software Engineering", 3.0),
        ("DC-220", "Advanced Database Management Systems", 3.0),
        ("HQ-004", "Quran Translation IV", 0.5),
    ],
    5: [
        ("CC-313", "Analysis of Algorithms", 3.0),
        ("CC-310", "Artificial Intelligence", 3.0),
        ("DC-320", "Theory of Automata and Formal Languages", 3.0),
        ("DC-321", "Human Computer Interaction", 3.0),
        ("DC-322", "Computer Architecture", 3.0),
        ("EC-330", "Web Technologies / Elective", 3.0),
        ("HQ-005", "Quran Translation V", 0.5),
    ],
    6: [
        ("CC-311", "Operating Systems", 3.0),
        ("EC-333", "Mobile Application Development / Elective", 3.0),
        ("EC-324", "Software Construction & Development / Elective", 3.0),
        ("EC-335", "Machine Learning / Elective", 3.0),
        ("EC-334", "Game Design and Development / Elective", 3.0),
        ("MS-253", "Multivariable Calculus", 3.0),
        ("HQ-006", "Quran Translation VI", 0.5),
    ],
    7: [
        ("CC-411", "Final Year Project I", 2.0),
        ("DC-328", "Parallel & Distributed Computing", 3.0),
        ("EC-345", "Computer Vision / Elective", 3.0),
        ("EC-425", "Software Quality Engineering / Elective", 3.0),
        ("MS-254", "Technical and Business Writing", 3.0),
        ("GE-263", "Entrepreneurship", 2.0),
        ("GE-262", "Professional Practices", 2.0),
        ("HQ-007", "Quran Translation VII", 0.5),
    ],
    8: [
        ("CC-412", "Final Year Project II", 4.0),
        ("DC-421", "Compiler Construction", 3.0),
        ("UE-272", "Introduction to Marketing", 3.0),
        ("GE-168", "Ideology and Constitution of Pakistan", 2.0),
        ("GE-363", "Civics and Community Engagement", 2.0),
        ("HQ-008", "Quran Translation VIII", 0.5),
    ],
}


def marks_to_grade_points(marks: int) -> float | str:
    """Convert marks out of 100 into a PUCIT grade point (for example 78 -> 3.3).

    Use this whenever the student gives you raw marks (a number out of 100)
    for a course, before you can calculate a GPA. Call it once per course.
    """
    if marks < 0 or marks > 100:
        return "Error: marks must be between 0 and 100"

    for min_marks, points in GRADE_BANDS:
        if marks >= min_marks:
            return points

    return "Error: could not find a matching grade band"


def calculate_semester_gpa(grade_points: list[float], credit_hours: list[float]) -> float | str:
    """Calculate one semester's credit-hour-weighted GPA.

    Use this once you have a grade point (from marks_to_grade_points) and the
    credit hours for every course the student took in that semester. Both
    lists must be in the same order and the same length (grade_points[i] goes
    with credit_hours[i]).
    """
    if len(grade_points) != len(credit_hours):
        return "Error: grade_points and credit_hours must be the same length"

    if len(grade_points) == 0:
        return "Error: need at least one course to calculate a GPA"

    if any(ch <= 0 for ch in credit_hours):
        return "Error: credit hours must be greater than 0"

    total_points = sum(gp * ch for gp, ch in zip(grade_points, credit_hours))
    total_hours = sum(credit_hours)

    return round(total_points / total_hours, 2)


def calculate_new_cgpa(
    current_cgpa: float,
    completed_credit_hours: float,
    semester_gpa: float,
    semester_credit_hours: float,
) -> float | str:
    """Project the new CGPA after adding one semester's GPA to a student's record.

    Use this when the student already knows their current CGPA and completed
    credit hours, and wants to know where a new semester's GPA will leave
    their overall CGPA.
    """
    if completed_credit_hours < 0 or semester_credit_hours <= 0:
        return "Error: credit hours must be positive"

    if not (0 <= current_cgpa <= 4.0) or not (0 <= semester_gpa <= 4.0):
        return "Error: CGPA and GPA values must be between 0 and 4.0"

    total_hours = completed_credit_hours + semester_credit_hours
    new_cgpa = (
        current_cgpa * completed_credit_hours + semester_gpa * semester_credit_hours
    ) / total_hours

    return round(new_cgpa, 2)


def required_gpa_for_target(
    target_cgpa: float,
    current_cgpa: float,
    completed_credit_hours: float,
    remaining_credit_hours: float,
) -> float | str:
    """Calculate the GPA needed over the remaining credit hours to hit a target CGPA.

    Use this when the student names a target CGPA and you know their current
    CGPA, completed credit hours, and remaining credit hours.

    Note: this can return a number above 4.0. That means the target is NOT
    reachable in that many remaining credit hours - it does not mean the
    calculation is wrong. In that case, try again with more remaining credit
    hours (a longer horizon) instead of reporting the number as an answer.
    """
    if remaining_credit_hours <= 0:
        return "Error: remaining credit hours must be greater than 0"

    if not (0 <= target_cgpa <= 4.0) or not (0 <= current_cgpa <= 4.0):
        return "Error: CGPA values must be between 0 and 4.0"

    total_hours = completed_credit_hours + remaining_credit_hours
    required = (
        target_cgpa * total_hours - current_cgpa * completed_credit_hours
    ) / remaining_credit_hours

    return round(required, 2)


def get_semester_courses(semester: int) -> str:
    """Return the courses and credit hours for one semester (1 to 8).

    Use this when you need to know which courses a student took, or their
    credit hours, for a specific semester in the BS(CS) scheme of studies.
    Math Deficiency courses are never included, since they don't count
    towards GPA.
    """
    if semester < 1 or semester > 8:
        return "Error: semester must be between 1 and 8"

    lines = []
    for code, name, credit_hours in COURSES[semester]:
        lines.append(f"{code}: {name} ({credit_hours} credit hours)")

    return "\n".join(lines)


def get_remaining_credit_hours(current_semester: int) -> float | str:
    """Total the credit hours left AFTER a semester you have finished.

    Use this when the student wants to know how many credit hours are left
    until graduation. current_semester is the last semester they have fully
    finished (1 to 8). For a specific group of semesters (for example just
    semester 5, or semesters 5 and 6 together) use get_credit_hours instead.
    """
    if current_semester < 1 or current_semester > 8:
        return "Error: semester must be between 1 and 8"

    remaining = 0.0
    for semester in range(current_semester + 1, 9):
        for _, _, credit_hours in COURSES[semester]:
            remaining += credit_hours

    return remaining


def get_credit_hours(semesters: list[int]) -> float | str:
    """Add up the credit hours of a list of semesters (each from 1 to 8).

    Use this to get the credit hours of a window of semesters, for example
    [5] for just semester 5, [5, 6] for semesters 5 and 6 together, or
    [5, 6, 7] for three semesters. This is how you build the
    remaining_credit_hours for required_gpa_for_target without adding
    numbers yourself.
    """
    if len(semesters) == 0:
        return "Error: give at least one semester"

    if len(set(semesters)) != len(semesters):
        return "Error: each semester can only be listed once"

    total = 0.0
    for semester in semesters:
        if semester < 1 or semester > 8:
            return "Error: semester must be between 1 and 8"
        for _, _, credit_hours in COURSES[semester]:
            total += credit_hours

    return total


def save_report(filename: str, content: str) -> str:
    """Save a short text summary (like a GPA result or a graduation plan) to a file.

    Only call this after you have already produced a real result, and only
    when the student has said yes to saving it.
    """
    if not filename.strip():
        return "Error: filename cannot be empty"

    if not filename.endswith(".txt"):
        filename = filename + ".txt"

    try:
        with open(filename, "w") as f:
            f.write(content)
        return f"Saved report to {filename}"
    except Exception as e:
        return f"Error: could not save file - {e}"

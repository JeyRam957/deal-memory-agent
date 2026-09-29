import re


def extract_section(text, section_name, next_sections):
    pattern = rf"{re.escape(section_name)}\s*(.*?)(?=\n(?:{'|'.join(map(re.escape, next_sections))})\s*\n|\Z)"

    match = re.search(
        pattern,
        text,
        flags=re.IGNORECASE | re.DOTALL
    )

    if not match:
        return ""

    return match.group(1).strip()


def parse_analysis(text):

    sections = [
        "CALL SUMMARY",
        "CUSTOMER NEEDS",
        "OBJECTIONS",
        "ISSUES DETECTED",
        "BUYING SIGNALS",
        "SENTIMENT",
        "DEAL RISK",
        "RISK REASON",
        "COMPETITORS",
        "NEXT BEST ACTION",
        "FOLLOW-UP QUESTIONS"
    ]

    result = {}

    for index, section in enumerate(sections):

        remaining = sections[index + 1:]

        result[section] = extract_section(
            text,
            section,
            remaining
        )

    return result
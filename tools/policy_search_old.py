from pathlib import Path


POLICY_FILE = Path("data/policies.txt")


def read_policy_file():

    if not POLICY_FILE.exists():

        return ""

    with open(
        POLICY_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        return f.read()


def policy_search_tool(query: str):

    query=query.lower()

    data=read_policy_file()

    if not data:

        return "Policy file not found"

    sections=data.split(
        "------------------------------------------------"
    )

    matches=[]

    for section in sections:

        if query in section.lower():

            matches.append(
                section.strip()
            )

    if matches:

        return "\n\n".join(matches)

    return "No matching policy found."

import json
import os
import sys

from phantom_logic.work_items.interfaces.WorkItemAgentInterface import (
    WorkItemAgentInterface,
)


def main() -> int:
    calling_agent = os.environ.get(
        "PHANTOM_LOGIC_CALLING_AGENT",
        "",
    )

    try:
        request = json.load(sys.stdin)

        if not isinstance(request, dict):
            raise ValueError("Request must be a JSON object.")

        result = WorkItemAgentInterface.create_work_items(
            calling_agent=calling_agent,
            work_items=request.get("work_items"),
        )

    except Exception as exception:
        result = {
            "success": False,
            "errors": [
                f"Work Item operation failed: {exception}"
            ],
            "work_items": [],
            "events": [],
        }

    json.dump(result, sys.stdout)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

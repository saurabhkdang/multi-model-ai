import json
import requests

API_URL = "http://127.0.0.1:8000/ask"


def normalize_agents(agents):
    return sorted(list(set(agents)))


def run_tests():
    with open("tests/test_cases.json", "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    passed = 0
    failed = 0

    for case in test_cases:
        payload = {
            "query": case["question"],
            "debug": True
        }

        try:
            response = requests.post(API_URL, json=payload, timeout=60)
            data = response.json()

            debug = data.get("debug", {})
            actual_agents = debug.get("agents_called", [])

            expected_agents = normalize_agents(case["expected_agents"])
            actual_agents = normalize_agents(actual_agents)

            is_passed = expected_agents == actual_agents

            if is_passed:
                passed += 1
                status = "PASS"
            else:
                failed += 1
                status = "FAIL"

            print("=" * 80)
            print(f"Test ID: {case['id']} | {status}")
            print(f"Question: {case['question']}")
            print(f"Expected Agents: {expected_agents}")
            print(f"Actual Agents:   {actual_agents}")
            print(f"Expected Type: {case['expected_type']}")
            print(f"Request ID: {debug.get('request_id')}")

            if not is_passed:
                print("Response:")
                print(json.dumps(data, indent=2, ensure_ascii=False))

        except Exception as e:
            failed += 1
            print("=" * 80)
            print(f"Test ID: {case['id']} | ERROR")
            print(f"Question: {case['question']}")
            print(f"Error: {str(e)}")

    print("=" * 80)
    print("TEST SUMMARY")
    print(f"Total: {len(test_cases)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")


if __name__ == "__main__":
    run_tests()
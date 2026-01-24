import json
import sys
import xml.etree.ElementTree as ET


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: dbt_test_to_junit.py <run_results.json> <output.xml>")
        return 2

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    with open(input_path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)

    results = payload.get("results", [])
    testsuite = ET.Element("testsuite", name="dbt tests")

    for result in results:
        test_name = result.get("unique_id", "unknown")
        status = result.get("status", "unknown")
        time_value = str(result.get("execution_time", 0))
        testcase = ET.SubElement(testsuite, "testcase", name=test_name, time=time_value)

        if status == "fail":
            message = result.get("message") or "dbt test failed"
            ET.SubElement(testcase, "failure", message=message).text = message
        elif status == "error":
            message = result.get("message") or "dbt test error"
            ET.SubElement(testcase, "error", message=message).text = message
        elif status == "skipped":
            ET.SubElement(testcase, "skipped", message="skipped")

    tree = ET.ElementTree(testsuite)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

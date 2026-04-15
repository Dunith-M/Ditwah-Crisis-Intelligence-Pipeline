def generate_token_report(results: list) -> list:
    report = []

    for r in results:
        report.append({
            "tokens": r["tokens"],
            "action": r["action"]
        })

    return report
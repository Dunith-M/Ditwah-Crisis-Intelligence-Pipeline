from typing import List, Dict


class ChooseRescueRouteUseCase:

    def execute(self, incidents: List[Dict]) -> Dict:

        # Strategy 1: Highest score first
        highest_score_route = sorted(
            incidents, key=lambda x: x["total_score"], reverse=True
        )

        # Strategy 2: Closest first (proxy = accessibility high)
        closest_route = sorted(
            incidents, key=lambda x: x["accessibility"], reverse=True
        )

        # Strategy 3: Furthest first
        furthest_route = sorted(
            incidents, key=lambda x: x["accessibility"]
        )

        strategies = {
            "highest_score": highest_score_route,
            "closest_first": closest_route,
            "furthest_first": furthest_route
        }

        comparison = self._compare(strategies)

        return {
            "strategies": strategies,
            "comparison": comparison,
            "final_decision": comparison["best_strategy"]
        }

    def _compare(self, strategies: Dict) -> Dict:

        results = {}

        for name, route in strategies.items():
            total_score = sum(i["total_score"] for i in route)
            total_time = sum(10 - i["accessibility"] for i in route)  # proxy

            plausibility = "high" if total_time < 20 else "medium"

            results[name] = {
                "total_score_saved": total_score,
                "total_travel_time": total_time,
                "plausibility": plausibility
            }

        # Decision logic
        best = max(results, key=lambda x: results[x]["total_score_saved"])

        return {
            "strategy_metrics": results,
            "best_strategy": best
        }
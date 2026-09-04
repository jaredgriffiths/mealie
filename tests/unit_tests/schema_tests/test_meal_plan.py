from datetime import UTC, datetime

import pytest

from mealie.schema.meal_plan.plan_rules import PlanRulesDay

test_cases = [
    (datetime(2022, 2, 7, tzinfo=UTC), PlanRulesDay.monday),
    (datetime(2022, 2, 8, tzinfo=UTC), PlanRulesDay.tuesday),
    (datetime(2022, 2, 9, tzinfo=UTC), PlanRulesDay.wednesday),
    (datetime(2022, 2, 10, tzinfo=UTC), PlanRulesDay.thursday),
    (datetime(2022, 2, 11, tzinfo=UTC), PlanRulesDay.friday),
    (datetime(2022, 2, 12, tzinfo=UTC), PlanRulesDay.saturday),
    (datetime(2022, 2, 13, tzinfo=UTC), PlanRulesDay.sunday),
]


@pytest.mark.parametrize("date, expected", test_cases)
def test_date_obj_to_enum(date: datetime, expected: PlanRulesDay):
    assert PlanRulesDay.from_date(date) == expected

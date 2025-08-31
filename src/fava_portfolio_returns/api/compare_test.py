import datetime
import unittest

from fava_portfolio_returns.api.compare import Series, DetailedDataPoint
from fava_portfolio_returns.api.compare import compare_chart
from fava_portfolio_returns.test.test import approx2
from fava_portfolio_returns.test.test import load_portfolio_file


class TestCompare(unittest.TestCase):
    def test_savings_plan_simple(self):
        p = load_portfolio_file("savings_plan")
        series = compare_chart(p, datetime.date(2020, 1, 1), datetime.date(2020, 4, 1), "simple", ["c:CORP"])
        assert series == [
            Series(
                name="Returns",
                data=[
                    (datetime.date(2020, 1, 1), 0.0),
                    (datetime.date(2020, 2, 1), 0.2),
                    (datetime.date(2020, 3, 1), approx2(0.33)),
                    (datetime.date(2020, 4, 1), approx2(0.43)),
                ],
            ),
            Series(
                name="CORP (CORP)",
                data=[
                    (datetime.date(2020, 1, 1), 0.0),
                    (datetime.date(2020, 2, 1), 0.5),
                    (datetime.date(2020, 3, 1), 1),
                    (datetime.date(2020, 4, 1), 1.5),
                ],
            ),
        ]

    def test_savings_plan_detailed_table(self):
        p = load_portfolio_file("savings_plan")
        series = compare_chart(p, datetime.date(2020, 1, 1), datetime.date(2020, 4, 1), "detailed_table", ["c:CORP"])
        
        # Check that we get DetailedDataPoint objects
        assert len(series) == 2
        assert series[0].name == "Returns"
        assert series[1].name == "CORP (CORP)"
        
        # Check that the data contains DetailedDataPoint objects
        for serie in series:
            assert len(serie.data) == 4
            for date, value in serie.data:
                assert isinstance(value, DetailedDataPoint)
                assert hasattr(value, 'date')
                assert hasattr(value, 'market')
                assert hasattr(value, 'cost')
                assert hasattr(value, 'cash')
                assert hasattr(value, 'simple_return')
                assert hasattr(value, 'twr')
                assert value.date == date

    def test_savings_plan_twr(self):
        p = load_portfolio_file("savings_plan")
        series = compare_chart(p, datetime.date(2020, 1, 1), datetime.date(2020, 4, 1), "twr", ["c:CORP"])
        assert series == [
            Series(
                name="Returns",
                data=[
                    # TWR is identical to price series, because effects of cash flows are eliminated
                    (datetime.date(2020, 1, 1), 0.0),
                    (datetime.date(2020, 2, 1), 0.5),
                    (datetime.date(2020, 3, 1), 1.0),
                    (datetime.date(2020, 4, 1), 1.5),
                ],
            ),
            Series(
                name="CORP (CORP)",
                data=[
                    (datetime.date(2020, 1, 1), 0.0),
                    (datetime.date(2020, 2, 1), 0.5),
                    (datetime.date(2020, 3, 1), 1.0),
                    (datetime.date(2020, 4, 1), 1.5),
                ],
            ),
        ]

    def test_savings_plan_middle(self):
        p = load_portfolio_file("savings_plan")
        series = compare_chart(p, datetime.date(2020, 3, 1), datetime.date(2020, 4, 1), "simple", ["c:CORP"])
        print(series[0].data[0])
        assert series == [
            Series(
                name="Returns",
                data=[
                    (datetime.date(2020, 3, 1), 0.0),
                    (datetime.date(2020, 4, 1), approx2(0.09)),
                ],
            ),
            Series(
                name="CORP (CORP)",
                data=[
                    (datetime.date(2020, 3, 1), 0.0),
                    (datetime.date(2020, 4, 1), 0.25),
                ],
            ),
        ]

    def test_linear_growth_stock_simple(self):
        p = load_portfolio_file("linear_growth_stock")
        series = compare_chart(p, datetime.date(2020, 1, 1), datetime.date(2020, 6, 1), "simple", ["c:CORP"])
        assert series == [
            Series(
                name="Returns",
                data=[
                    (datetime.date(2020, 1, 1), 0.0),
                    (datetime.date(2020, 2, 1), 0.5),
                    (datetime.date(2020, 3, 1), 1.0),
                    (datetime.date(2020, 4, 1), approx2(0.42)),  # returns dropped because of investment
                    (datetime.date(2020, 5, 1), approx2(0.71)),
                    (datetime.date(2020, 6, 1), 1.0),
                ],
            ),
            Series(
                name="CORP (CORP)",
                data=[
                    (datetime.date(2020, 1, 1), 0.0),
                    (datetime.date(2020, 2, 1), 0.5),
                    (datetime.date(2020, 3, 1), 1.0),
                    (datetime.date(2020, 4, 1), 1.5),
                    (datetime.date(2020, 5, 1), 2.0),
                    (datetime.date(2020, 6, 1), 2.5),
                ],
            ),
        ]

    def test_linear_growth_stock_twr(self):
        p = load_portfolio_file("linear_growth_stock")
        series = compare_chart(p, datetime.date(2020, 1, 1), datetime.date(2020, 6, 1), "twr", ["c:CORP"])
        assert series == [
            Series(
                name="Returns",
                data=[
                    # TWR is identical to price series, because effects of cash flows are eliminated
                    (datetime.date(2020, 1, 1), 0.0),
                    (datetime.date(2020, 2, 1), 0.5),
                    (datetime.date(2020, 3, 1), 1.0),
                    (datetime.date(2020, 4, 1), 1.5),
                    (datetime.date(2020, 5, 1), 2.0),
                    (datetime.date(2020, 6, 1), 2.5),
                ],
            ),
            Series(
                name="CORP (CORP)",
                data=[
                    (datetime.date(2020, 1, 1), 0.0),
                    (datetime.date(2020, 2, 1), 0.5),
                    (datetime.date(2020, 3, 1), 1.0),
                    (datetime.date(2020, 4, 1), 1.5),
                    (datetime.date(2020, 5, 1), 2.0),
                    (datetime.date(2020, 6, 1), 2.5),
                ],
            ),
        ]

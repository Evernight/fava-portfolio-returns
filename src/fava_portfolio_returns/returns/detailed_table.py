from dataclasses import dataclass
import datetime
import logging
from typing import Union

from fava_portfolio_returns.api.portfolio import portfolio_values
from fava_portfolio_returns.core.portfolio import FilteredPortfolio
from fava_portfolio_returns.returns.base import ReturnsBase
from fava_portfolio_returns.returns.simple import SimpleReturns
from fava_portfolio_returns.returns.twr import TWR

logger = logging.getLogger(__name__)


@dataclass
class DetailedDataPoint:
    date: datetime.date
    market: float
    cost: float
    cash: float
    simple_return: float
    twr: float

class DetailedTableReturns(ReturnsBase):
    """
    Returns detailed data points containing market value, cost, cash, simple returns, and TWR
    for each portfolio value date. This provides comprehensive information for detailed tables.
    """

    def series(
        self, p: FilteredPortfolio, start_date: datetime.date, end_date: datetime.date
    ) -> list[tuple[datetime.date, Union[float, DetailedDataPoint]]]:
        """
        Returns a series of DetailedDataPoint objects containing all relevant portfolio metrics.
        """
        values = portfolio_values(p, start_date, end_date)
        simple_returns = SimpleReturns()
        twr_returns = TWR()

        simple_returns_series = simple_returns.series(p, start_date, end_date)
        twr_returns_series = twr_returns.series(p, start_date, end_date)

        detailed_data = []
        for value, (_, simple_return), (_, twr_return) in zip(values, simple_returns_series, twr_returns_series):
            detailed_point = DetailedDataPoint(
                date=value.date,
                market=float(value.market),
                cost=float(value.cost),
                cash=float(value.cash),
                simple_return=simple_return,
                twr=twr_return,
            )
            detailed_data.append((value.date, detailed_point))

        return detailed_data

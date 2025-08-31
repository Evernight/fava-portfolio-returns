import datetime
import logging
from dataclasses import dataclass
from typing import NamedTuple
from typing import Union

from fava_portfolio_returns.api.portfolio import portfolio_values
from fava_portfolio_returns.core.portfolio import FilteredPortfolio
from fava_portfolio_returns.core.utils import get_prices
from fava_portfolio_returns.returns.factory import RETURN_METHODS
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


class Series(NamedTuple):
    name: str
    data: list[tuple[datetime.date, Union[float, DetailedDataPoint]]]

@dataclass
class DatedSeries:
    name: str
    dates: frozenset[datetime.date]
    data: list[tuple[datetime.date, Union[float, DetailedDataPoint]]]

    def __init__(self, name, data):
        self.name = name
        self.data = data
        self.dates = frozenset(date for date, _ in data)

    def get_performance_starting_at_date(self, date: datetime.date, normalize_to_first_value: bool = False) -> Series:
        start_from = None
        for i, (date, value) in enumerate(self.data):
            if date == date:
                first_value = value
                start_from = i
                break
        performance = []
        for date, value in self.data[start_from:]:
            performance.append((date, value/first_value - 1 if normalize_to_first_value else value - first_value))
        return Series(name=self.name, data=performance)


def compare_chart(
    p: FilteredPortfolio, start_date: datetime.date, end_date: datetime.date, method: str, compare_with: list[str]
):
    if method == "detailed_table":
        return _compare_chart_detailed(p, start_date, end_date, compare_with)

    returns_method = RETURN_METHODS.get(method)
    if not returns_method:
        raise ValueError(f"Invalid method '{method}'")

    group_series: list[DatedSeries] = [DatedSeries(name="Returns", data=returns_method.series(p, start_date, end_date))]
    for group in p.portfolio.investment_groups.groups:
        if group.id in compare_with:
            fp = p.portfolio.filter([group.id], p.target_currency)
            group_series.append(
                DatedSeries(name=f"(GRP) {group.name}", data=returns_method.series(fp, start_date, end_date))
            )

    account_series: list[DatedSeries] = []
    for account in p.portfolio.investment_groups.accounts:
        if account.id in compare_with:
            fp = p.portfolio.filter([account.id], p.target_currency)
            account_series.append(
                DatedSeries(name=f"(ACC) {account.assetAccount}", data=returns_method.series(fp, start_date, end_date))
            )

    price_series: list[DatedSeries] = []
    for currency in p.portfolio.investment_groups.currencies:
        if currency.id in compare_with:
            prices = get_prices(p.pricer, (currency.currency, p.target_currency))
            prices_filtered = [(date, float(value)) for date, value in prices if start_date <= date <= end_date]
            price_series.append(DatedSeries(name=f"{currency.name} ({currency.currency})", data=prices_filtered))

    # find first common date
    common_date = None
    for date in sorted(group_series[0].dates):
        if all(date in s.dates for s in group_series[1:]) and all(date in s.dates for s in price_series) and all(date in s.dates for s in account_series):
            common_date = date
            break
    else:
        raise ValueError("No overlapping start date found for the selected series.")
    
    for group_serie in group_series:
        group_serie.data = group_serie.get_performance_starting_at_date(common_date)
    for price_serie in price_series:
        price_serie.data = price_serie.get_performance_starting_at_date(common_date, normalize_to_first_value=True)
    for account_serie in account_series:
        account_serie.data = account_serie.get_performance_starting_at_date(common_date)

    return group_series + price_series + account_series


def _compare_chart_detailed(
    p: FilteredPortfolio, start_date: datetime.date, end_date: datetime.date, compare_with: list[str]
):
    """Generate detailed data points for the main portfolio and comparison groups."""

    def create_detailed_series(portfolio: FilteredPortfolio, name: str) -> DatedSeries:
        values = portfolio_values(portfolio, start_date, end_date)
        simple_returns = SimpleReturns()
        twr_returns = TWR()

        simple_returns_series = simple_returns.series(portfolio, start_date, end_date)
        twr_returns_series = twr_returns.series(portfolio, start_date, end_date)

        detailed_data = []
        for value, simple_return, twr_return in zip(values, simple_returns_series, twr_returns_series):
            detailed_data.append(
                DetailedDataPoint(
                    date=value.date,
                    market=float(value.market),
                    cost=float(value.cost),
                    cash=float(value.cash),
                    simple_return=simple_return,
                    twr=twr_return,
                )
            )

        return DatedSeries(name=name, data=[(dp.date, dp) for dp in detailed_data])

    # Main portfolio series
    group_series: list[DatedSeries] = [create_detailed_series(p, "Returns")]

    # Group series
    for group in p.portfolio.investment_groups.groups:
        if group.id in compare_with:
            fp = p.portfolio.filter([group.id], p.target_currency)
            group_series.append(create_detailed_series(fp, f"(GRP) {group.name}"))

    # Account series
    account_series: list[DatedSeries] = []
    for account in p.portfolio.investment_groups.accounts:
        if account.id in compare_with:
            fp = p.portfolio.filter([account.id], p.target_currency)
            account_series.append(create_detailed_series(fp, f"(ACC) {account.assetAccount}"))

    # find first common date
    common_date = None
    for date in sorted(group_series[0].dates):
        if all(date in s.dates for s in group_series[1:]) and all(date in s.dates for s in account_series):
            common_date = date
            break
    else:
        raise ValueError("No overlapping start date found for the selected series.")

    # cut off data before common date
    for group_serie in group_series:
        for i, (date, _) in enumerate(group_serie.data):
            if date == common_date:
                group_serie.data = group_serie.data[i:]
                break
    for account_serie in account_series:
        for i, (date, _) in enumerate(account_serie.data):
            if date == common_date:
                account_serie.data = account_serie.data[i:]
                break

    # Return series with detailed data points
    series: list[Series] = []
    for group_serie in group_series:
        series.append(Series(name=group_serie.name, data=group_serie.data))
    for account_serie in account_series:
        series.append(Series(name=account_serie.name, data=account_serie.data))

    return series

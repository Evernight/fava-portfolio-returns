import datetime
import logging
from dataclasses import dataclass
from typing import NamedTuple
from typing import Union

from fava_portfolio_returns.core.portfolio import FilteredPortfolio
from fava_portfolio_returns.core.utils import get_prices
from fava_portfolio_returns.returns.detailed_table import DetailedDataPoint
from fava_portfolio_returns.returns.factory import RETURN_METHODS

logger = logging.getLogger(__name__)


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
            if isinstance(value, DetailedDataPoint):
                if normalize_to_first_value:
                    new_value = DetailedDataPoint(
                    date=date,
                    market=value.market,
                    cost=value.cost,
                    cash=value.cash,
                    simple_return=value.simple_return - first_value.simple_return,
                    twr=value.twr/first_value.twr - 1.0)
                else:
                    new_value = DetailedDataPoint(
                    date=date,
                    market=value.market,
                    cost=value.cost,
                    cash=value.cash,
                    simple_return=value.simple_return - first_value.simple_return,
                    twr=value.twr - first_value.twr)
                performance.append((date, new_value))
            else:
                performance.append((date, value/first_value - 1 if normalize_to_first_value else value - first_value))
        return Series(name=self.name, data=performance)


def compare_chart(
    p: FilteredPortfolio, start_date: datetime.date, end_date: datetime.date, method: str, compare_with: list[str]
):
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
            if method == "detailed_table":
                prices_filtered = [(date, DetailedDataPoint(date=date, market=float(value), cost=0.0, cash=float(value), simple_return=float(value), twr=float(value))) for date, value in prices_filtered]
            price_series.append(DatedSeries(name=f"{currency.name} ({currency.currency})", data=prices_filtered))

    # find first common date
    common_date = None
    for date in sorted(group_series[0].dates):
        if all(date in s.dates for s in group_series[1:]) and all(date in s.dates for s in price_series) and all(date in s.dates for s in account_series):
            common_date = date
            break
    else:
        raise ValueError("No overlapping start date found for the selected series.")
    
    series: list[Series] = []
    for group_serie in group_series:
        series.append(group_serie.get_performance_starting_at_date(common_date))
    for price_serie in price_series:
        series.append(price_serie.get_performance_starting_at_date(common_date, normalize_to_first_value=True))
    for account_serie in account_series:
        series.append(account_serie.get_performance_starting_at_date(common_date))

    return series

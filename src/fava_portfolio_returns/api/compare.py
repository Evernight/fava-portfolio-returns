import datetime
import logging
from dataclasses import dataclass
from typing import NamedTuple

from fava_portfolio_returns.api.portfolio import portfolio_values
from fava_portfolio_returns.core.portfolio import FilteredPortfolio
from fava_portfolio_returns.core.utils import get_prices
from fava_portfolio_returns.returns.factory import RETURN_METHODS

logger = logging.getLogger(__name__)


@dataclass
class DetailedDataPoint:
    date: datetime.date
    market: float
    cost: float
    cash: float
    simple_return: float
    twr: float

@dataclass
class DatedSeries:
    name: str
    dates: frozenset[datetime.date]
    data: list[tuple[datetime.date, float]]

    def __init__(self, name, data):
        self.name = name
        self.data = data
        self.dates = frozenset(date for date, _ in data)

@dataclass
class DetailedDatedSeries:
    name: str
    dates: frozenset[datetime.date]
    data: list[DetailedDataPoint]

    def __init__(self, name, data):
        self.name = name
        self.data = data
        self.dates = frozenset(point.date for point in data)


class Series(NamedTuple):
    name: str
    data: list[tuple[datetime.date, float]]

class DetailedSeries(NamedTuple):
    name: str
    data: list[DetailedDataPoint]


def compare_chart(
    p: FilteredPortfolio, start_date: datetime.date, end_date: datetime.date, method: str, compare_with: list[str]
):
    returns_method = RETURN_METHODS.get(method)
    if not returns_method:
        raise ValueError(f"Invalid method {method}")

    group_series: list[DatedSeries] = [DatedSeries(name="Returns", data=returns_method.series(p, start_date, end_date))]
    for group in p.portfolio.investment_groups.groups:
        if group.id in compare_with:
            fp = p.portfolio.filter([group.id], p.target_currency)
            group_series.append(
                DatedSeries(name=f"(GRP) {group.name}", data=returns_method.series(fp, start_date, end_date))
            )

    price_series: list[DatedSeries] = []
    for currency in p.portfolio.investment_groups.currencies:
        if currency.id in compare_with:
            prices = get_prices(p.pricer, (currency.currency, p.target_currency))
            prices_filtered = [(date, float(value)) for date, value in prices if start_date <= date <= end_date]
            price_series.append(DatedSeries(name=f"{currency.name} ({currency.currency})", data=prices_filtered))

    account_series: list[DatedSeries] = []
    for account in p.portfolio.investment_groups.accounts:
        if account.id in compare_with:
            fp = p.portfolio.filter([account.id], p.target_currency)
            account_series.append(
                DatedSeries(name=f"(ACC) {account.assetAccount}", data=returns_method.series(fp, start_date, end_date))
            )

    # find first common date
    common_date = None
    for date in sorted(group_series[0].dates):
        if all(date in s.dates for s in group_series[1:]) and all(date in s.dates for s in price_series):
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
    for price_serie in price_series:
        for i, (date, _) in enumerate(price_serie.data):
            if date == common_date:
                price_serie.data = price_serie.data[i:]
                break
    for account_serie in account_series:
        for i, (date, _) in enumerate(account_serie.data):
            if date == common_date:
                account_serie.data = account_serie.data[i:]
                break

    # compute performance relative to first data point
    series: list[Series] = []
    for group_serie in group_series:
        first_return = group_serie.data[0][1]
        performance = [(date, returns - first_return) for date, returns in group_serie.data]
        series.append(Series(name=group_serie.name, data=performance))
    for price_serie in price_series:
        first_price = price_serie.data[0][1]
        performance = [(date, float(price / first_price - 1)) for date, price in price_serie.data]
        series.append(Series(name=price_serie.name, data=performance))
    for account_serie in account_series:
        first_return = account_serie.data[0][1]
        performance = [(date, returns - first_return) for date, returns in account_serie.data]
        series.append(Series(name=account_serie.name, data=performance))

    return series


def _create_detailed_data_for_portfolio(
    p: FilteredPortfolio, start_date: datetime.date, end_date: datetime.date, name: str
) -> DetailedDatedSeries:
    """Helper function to create detailed data for a portfolio"""
    simple_method = RETURN_METHODS["simple"]
    twr_method = RETURN_METHODS["twr"]
    
    portfolio_vals = portfolio_values(p, start_date, end_date)
    simple_returns = dict(simple_method.series(p, start_date, end_date))
    twr_returns = dict(twr_method.series(p, start_date, end_date))
    
    data = []
    for pv in portfolio_vals:
        if pv.date in simple_returns and pv.date in twr_returns:
            data.append(DetailedDataPoint(
                date=pv.date,
                market=float(pv.market),
                cost=float(pv.cost),
                cash=float(pv.cash),
                simple_return=simple_returns[pv.date],
                twr=twr_returns[pv.date]
            ))
    
    return DetailedDatedSeries(name=name, data=data)


def compare_chart_detailed(
    p: FilteredPortfolio, start_date: datetime.date, end_date: datetime.date, compare_with: list[str]
) -> list[DetailedSeries]:
    """Returns detailed comparison data with portfolio values and multiple return calculations"""
    
    # Reuse the logic from compare_chart to get the regular series with proper normalization
    regular_series = compare_chart(p, start_date, end_date, "simple", compare_with)
    
    # Now create detailed series for the same portfolios that were selected
    all_detailed_series: list[DetailedDatedSeries] = []
    
    # Main portfolio
    main_detailed = _create_detailed_data_for_portfolio(p, start_date, end_date, "Returns")
    all_detailed_series.append(main_detailed)
    
    # Add comparison groups
    for group in p.portfolio.investment_groups.groups:
        if group.id in compare_with:
            fp = p.portfolio.filter([group.id], p.target_currency)
            group_detailed = _create_detailed_data_for_portfolio(fp, start_date, end_date, f"(GRP) {group.name}")
            all_detailed_series.append(group_detailed)
    
    # Add comparison currencies (price series) - these don't have portfolio values
    for currency in p.portfolio.investment_groups.currencies:
        if currency.id in compare_with:
            prices = get_prices(p.pricer, (currency.currency, p.target_currency))
            prices_filtered = [(date, float(value)) for date, value in prices if start_date <= date <= end_date]
            
            currency_data = []
            if prices_filtered:
                first_price = prices_filtered[0][1]
                for date, price in prices_filtered:
                    price_return = float(price / first_price - 1)
                    currency_data.append(DetailedDataPoint(
                        date=date,
                        market=0.0,  # No portfolio values for currency comparisons
                        cost=0.0,
                        cash=0.0,
                        simple_return=price_return,
                        twr=price_return
                    ))
            
            all_detailed_series.append(DetailedDatedSeries(name=f"{currency.name} ({currency.currency})", data=currency_data))
    
    # Add comparison accounts
    for account in p.portfolio.investment_groups.accounts:
        if account.id in compare_with:
            fp = p.portfolio.filter([account.id], p.target_currency)
            account_detailed = _create_detailed_data_for_portfolio(fp, start_date, end_date, f"(ACC) {account.assetAccount}")
            all_detailed_series.append(account_detailed)
    
    # Find the common date by using the regular series (which already has this logic)
    if not regular_series or not all_detailed_series:
        return []
    
    # Get the first date from the regular series (which is already normalized)
    first_regular_date = regular_series[0].data[0][0]
    
    # Apply the same date filtering and normalization to detailed series
    final_series: list[DetailedSeries] = []
    for detailed_serie in all_detailed_series:
        # Filter data to start from the same date as regular series
        filtered_data = [dp for dp in detailed_serie.data if dp.date >= first_regular_date]
        
        if not filtered_data:
            continue
            
        # Normalize to start from 0 (same as regular series)
        first_point = filtered_data[0]
        first_simple = first_point.simple_return
        first_twr = first_point.twr
        
        normalized_data = []
        for dp in filtered_data:
            normalized_data.append(DetailedDataPoint(
                date=dp.date,
                market=dp.market,
                cost=dp.cost,
                cash=dp.cash,
                simple_return=dp.simple_return - first_simple,
                twr=dp.twr - first_twr
            ))
        
        final_series.append(DetailedSeries(name=detailed_serie.name, data=normalized_data))
    
    return final_series

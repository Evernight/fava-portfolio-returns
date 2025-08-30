import { Alert, Box } from "@mui/material";
import { createEnumParam, useQueryParam, withDefault } from "use-query-params";
import { useCompare } from "../api/compare";
import { Dashboard, DashboardRow, Panel } from "../components/Dashboard";
import { DisplayMethodSelection, DisplayMethod } from "../components/DisplayMethodSelection";
import { EChart } from "../components/EChart";
import { useToolbarContext } from "../components/Header/ToolbarProvider";
import { InvestmentsSelection } from "../components/InvestmentsSelection";
import { Loading } from "../components/Loading";
import { PerformanceDataGrid } from "../components/PerformanceDataGrid";
import { ReturnsMethodSelection } from "../components/ReturnsMethodSelection";
import { percentFormatter } from "../components/format";
import { CommaArrayParam } from "../components/query_params";

const ReturnsMethodEnum = createEnumParam(["simple", "twr"]);
const ReturnsMethodParam = withDefault(ReturnsMethodEnum, "simple" as const);
const DisplayMethodEnum = createEnumParam(["chart", "table"]);
const DisplayMethodParam = withDefault(DisplayMethodEnum, "chart" as const);
const InvestmentsParam = withDefault(CommaArrayParam, []);

export function Performance() {
  const [method, setMethod] = useQueryParam("method", ReturnsMethodParam);
  const [displayMethod, setDisplayMethod] = useQueryParam("display", DisplayMethodParam);
  const [_investments, setInvestments] = useQueryParam("compareWith", InvestmentsParam);
  const investments = _investments.filter((i) => i !== null) as string[];

  return (
    <Dashboard>
      <DashboardRow>
        <Panel
          title="Performance"
          help={`The performance chart compares the relative performance of the currently selected investments with other groups and commodities.`}
          topRightElem={
            <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
              <ReturnsMethodSelection options={["simple", "twr"]} method={method} setMethod={setMethod} />
              <DisplayMethodSelection method={displayMethod} setMethod={setDisplayMethod} />
            </Box>
          }
        >
          <PerformanceChart method={method} investments={investments} displayMethod={displayMethod} />
          <Box sx={{ display: "flex", justifyContent: "center", marginTop: 3 }}>
            <InvestmentsSelection
              label="Compare with"
              types={["Group", "Currency", "Account"]}
              investments={investments}
              setInvestments={setInvestments}
            />
          </Box>
        </Panel>
      </DashboardRow>
    </Dashboard>
  );
}

interface PerformanceChartProps {
  method: string;
  investments: string[];
  displayMethod: DisplayMethod;
}

function PerformanceChart({ method, investments, displayMethod }: PerformanceChartProps) {
  const { investmentFilter, targetCurrency } = useToolbarContext();
  const { isPending, error, data } = useCompare({
    investmentFilter,
    targetCurrency,
    method,
    compareWith: investments,
  });

  if (isPending) {
    return <Loading />;
  }
  if (error) {
    return <Alert severity="error">{error.message}</Alert>;
  }

  if (displayMethod === "table") {
    return <PerformanceDataGrid series={data.series} />;
  }

  const option = {
    tooltip: {
      trigger: "axis",
      valueFormatter: percentFormatter,
    },
    legend: {
      bottom: 0,
    },
    grid: {
      left: 100,
    },
    xAxis: {
      type: "time",
    },
    yAxis: {
      type: "value",
      axisLabel: {
        formatter: percentFormatter,
      },
    },
    series: data.series.map((serie) => ({
      type: "line",
      showSymbol: false,
      name: serie.name,
      data: serie.data,
    })),
  };

  return <EChart height="400px" option={option} />;
}

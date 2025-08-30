import { useQuery, UseQueryResult } from "@tanstack/react-query";
import { fetchJSON } from "./api";

interface CompareRequest {
  investmentFilter: string[];
  targetCurrency: string;
  method: string;
  compareWith: string[];
  detailed?: boolean;
}

interface Serie {
  name: string;
  data: [string, number][];
}

export interface DetailedDataPoint {
  date: string;
  market: number;
  cost: number;
  cash: number;
  simple_return: number;
  twr: number;
}

interface DetailedSerie {
  name: string;
  data: DetailedDataPoint[];
}

export interface CompareResponse {
  series: Serie[];
}

export interface DetailedCompareResponse {
  series: DetailedSerie[];
}

export function useCompare(request: CompareRequest): UseQueryResult<CompareResponse> {
  const params = new URLSearchParams(location.search); // keep Fava's filters like ?time=...
  params.set("investments", request.investmentFilter.join(","));
  params.set("currency", request.targetCurrency);
  params.set("method", request.method);
  params.set("compareWith", request.compareWith.join(","));
  if (request.detailed) {
    params.set("detailed", "true");
  }
  const url = `compare?${params}`;

  return useQuery({
    queryKey: [url],
    queryFn: () => fetchJSON<CompareResponse>(url),
  });
}

export function useDetailedCompare(request: Omit<CompareRequest, 'method'>): UseQueryResult<DetailedCompareResponse> {
  const params = new URLSearchParams(location.search); // keep Fava's filters like ?time=...
  params.set("investments", request.investmentFilter.join(","));
  params.set("currency", request.targetCurrency);
  params.set("compareWith", request.compareWith.join(","));
  params.set("detailed", "true");
  const url = `compare?${params}`;

  return useQuery({
    queryKey: [url],
    queryFn: () => fetchJSON<DetailedCompareResponse>(url),
  });
}

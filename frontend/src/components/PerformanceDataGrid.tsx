import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { percentFormatter } from './format';

interface Serie {
  name: string;
  data: [string, number][];
}

interface PerformanceDataGridProps {
  series: Serie[];
}

interface GridRow {
  id: string;
  investment: string;
  [date: string]: string | number;
}

export function PerformanceDataGrid({ series }: PerformanceDataGridProps) {
  if (!series || series.length === 0) {
    return <div>No data available</div>;
  }

  // Get all unique dates from all series
  const allDates = new Set<string>();
  series.forEach(serie => {
    serie.data.forEach(([date]) => {
      allDates.add(date);
    });
  });
  
  const sortedDates = Array.from(allDates).sort();

  // Transform data into rows for DataGrid
  const rows: GridRow[] = series.map(serie => {
    const row: GridRow = {
      id: serie.name,
      investment: serie.name,
    };
    
    // Create a map for quick lookup of values by date
    const dataMap = new Map(serie.data);
    
    // Fill in values for each date
    sortedDates.forEach(date => {
      const value = dataMap.get(date);
      row[date] = value !== undefined ? value : '';
    });
    
    return row;
  });

  // Create column definitions
  const columns: GridColDef[] = [
    {
      field: 'investment',
      headerName: 'Investment',
      width: 200,
    },
    ...sortedDates.map(date => ({
      field: date,
      headerName: new Date(date).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
      }),
      width: 120,
      type: 'number' as const,
      valueFormatter: (value: number | string) => {
        if (typeof value === 'number') {
          return percentFormatter(value);
        }
        return value;
      },
    }))
  ];

  return (
    <div style={{ height: 400, width: '100%' }}>
      <DataGrid
        rows={rows}
        columns={columns}
        disableRowSelectionOnClick
        disableColumnFilter
        hideFooter
        sx={{
          '& .MuiDataGrid-columnHeader': {
            backgroundColor: 'rgba(0, 0, 0, 0.04)',
          },
        }}
      />
    </div>
  );
}

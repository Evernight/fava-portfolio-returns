import { Box, Chip } from '@mui/material';
import { DataGrid, GridColDef, GridRowClassNameParams } from '@mui/x-data-grid';
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
  color: string;
  [date: string]: string | number;
}

// Color palette for different investments
const COLOR_PALETTE = [
  '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
  '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
  '#aec7e8', '#ffbb78', '#98df8a', '#ff9896', '#c5b0d5',
  '#c49c94', '#f7b6d3', '#c7c7c7', '#dbdb8d', '#9edae5'
];

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
  const rows: GridRow[] = series.map((serie, index) => {
    const color = COLOR_PALETTE[index % COLOR_PALETTE.length];
    const row: GridRow = {
      id: serie.name,
      investment: serie.name,
      color: color,
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
      renderCell: (params) => (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Box
            sx={{
              width: 12,
              height: 12,
              backgroundColor: params.row.color,
              borderRadius: '50%',
            }}
          />
          {params.value}
        </Box>
      ),
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
      renderCell: (params) => {
        if (typeof params.value === 'number') {
          return (
            <Box sx={{ color: params.row.color, fontWeight: 'bold' }}>
              {percentFormatter(params.value)}
            </Box>
          );
        }
        return params.value;
      },
    }))
  ];

  return (
    <Box sx={{ width: '100%' }}>
      {/* Legend */}
      <Box sx={{ mb: 2, display: 'flex', flexWrap: 'wrap', gap: 1 }}>
        {rows.map((row) => (
          <Chip
            key={row.id}
            label={row.investment}
            sx={{
              backgroundColor: row.color,
              color: 'white',
              fontWeight: 'bold',
              '& .MuiChip-label': {
                fontSize: '0.875rem',
              },
            }}
          />
        ))}
      </Box>
      
      {/* DataGrid */}
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
            '& .MuiDataGrid-virtualScroller': {
              overflowX: 'scroll !important',
            },
          }}
        />
      </div>
    </Box>
  );
}

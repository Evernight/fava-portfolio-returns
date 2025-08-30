import { MenuItem, Select } from "@mui/material";

export const DisplayMethods = {
  chart: { label: "Chart" },
  table: { label: "Table" },
};

export type DisplayMethod = keyof typeof DisplayMethods;

interface DisplayMethodSelectionProps {
  method: DisplayMethod;
  setMethod: (method: DisplayMethod) => void;
}

export function DisplayMethodSelection({
  method,
  setMethod,
}: DisplayMethodSelectionProps) {
  return (
    <Select 
      value={method} 
      onChange={(e) => setMethod(e.target.value as DisplayMethod)} 
      displayEmpty 
      size="small"
    >
      {Object.entries(DisplayMethods).map(([key, value]) => (
        <MenuItem key={key} value={key}>
          {value.label}
        </MenuItem>
      ))}
    </Select>
  );
}

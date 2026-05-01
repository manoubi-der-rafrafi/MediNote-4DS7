

interface HeatmapGridProps {
  values: number[];
  names: string[];
}

export function HeatmapGrid({ values, names }: HeatmapGridProps) {
  const getColor = (val: number) => {
    if (val > 80) return '#2C2C2A';
    if (val > 60) return '#5F5E5A';
    if (val > 40) return '#8F8E8A';
    if (val > 20) return '#D3D1C7';
    return '#F1EFE8';
  };

  const getTextColor = (val: number) => {
    return val > 60 ? '#ffffff' : '#1F1F1D';
  };

  return (
    <div className="bg-card border border-line rounded-lg p-5">
      <h3 className="text-lg font-semibold text-ink mb-4">Gouvernorate Heatmap</h3>
      <div className="grid grid-cols-6 gap-2">
        {values.map((val, idx) => (
          <div
            key={idx}
            className="aspect-square rounded flex flex-col items-center justify-center text-center cursor-pointer hover:shadow-md transition-shadow"
            style={{
              backgroundColor: getColor(val),
              color: getTextColor(val),
            }}
            title={names[idx]}
          >
            <div className="text-xs font-bold">{val}</div>
            <div className="text-xs mt-1">{names[idx]}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

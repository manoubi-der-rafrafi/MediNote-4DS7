import { Pill } from './Pill';

interface AnimationRow {
  id: number;
  code: string;
  name: string;
  roi: number;
  budget: string;
  invested: string;
  mouvementFort: number;
  pStrong: number;
  verdict: 'strong' | 'weak' | 'pending';
}

interface AnimationTableProps {
  rows: AnimationRow[];
}

export function AnimationTable({ rows }: AnimationTableProps) {
  return (
    <div className="bg-card border border-line rounded-lg overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-line bg-gray-50">
              <th className="px-4 py-3 text-left text-label">Code</th>
              <th className="px-4 py-3 text-left text-label">Name</th>
              <th className="px-4 py-3 text-right text-label">ROI</th>
              <th className="px-4 py-3 text-right text-label">Budget</th>
              <th className="px-4 py-3 text-right text-label">Invested</th>
              <th className="px-4 py-3 text-right text-label">Mouvement fort %</th>
              <th className="px-4 py-3 text-right text-label">P(strong)</th>
              <th className="px-4 py-3 text-center text-label">Verdict</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.id} className="border-b border-line hover:bg-gray-50">
                <td className="px-4 py-3 font-mono text-xs">{row.code}</td>
                <td className="px-4 py-3">{row.name}</td>
                <td className="px-4 py-3 text-right font-semibold">{row.roi.toFixed(2)}×</td>
                <td className="px-4 py-3 text-right">{row.budget}</td>
                <td className="px-4 py-3 text-right">{row.invested}</td>
                <td className="px-4 py-3 text-right">{row.mouvementFort}%</td>
                <td className="px-4 py-3 text-right">{row.pStrong.toFixed(2)}</td>
                <td className="px-4 py-3 text-center">
                  <Pill
                    variant={row.verdict === 'strong' ? 'ok' : row.verdict === 'weak' ? 'bad' : 'info'}
                    text={row.verdict}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

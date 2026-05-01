import React, { useState, useMemo } from 'react';
import { animData } from '../data/animData';
import { Pill } from './Pill';
import { MiniBar } from './MiniBar';

export const AnimSearchTable: React.FC = () => {
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [verdictFilter, setVerdictFilter] = useState('');

  const filtered = useMemo(() => {
    return animData.filter((anim) => {
      const matchSearch = anim.name.toLowerCase().includes(search.toLowerCase());
      const matchType = !typeFilter || anim.type === typeFilter;
      const matchVerdict = !verdictFilter || anim.verdict === verdictFilter;
      return matchSearch && matchType && matchVerdict;
    });
  }, [search, typeFilter, verdictFilter]);

  return (
    <div className="bg-card border border-line rounded-lg p-5">
      <h3 className="text-lg font-semibold text-ink mb-4">32 Animations</h3>

      {/* Filters */}
      <div className="flex gap-3 mb-4">
        <input
          type="text"
          placeholder="Search..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="px-3 py-2 border border-line rounded text-sm"
        />
        <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)} className="px-3 py-2 border border-line rounded text-sm">
          <option value="">All Types</option>
          <option value="Training">Training</option>
          <option value="Event">Event</option>
          <option value="PLV">PLV</option>
          <option value="Digital">Digital</option>
          <option value="Promo">Promo</option>
          <option value="Contest">Contest</option>
        </select>
        <select value={verdictFilter} onChange={(e) => setVerdictFilter(e.target.value)} className="px-3 py-2 border border-line rounded text-sm">
          <option value="">All Verdicts</option>
          <option value="Keep">Keep</option>
          <option value="Watch">Watch</option>
          <option value="Drop">Drop</option>
        </select>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-line">
              <th className="text-left py-2 px-2 text-xs font-semibold text-mute">#</th>
              <th className="text-left py-2 px-2 text-xs font-semibold text-mute">Animation</th>
              <th className="text-left py-2 px-2 text-xs font-semibold text-mute">Type</th>
              <th className="text-right py-2 px-2 text-xs font-semibold text-mute">Budget</th>
              <th className="text-right py-2 px-2 text-xs font-semibold text-mute">Inv.</th>
              <th className="text-center py-2 px-2 text-xs font-semibold text-mute">MF%</th>
              <th className="text-center py-2 px-2 text-xs font-semibold text-mute">Sentiment</th>
              <th className="text-right py-2 px-2 text-xs font-semibold text-mute">P(strong)</th>
              <th className="text-center py-2 px-2 text-xs font-semibold text-mute">Verdict</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((anim) => (
              <tr key={anim.id} className="border-b border-line/50 hover:bg-gray-50">
                <td className="py-2 px-2 text-xs text-mute font-mono">{anim.id + 1}</td>
                <td className="py-2 px-2 font-medium">{anim.name}</td>
                <td className="py-2 px-2 text-xs">{anim.type}</td>
                <td className="py-2 px-2 text-right font-semibold">{anim.budget}K</td>
                <td className="py-2 px-2 text-right">{anim.invested}K</td>
                <td className="py-2 px-2 text-center">
                  <MiniBar percent={anim.movementFort} color="bg-brand" />
                </td>
                <td className="py-2 px-2 text-center">
                  <Pill variant={anim.sentiment.includes('-') ? 'bad' : anim.sentiment.includes('+') ? 'ok' : 'warn'} text={anim.sentiment} />
                </td>
                <td className="py-2 px-2 text-right font-semibold">{anim.pStrong}</td>
                <td className="py-2 px-2 text-center">
                  <Pill
                    variant={anim.verdict === 'Keep' ? 'ok' : anim.verdict === 'Watch' ? 'info' : 'warn'}
                    text={anim.verdict}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

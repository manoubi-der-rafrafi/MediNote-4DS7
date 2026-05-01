// Page: Segments — App: Marketing — API: /api/v1/marketing/segments
import React, { useState } from 'react';
import { PageHeader } from '../components/ui/PageHeader';
import { RingChart } from '../components/ui/RingChart';
import { CustomPieChart } from '../components/ui/CustomPieChart';
import { DataTable, DataTableColumn } from '../components/ui/DataTable';
import { Badge } from '../components/ui/Badge';

interface Entity {
  id: string;
  name: string;
  segment: string;
  score: number;
  delegate: string;
  action: string;
  type: 'medecin' | 'pharmacie';
}

const mockMedecinsSegments = [
  { name: 'HIGH_POTENTIAL', count: 105, percentage: 25 },
  { name: 'LOYAL', count: 168, percentage: 40 },
  { name: 'AT_RISK', count: 84, percentage: 20 },
  { name: 'DORMANT', count: 63, percentage: 15 },
];

const mockPharmaciesSegments = [
  { name: 'ADVOCATE', count: 35, percentage: 23 },
  { name: 'HIGH_OPP', count: 52, percentage: 35 },
  { name: 'LOYAL', count: 42, percentage: 28 },
  { name: 'URGENT', count: 21, percentage: 14 },
];

const mockEntities: Entity[] = [
  { id: '1', name: 'Dr. Ahmed Bennani', segment: 'LOYAL', score: 87, delegate: 'Mohammed', action: 'Maintien', type: 'medecin' },
  { id: '2', name: 'Dr. Fatima Kara', segment: 'HIGH_POTENTIAL', score: 92, delegate: 'Sofia', action: 'Activité', type: 'medecin' },
  { id: '3', name: 'Pharmacie Al Azhar', segment: 'ADVOCATE', score: 95, delegate: 'Hassan', action: 'Partenariat', type: 'pharmacie' },
];

const getSegmentColor = (segment: string): string => {
  const colorMap: Record<string, string> = {
    HIGH_POTENTIAL: 'gold',
    LOYAL: 'teal',
    AT_RISK: 'orange',
    DORMANT: 'gray',
    ADVOCATE: 'teal',
    HIGH_OPP: 'gold',
    URGENT: 'red',
  };
  return colorMap[segment] || 'blue';
};

export const SegmentsPage: React.FC = () => {
  const [viewType, setViewType] = useState<'medecins' | 'pharmacies'>('medecins');
  const [filteredEntities, setFilteredEntities] = useState(mockEntities.filter(e => e.type === 'medecin'));

  const handleToggle = (type: 'medecins' | 'pharmacies') => {
    setViewType(type);
    setFilteredEntities(mockEntities.filter(e => e.type === (type === 'medecins' ? 'medecin' : 'pharmacie')));
  };

  const segments = viewType === 'medecins' ? mockMedecinsSegments : mockPharmaciesSegments;
  const title = viewType === 'medecins' ? '420 médecins · 4 segments' : '150 pharmacies · 4 segments';

  const columns: DataTableColumn<Entity>[] = [
    { key: 'name', label: 'Entité' },
    {
      key: 'segment',
      label: 'Segment',
      render: (v: string) => <Badge variant={`tier-${getSegmentColor(v).toLowerCase()}` as any}>{v}</Badge>,
    },
    {
      key: 'score',
      label: 'Score',
      render: (v: number) => (
        <div className="flex items-center gap-2">
          <div className="w-12 h-2 bg-s3 rounded-full overflow-hidden">
            <div className="h-full bg-marketing" style={{ width: `${(v / 100) * 100}%` }} />
          </div>
          <span className="text-sm">{v}</span>
        </div>
      ),
    },
    { key: 'delegate', label: 'Délégué' },
    { key: 'action', label: 'Action recommandée' },
  ];

  return (
    <div>
      <PageHeader
        title="Segmentation"
        subtitle="Clustering K-Means · Nb03"
        action={{
          label: 'Recalculer',
          onClick: () => alert('Recalcul lancé'),
        }}
      />

      {/* View Toggle */}
      <div className="flex gap-2 mb-6">
        <button
          onClick={() => handleToggle('medecins')}
          className={`px-4 py-2 rounded-lg font-semibold transition-colors ${
            viewType === 'medecins'
              ? 'bg-marketing text-white'
              : 'bg-s2 text-gray-300 hover:bg-s3'
          }`}
        >
          👨‍⚕️ Médecins
        </button>
        <button
          onClick={() => handleToggle('pharmacies')}
          className={`px-4 py-2 rounded-lg font-semibold transition-colors ${
            viewType === 'pharmacies'
              ? 'bg-marketing text-white'
              : 'bg-s2 text-gray-300 hover:bg-s3'
          }`}
        >
          💊 Pharmacies
        </button>
      </div>

      {/* Segment Display */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold mb-4">{title}</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {segments.map(seg => (
            <div key={seg.name} className="flex justify-center">
              <RingChart
                progress={seg.percentage}
                color={getSegmentColor(seg.name)}
                size={120}
                label={seg.name}
                sublabel={`${seg.count} entités`}
              />
            </div>
          ))}
        </div>

        {/* Pie Chart */}
        <div className="bg-s1 border border-bd rounded-lg p-6 mb-6">
          <CustomPieChart
            data={segments.map(s => ({ name: s.name, value: s.count }))}
            colors={segments.map(s => {
              const colorMap: Record<string, string> = {
                gold: '#FBBF24',
                teal: '#2DD4BF',
                orange: '#FB923C',
                gray: '#6B7280',
                red: '#F87171',
              };
              return colorMap[getSegmentColor(s.name)] || '#4F8EF7';
            })}
          />
        </div>
      </div>

      {/* Details Table */}
      <h3 className="text-lg font-semibold mb-4">Détails</h3>
      <DataTable
        columns={columns}
        data={filteredEntities}
        pageSize={10}
      />
    </div>
  );
};

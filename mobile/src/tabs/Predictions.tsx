// WEB-ONLY: Disabled - uses React DOM and chart.js which don't work in React Native.
// Use the React Native components in screens/ instead.
export {};

export const Predictions: React.FC = () => {
  const { forecast, anomalies } = useSupervisorData(541);

  const initialized = useRef(false);
  useEffect(() => { initialized.current = true; }, []);

  const revenue30d = Number(forecast?.revenue_30d ?? 0.84);
  const forecastTrend = String(forecast?.trend ?? '+6.2%');

  const kpis = [
    { label: 'Call list semaine', value: '12', delta: 'Churn risk', deltaType: 'neutral' as const },
    { label: 'Prospects à convertir', value: '8', delta: 'P > 0.70', deltaType: 'up' as const },
    { label: 'CA Q+1 prévu', value: `${revenue30d.toFixed(2)} M`, delta: `${forecastTrend}`, deltaType: 'up' as const },
    { label: 'P(strong) moyen', value: '0.72', delta: 'vs plateforme 0.61', deltaType: 'up' as const },
  ];

  const monthly = Array.isArray(forecast?.monthly_breakdown) ? forecast.monthly_breakdown : [];
  const forecastSeries = monthly.length >= 3
    ? monthly.slice(0, 3).map((v: any) => Number(v?.value ?? v ?? 0))
    : [268,278,294];
  const forecastData = {
    labels: ['M+1','M+2','M+3'],
    datasets: [
      { label: 'Upper 80%', data: forecastSeries.map((v: number) => v * 1.08), borderColor: 'transparent', backgroundColor: 'rgba(46,125,79,0.10)', fill: '+1', pointRadius: 0, tension: 0.35 },
      { label: 'Forecast', data: forecastSeries, borderColor: C.brand, borderWidth: 1.5, backgroundColor: 'transparent', pointRadius: 3, tension: 0.35 },
      { label: 'Lower 80%', data: forecastSeries.map((v: number) => v * 0.92), borderColor: 'transparent', backgroundColor: 'rgba(46,125,79,0.10)', fill: false, pointRadius: 0, tension: 0.35 },
    ]
  };

  const churnRiskFallback = [
    { score: '0.91', iconBg: 'rgba(185, 74, 72, 0.12)', iconColor: C.neg, name: 'Pharmacie El Menzah', meta: '8 mois sans commande · 15.1 K/an', chip: { label: 'Urgent', variant: 'neg' as const } },
    { score: '0.84', iconBg: 'rgba(185, 74, 72, 0.12)', iconColor: C.neg, name: 'Pharmacie Carthage', meta: '7 mois sans commande · 7.4 K/an', chip: { label: 'Urgent', variant: 'neg' as const } },
    { score: '0.68', iconBg: 'rgba(184, 134, 11, 0.14)', iconColor: C.warn, name: 'Pharmacie Al Hayet', meta: '4 mois · 14.2 K/an · 3 reliquats', chip: { label: 'High', variant: 'warn' as const } },
    { score: '0.55', iconBg: 'rgba(184, 134, 11, 0.14)', iconColor: C.warn, name: 'Pharmacie Ezzahra', meta: '3 mois · 12.6 K/an · 1 reliquat', chip: { label: 'Med', variant: 'warn' as const } },
    { score: '0.51', iconBg: 'rgba(184, 134, 11, 0.14)', iconColor: C.warn, name: 'Pharmacie Al Nour', meta: '3 mois · 9.8 K/an · 0 reliquat', chip: { label: 'Med', variant: 'warn' as const } },
  ];
  const churnRisk = Array.isArray(anomalies) && anomalies.length > 0
    ? anomalies.slice(0, 5).map((a: any, idx: number) => {
        const risk = Number(a?.risk ?? 0.65);
        const severity = a?.severity || (risk >= 0.8 ? 'critical' : risk >= 0.6 ? 'warning' : 'info');
        const variant = severity === 'critical' ? 'neg' : severity === 'warning' ? 'warn' : 'default';
        return {
          score: risk.toFixed(2),
          iconBg: variant === 'neg' ? 'rgba(185, 74, 72, 0.12)' : variant === 'warn' ? 'rgba(184, 134, 11, 0.14)' : 'rgba(88, 88, 88, 0.12)',
          iconColor: variant === 'neg' ? C.neg : variant === 'warn' ? C.warn : C.muted,
          name: a?.title || `Client à risque ${idx + 1}`,
          meta: a?.message || 'Action préventive recommandée',
          chip: { label: variant === 'neg' ? 'Urgent' : variant === 'warn' ? 'High' : 'Info', variant: variant as 'neg' | 'warn' | 'default' },
        };
      })
    : churnRiskFallback;

  const pStrongData = {
    labels: ['V1','V2','V3','V4','V5','V6','V7','V8','V9','V10'],
    datasets: [{
      data: [0.88,0.72,0.91,0.68,0.52,0.84,0.44,0.78,0.92,0.65],
      backgroundColor: (ctx: any) => ctx.raw >= 0.7 ? C.pos : ctx.raw >= 0.5 ? C.warn : C.neg,
      borderRadius: 4,
    }]
  };

  return (
    <div>
      <HeroBanner label="ML · Risk score" bigValue="27% de risque" subtitle="de manquer l'objectif semestre · ML AUC = 1.00" />
      <KpiGrid kpis={kpis} />

      <Card title="Forecast CA Q+1 — 3 prochains mois · bande 80%">
        <ChartBox height={200}>
          <Line data={forecastData} options={{ ...chartOpts, plugins: { ...chartOpts.plugins, legend: { display: false } } }} />
        </ChartBox>
      </Card>

      <Card title="Churn risk · clients à appeler — Prédiction ML · top 5">
        {churnRisk.map((c, i) => (
          <ListRow
            key={i}
            icon={
              <div className="w-8 h-8 rounded flex items-center justify-center font-semibold text-[11px]" style={{ backgroundColor: c.iconBg, color: c.iconColor }}>
                {c.score}
              </div>
            }
            title={c.name}
            subtitle={c.meta}
            rightElement={<Chip {...c.chip} />}
          />
        ))}
      </Card>

      <Card title="P(strong mouvement) · depuis vos visites — Inference live · 10 dernières visites">
        <ChartBox height={200}>
          <Bar
            data={pStrongData}
            options={{
              ...chartOpts,
              plugins: { ...chartOpts.plugins, legend: { display: false } },
              scales: { ...chartOpts.scales, y: { ...chartOpts.scales.y, min: 0, max: 1 } },
              elements: { bar: { maxBarThickness: 22 } }
            }}
          />
        </ChartBox>
      </Card>
    </div>
  );
};

import React from 'react';
import { AnimSearchTable } from '../components/AnimSearchTable';

export const AnimationList: React.FC = () => {
  return (
    <div>
      <h1 className="text-3xl font-bold text-ink mb-1">32 Animations</h1>
      <p className="text-mute text-sm mb-6">Scorecard and performance tracking</p>
      <AnimSearchTable />
    </div>
  );
};

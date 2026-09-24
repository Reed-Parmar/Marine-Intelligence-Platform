import React from 'react';
import { CatchForecastResult } from '../../types/ml';
import { CatchPredictionCard } from './CatchPredictionCard';

export const PredictionCard: React.FC<{ 
  forecast: CatchForecastResult;
  onSimulate?: (species: string) => void;
}> = (props) => {
  return <CatchPredictionCard {...props} />;
};

export { CatchPredictionCard };

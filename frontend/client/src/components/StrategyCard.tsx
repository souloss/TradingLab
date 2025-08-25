import { useState } from "react";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface StrategyCardProps {
  strategy: {
    id: string;
    name: string;
    type: 'MACD' | 'MA' | 'ATR' | 'VOLUME';
    description: string;
    icon: string;
    color: string;
    bgColor: string;
    borderColor: string;
  };
  isSelected: boolean;
  parameters: Record<string, any>;
  onToggle: (strategyId: string) => void;
  onParameterChange: (strategyId: string, paramName: string, value: any) => void;
  isSingleSelect?: boolean; // 添加 isSingleSelect 属性，设为可选
}

export default function StrategyCard({
  strategy,
  isSelected,
  parameters,
  onToggle,
  onParameterChange,
  isSingleSelect = false // 默认为 false，保持向后兼容
}: StrategyCardProps) {
  const renderParameters = () => {
    switch (strategy.type) {
      case 'MACD':
        return (
          <div className="grid md:grid-cols-3 gap-4">
            <div>
              <Label htmlFor={`${strategy.id}-fast`} className="text-sm font-medium text-foreground">
                快线周期
              </Label>
              <Input
                id={`${strategy.id}-fast`}
                type="number"
                value={parameters.fastPeriod || 12}
                onChange={(e) => onParameterChange(strategy.id, 'fastPeriod', Number(e.target.value))}
                className="mt-1"
              />
            </div>
            <div>
              <Label htmlFor={`${strategy.id}-slow`} className="text-sm font-medium text-foreground">
                慢线周期
              </Label>
              <Input
                id={`${strategy.id}-slow`}
                type="number"
                value={parameters.slowPeriod || 26}
                onChange={(e) => onParameterChange(strategy.id, 'slowPeriod', Number(e.target.value))}
                className="mt-1"
              />
            </div>
            <div>
              <Label htmlFor={`${strategy.id}-signal`} className="text-sm font-medium text-foreground">
                信号周期
              </Label>
              <Input
                id={`${strategy.id}-signal`}
                type="number"
                value={parameters.signalPeriod || 9}
                onChange={(e) => onParameterChange(strategy.id, 'signalPeriod', Number(e.target.value))}
                className="mt-1"
              />
            </div>
          </div>
        );
      case 'MA':
        return (
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <Label htmlFor={`${strategy.id}-short`} className="text-sm font-medium text-foreground">
                短期均线
              </Label>
              <Input
                id={`${strategy.id}-short`}
                type="number"
                value={parameters.shortPeriod || 5}
                onChange={(e) => onParameterChange(strategy.id, 'shortPeriod', Number(e.target.value))}
                className="mt-1"
              />
            </div>
            <div>
              <Label htmlFor={`${strategy.id}-long`} className="text-sm font-medium text-foreground">
                长期均线
              </Label>
              <Input
                id={`${strategy.id}-long`}
                type="number"
                value={parameters.longPeriod || 20}
                onChange={(e) => onParameterChange(strategy.id, 'longPeriod', Number(e.target.value))}
                className="mt-1"
              />
            </div>
          </div>
        );
      case 'ATR':
        return (
          <div className="grid md:grid-cols-3 gap-4">
            <div>
              <Label htmlFor={`${strategy.id}-atr`} className="text-sm font-medium text-foreground">
                ATR周期
              </Label>
              <Input
                id={`${strategy.id}-atr`}
                type="number"
                value={parameters.atr_period || 14}
                onChange={(e) => onParameterChange(strategy.id, 'atr_period', Number(e.target.value))}
                className="mt-1"
              />
            </div>
            <div>
              <Label htmlFor={`${strategy.id}-highlow`} className="text-sm font-medium text-foreground">
                高低点计算周期
              </Label>
              <Input
                id={`${strategy.id}-highlow`}
                type="number"
                value={parameters.period || 20}
                onChange={(e) => onParameterChange(strategy.id, 'period', Number(e.target.value))}
                className="mt-1"
              />
            </div>
            <div>
              <Label htmlFor={`${strategy.id}-multiplier`} className="text-sm font-medium text-foreground">
                ATR倍数
              </Label>
              <Input
                id={`${strategy.id}-multiplier`}
                type="number"
                step="0.1"
                value={parameters.atr_multiplier || 1.5}
                onChange={(e) => onParameterChange(strategy.id, 'atr_multiplier', Number(e.target.value))}
                className="mt-1"
              />
            </div>
          </div>
        );
      case 'VOLUME':
        return (
          <div className="grid md:grid-cols-3 gap-4">
            <div>
              <Label htmlFor={`${strategy.id}-time`} className="text-sm font-medium text-foreground">
                时间范围
              </Label>
              <Input
                id={`${strategy.id}-time`}
                type="number"
                value={parameters.period || 20}
                onChange={(e) => onParameterChange(strategy.id, 'period', Number(e.target.value))}
                className="mt-1"
              />
            </div>
            <div>
              <Label htmlFor={`${strategy.id}-buy`} className="text-sm font-medium text-foreground">
                买入成交量低倍系数
              </Label>
              <Input
                id={`${strategy.id}-buy`}
                type="number"
                step="0.1"
                value={parameters.buyVolumeMultiplier || 0.3}
                onChange={(e) => onParameterChange(strategy.id, 'buyVolumeMultiplier', Number(e.target.value))}
                className="mt-1"
              />
            </div>
            <div>
              <Label htmlFor={`${strategy.id}-sell`} className="text-sm font-medium text-foreground">
                卖出成交量高倍系数
              </Label>
              <Input
                id={`${strategy.id}-sell`}
                type="number"
                value={parameters.sellVolumeMultiplier || 3}
                onChange={(e) => onParameterChange(strategy.id, 'sellVolumeMultiplier', Number(e.target.value))}
                className="mt-1"
              />
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="space-y-4">
      {/* Strategy Selection Card */}
      <div
        className={`strategy-card rounded-lg p-4 cursor-pointer border-2 transition-all ${isSelected
            ? `${strategy.bgColor} ${strategy.borderColor} selected`
            : "border-border hover:border-border bg-card"
          }`}
        onClick={() => onToggle(strategy.id)}
      >
        <div className="flex items-center space-x-3">
          {/* 在单选模式下使用单选样式，多选模式下使用复选框样式 */}
          {isSingleSelect ? (
            <div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${isSelected
                ? `${strategy.color.replace('text-', 'bg-')} border-current`
                : 'border-gray-300'
              }`}>
              {isSelected && (
                <div className="w-2 h-2 rounded-full bg-white"></div>
              )}
            </div>
          ) : (
            <Checkbox
              checked={isSelected}
              onChange={() => onToggle(strategy.id)}
              className={`w-4 h-4 ${strategy.color}`}
            />
          )}
          <i className={`${strategy.icon} ${strategy.color}`}></i>
          <div>
            <h4 className="font-semibold text-foreground">{strategy.name}</h4>
            <p className="text-sm text-muted-foreground">{strategy.description}</p>
          </div>
        </div>
      </div>
      {/* Strategy Parameters */}
      {isSelected && (
        <div className={`${strategy.bgColor} rounded-lg p-4`}>
          <div className="flex items-center space-x-2 mb-4">
            <i className={`${strategy.icon} ${strategy.color}`}></i>
            <h4 className={`font-semibold ${strategy.color}`}>{strategy.name}</h4>
          </div>
          {renderParameters()}
        </div>
      )}
    </div>
  );
}
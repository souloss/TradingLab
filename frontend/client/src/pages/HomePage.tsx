import { Link } from "wouter";

export default function HomePage() {
  const strategies = [
    {
      name: "MACD",
      description: "移动平均收敛发散指标",
      color: "text-blue-600",
      bgColor: "bg-blue-100",
    },
    {
      name: "双均线",
      description: "短期与长期均线交叉信号",
      color: "text-green-600",
      bgColor: "bg-green-100",
    },
    {
      name: "ATR",
      description: "平均真实波动范围",
      color: "text-orange-600",
      bgColor: "bg-orange-100",
    },
    {
      name: "成交量",
      description: "基于成交量变化的买卖信号",
      color: "text-purple-600",
      bgColor: "bg-purple-100",
    },
  ];

  const advantages = [
    {
      title: "专业精准",
      description: "基于深度技术分析指标，历史精准测试可达85%",
      icon: "fas fa-chart-line",
      color: "text-green-600",
      bgColor: "bg-green-100",
    },
    {
      title: "快速高效",
      description: "支持多种组合回测运算，多策略自由组合",
      icon: "fas fa-bolt",
      color: "text-blue-600",
      bgColor: "bg-blue-100",
    },
    {
      title: "直观可视",
      description: "专业的数据显示，交易节点一目了然",
      icon: "fas fa-chart-bar",
      color: "text-purple-600",
      bgColor: "bg-purple-100",
    },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Hero Section */}
      <div className="text-center mb-16">
        <div className="inline-flex items-center justify-center w-20 h-20 bg-primary text-primary-foreground rounded-2xl mb-6">
          <i className="fas fa-chart-line text-2xl"></i>
        </div>
        <h1 className="text-4xl font-bold text-foreground mb-4">专业量化交易系统</h1>
        <p className="text-xl text-muted-foreground max-w-3xl mx-auto mb-8">
          基于先进的技术分析指标，为您提供精准的股票策略回测服务，支持多分析维度批量选股，助您发现最佳投资机会。
        </p>
        <div className="inline-flex items-center px-4 py-2 bg-warning/10 text-warning rounded-full text-sm font-medium">
          <i className="fas fa-award mr-2"></i>专业级研判分析平台
        </div>
      </div>

      {/* Main Features */}
      <div className="grid md:grid-cols-2 gap-8 mb-16">
        {/* Individual Stock Analysis Card */}
        <div className="bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-950 dark:to-emerald-950 rounded-2xl p-8 border border-green-200 dark:border-green-800 hover:shadow-lg transition-shadow">
          <div className="bg-success text-success-foreground rounded-xl p-3 w-12 h-12 flex items-center justify-center mb-6">
            <i className="fas fa-search-dollar text-lg"></i>
          </div>
          <h3 className="text-2xl font-bold text-foreground mb-4">个股回测</h3>
          <p className="text-muted-foreground mb-6">针对单只股票进行精确的策略回测分析，支持多种技术指标组合运用</p>
          <div className="flex flex-wrap gap-2 mb-6 text-sm">
            <span className="bg-card px-3 py-1 rounded-full text-foreground">MACD策略</span>
            <span className="bg-card px-3 py-1 rounded-full text-foreground">双均线策略</span>
            <span className="bg-card px-3 py-1 rounded-full text-foreground">ATR策略</span>
            <span className="bg-card px-3 py-1 rounded-full text-foreground">成交量策略</span>
          </div>
          <Link href="/individual">
            <div className="w-full bg-success text-success-foreground px-6 py-3 rounded-xl font-medium hover:bg-success/90 transition-colors inline-flex items-center justify-center">
              开始个股回测 <i className="fas fa-arrow-right ml-2"></i>
            </div>
          </Link>
        </div>

        {/* Stock Selection Card */}
        <div className="bg-gradient-to-br from-purple-50 to-violet-50 dark:from-purple-950 dark:to-violet-950 rounded-2xl p-8 border border-purple-200 dark:border-purple-800 hover:shadow-lg transition-shadow">
          <div className="bg-secondary text-secondary-foreground rounded-xl p-3 w-12 h-12 flex items-center justify-center mb-6">
            <i className="fas fa-filter text-lg"></i>
          </div>
          <h3 className="text-2xl font-bold text-foreground mb-4">选股回测</h3>
          <p className="text-muted-foreground mb-6">基于多维度筛选条件进行批量分析，发现符合投资机会</p>
          <div className="flex flex-wrap gap-2 mb-6 text-sm">
            <span className="bg-card px-3 py-1 rounded-full text-foreground">市值筛选</span>
            <span className="bg-card px-3 py-1 rounded-full text-foreground">行业分析</span>
            <span className="bg-card px-3 py-1 rounded-full text-foreground">技术面配置</span>
            <span className="bg-card px-3 py-1 rounded-full text-foreground">批量回测</span>
          </div>
          <Link href="/selection">
            <div className="w-full bg-secondary text-secondary-foreground px-6 py-3 rounded-xl font-medium hover:bg-secondary/90 transition-colors inline-flex items-center justify-center">
              开始选股回测 <i className="fas fa-arrow-right ml-2"></i>
            </div>
          </Link>
        </div>
      </div>

      {/* Supported Strategies */}
      <div className="mb-16">
        <h2 className="text-3xl font-bold text-center text-foreground mb-12">支持的量化策略</h2>
        <p className="text-center text-muted-foreground mb-8">各种经典技术分析指标，可自由组合使用适合的配置</p>
        <div className="grid md:grid-cols-4 gap-6">
          {strategies.map((strategy) => (
            <div key={strategy.name} className="bg-card rounded-xl p-6 border border-border text-center hover:shadow-md transition-shadow">
              <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium mb-3 ${strategy.bgColor} ${strategy.color}`}>
                {strategy.name}
              </div>
              <h4 className="font-semibold text-foreground mb-2">{strategy.name}</h4>
              <p className="text-sm text-muted-foreground">{strategy.description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Why Choose Us */}
      <div className="bg-card rounded-2xl p-8 border border-border">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-primary text-primary-foreground rounded-xl mb-4">
            <i className="fas fa-bolt text-xl"></i>
          </div>
          <h2 className="text-3xl font-bold text-foreground">为什么选择我们？</h2>
        </div>
        <div className="grid md:grid-cols-3 gap-8">
          {advantages.map((advantage) => (
            <div key={advantage.title} className="text-center">
              <div className={`${advantage.bgColor} ${advantage.color} rounded-lg p-3 w-12 h-12 flex items-center justify-center mx-auto mb-4`}>
                <i className={advantage.icon}></i>
              </div>
              <h4 className="font-semibold text-foreground mb-2">{advantage.title}</h4>
              <p className="text-muted-foreground">{advantage.description}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

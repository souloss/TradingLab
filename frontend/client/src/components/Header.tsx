import { Link, useLocation } from "wouter";
import { useState } from "react";

export default function Header() {
  const [location] = useLocation();
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const navItems = [
    { id: "home", path: "/", label: "量化分析首页", icon: "fas fa-chart-bar" },
    { id: "individual", path: "/individual", label: "个股回测", icon: "fas fa-search-dollar" },
    { id: "selection", path: "/selection", label: "选股回测", icon: "fas fa-filter" },
    { id: "selection", path: "/backtests", label: "历史回测结果", icon: "fas fa-chart-bar" },
  ];

  return (
    <header className="bg-card shadow-sm border-b border-border sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo and Title */}
          <div className="flex items-center space-x-2 sm:space-x-3">
            <div className="bg-primary text-primary-foreground rounded-lg p-2">
              <i className="fas fa-chart-line text-lg"></i>
            </div>
            <a href="/">
            <div>
              <h1 className="text-lg sm:text-xl font-semibold text-foreground">量化交易系统</h1>
              <span className="hidden sm:inline text-sm text-muted-foreground">专业股票策略回测分析平台</span>
            </div>
            </a>
          </div>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex space-x-1">
            {navItems.map((item) => {
              const isActive = location === item.path;
              const isSelection = item.id === "selection";

              return (
                <Link key={item.id} href={item.path}>
                  <div className={`nav-btn px-4 py-2 rounded-lg text-sm font-medium transition-colors ${isActive
                      ? isSelection
                        ? "bg-secondary text-secondary-foreground"
                        : "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                    }`}>
                    <i className={`${item.icon} mr-2`}></i>
                    {item.label}
                  </div>
                </Link>
              );
            })}
          </nav>

          {/* Mobile menu button */}
          <div className="md:hidden">
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="inline-flex items-center justify-center p-2 rounded-md text-muted-foreground hover:text-foreground hover:bg-accent focus:outline-none focus:ring-2 focus:ring-inset focus:ring-primary"
              aria-expanded="false"
            >
              <span className="sr-only">打开主菜单</span>
              {!isMenuOpen ? (
                <i className="fas fa-bars block h-6 w-6"></i>
              ) : (
                <i className="fas fa-times block h-6 w-6"></i>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu, show/hide based on menu state. */}
      {isMenuOpen && (
        <div className="md:hidden">
          <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3 bg-card border-t border-border">
            {navItems.map((item) => {
              const isActive = location === item.path;
              const isSelection = item.id === "selection";

              return (
                <Link key={item.id} href={item.path}>
                  <div
                    onClick={() => setIsMenuOpen(false)}
                    className={`block px-3 py-2 rounded-md text-base font-medium transition-colors ${isActive
                        ? isSelection
                          ? "bg-secondary text-secondary-foreground"
                          : "bg-primary text-primary-foreground"
                        : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                      }`}
                  >
                    <i className={`${item.icon} mr-3`}></i>
                    {item.label}
                  </div>
                </Link>
              );
            })}
          </div>
        </div>
      )}
    </header>
  );
}
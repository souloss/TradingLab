import { Switch, Route } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import Header from "@/components/Header";
import HomePage from "@/pages/HomePage";
import IndividualBacktest from "@/pages/IndividualBacktest";
import SelectionBacktest from "@/pages/SelectionBacktest";
import ResultsPage from "@/pages/ResultsPage";
import NotFound from "@/pages/not-found";
import { useGlobalErrorHandler } from "./hooks/useGlobalErrorHandler";

function Router() {
  return (
    <>
      <Header />
      <main className="min-h-screen bg-background">
        <Switch>
          <Route path="/" component={HomePage} />
          <Route path="/individual" component={IndividualBacktest} />
          <Route path="/selection" component={SelectionBacktest} />
          <Route path="/results/:id" component={ResultsPage} />
          <Route component={NotFound} />
        </Switch>
      </main>
      
      {/* Footer */}
      <footer className="bg-card border-t border-border mt-16">
        <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
          <p className="text-center text-muted-foreground text-sm">
            © 2024 量化交易系统 - 专业的股票策略回测分析平台
          </p>
        </div>
      </footer>
    </>
  );
}

function App() {
  useGlobalErrorHandler(); // 全局错误捕获
  
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <Router />
      </TooltipProvider>
    </QueryClientProvider>
  );
}

export default App;

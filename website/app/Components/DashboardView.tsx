import TopBar from "./TopBar";
import RiskMap from "./RiskMap";
import DriverMonitor from "./DriverMonitor";
import AlertsPanel from "./AlertsPanel";
import RouteRisk from "./RouteRisk";
import StatCard from "./StatCard";

export default function DashboardView() {
  return (
    <div className="space-y-6">
      <TopBar />

      <div className="grid grid-cols-4 gap-6">
        <StatCard
          title="Active Drivers"
          value="1,248"
          change="+5.2% vs yesterday"
          color="bg-blue-500"
        />

        <StatCard
          title="High Risk Alerts"
          value="3"
          change="Active alerts"
          color="bg-red-500"
        />

        <StatCard
          title="Drivers Monitored"
          value="98.6%"
          change="Compliance rate"
          color="bg-green-500"
        />

        <StatCard
          title="Avg. Risk Score"
          value="23"
          change="Low risk"
          color="bg-purple-500"
        />
      </div>

      <div className="h-[450px] rounded-3xl overflow-hidden border border-white/10 shadow-2xl">
        <RiskMap />
      </div>

      <div className="grid grid-cols-3 gap-6">
        <DriverMonitor />
        <AlertsPanel />
        <RouteRisk />
      </div>
    </div>
  );
}
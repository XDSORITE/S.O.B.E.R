export default function AlertsPanel() {
  return (
    <div className="bg-[#0F172A] border border-white/10 rounded-3xl p-5">
      <h2 className="text-2xl font-bold mb-4">
        Active Alerts
      </h2>

      <div className="space-y-4">
        <div className="bg-red-500/20 border border-red-500/20 p-4 rounded-2xl">
          High DUI probability detected in Los Angeles
        </div>

        <div className="bg-yellow-500/20 border border-yellow-500/20 p-4 rounded-2xl">
          Elevated route risk near downtown Chicago
        </div>

        <div className="bg-blue-500/20 border border-blue-500/20 p-4 rounded-2xl">
          Driver fatigue monitoring active
        </div>
      </div>
    </div>
  );
}
export default function AlertsPanel() {
    return(
        <div className="bg-[#111827] border border-white/10 rounded-2x1 p-5">
            <h2 className="text-2x1 font-bold mb-4">Active Alerts</h2>
            <div className="space-y-4">
                <div className="bg-red-500/20 border border-red-500/20 p-4 rounded-x1">
                High DUI Probability detected in Los Angeles
                </div>
                <div className="bg-yellow-500/20 border border-yellow-500/20 p-4 rounded-x1">
                Route risk elevated near downtown Chicago
                </div>
                <div className="bg-blue-500/20 border border-blue-500/20 p-4 rounded-x1">
                Driver fatigue monitoring active
                </div>
            </div>
        </div>
    );
}
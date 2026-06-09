export default function TopBar() {
    return(
        <div className="bg-[#111827] border border-white/10 rounded-2x1 p-4 flex items-center justify-between">
            <div>
                <h1 className="text-2x1 font-bold">
                    DUI Risk Detection Dashboard
                </h1>
                <p className="text-gray-400 text-sm">
                    Real-time AI driver monitoring system
                </p>
            </div>
            <div className="flex items-center gap-4">
                <div className="bg-green-500/20 text-green-400 px-4 py-2 rounded-x1">
                System Online
                </div>
                <div className="bg-red-500/20 text-red-400 px-4 pv-2 rounded-x1">
                3 Active Alerts
                </div>
            </div>
        </div>
    );
}
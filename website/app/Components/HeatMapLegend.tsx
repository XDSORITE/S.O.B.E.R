export default function HeatmapLegend() {
    return(
        <div className="absolute bottom-5 right-5 bg-[#111827]/90 border border-white/10 rounded-x1 p-4 z-index:1000">
            <h3 className="font-bold mb-3">Risk Levels</h3>
            <div className="space-y-2">
                <div className="flex items-center gap-2">
                    <div className="w-4 h-4 bg-red-500 rounded-full"></div>
                    <span>High Risk</span>
                </div>
                <div className="flex items-center gap-2">
                    <div className="w-4 h-4 bg-yellow-400 rounded-full"></div>
                    <span>Moderate Risk</span>
                </div>
                <div className="flex items-center gap-2">
                    <div className="w-4 h-4 bg-green-500 rounded-full"></div>
                    <span>Low Risk</span>
                </div>
            </div>
        </div>
    );
}
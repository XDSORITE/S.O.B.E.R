export default function HeatmapLegend() {
  return (
    <div className="absolute bottom-4 right-4 bg-black/70 p-4 rounded-xl border border-white/10 z-[1000]">
      <h3 className="font-bold mb-2">
        Risk Levels
      </h3>

      <div className="space-y-2 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-red-500"></div>
          High Risk
        </div>

        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-yellow-400"></div>
          Elevated Risk
        </div>

        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-green-500"></div>
          Low Risk
        </div>
      </div>
    </div>
  );
}
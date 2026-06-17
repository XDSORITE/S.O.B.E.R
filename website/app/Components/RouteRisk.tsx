export default function RouteRisk() {
  return (
    <div className="bg-[#0F172A] border border-white/10 rounded-3xl p-5">
      <h2 className="text-2xl font-bold mb-4">
        Route Risk
      </h2>

      <div className="space-y-4">
        <div>
          <p className="text-gray-400">
            Current Route
          </p>

          <h3 className="text-xl font-semibold">
            Downtown LA → Santa Monica
          </h3>
        </div>

        <div>
          <p className="text-gray-400">
            Estimated Risk Level
          </p>

          <h3 className="text-red-400 text-3xl font-bold">
            HIGH
          </h3>
        </div>

        <div>
          <p className="text-gray-400">
            Collision Probability
          </p>

          <h3 className="text-2xl font-bold">
            72%
          </h3>
        </div>
      </div>
    </div>
  );
}
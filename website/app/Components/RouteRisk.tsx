export default function RouteRisk() {
    return(
        <div className="bg-[#111827] border border-white/10 rounded-2x1 p-5">
            <h2 className="text-2x1 font-bold mb-4">Route Risk</h2>
            <div className="space-y-4">
                <div>
                    <p className="text-gray-400">Current Route</p>
                    <h3 className="text-x1 font-semibold">Downtown LA --- Santa Monica</h3>
                </div>
                <div>
                    <p className="text-gray-400">Estimated Risk</p>
                    <h3 className="text-red-400 text-3x1 font-bold">HIGH</h3>
                </div>
                <div>
                    <p className="text-gray-400">Predicted Collision Probability</p>
                    <h3 className="text-2x1 font-bold">72%</h3>
                </div>
            </div>
        </div>
    );
}
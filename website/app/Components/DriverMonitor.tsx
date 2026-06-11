export default function DriverMonitor() {
    return(
        <div className="bg-[#111827] border border-white/10 rounded-2x1 p-5">
            <h2 className="text-2x1 font-bold mb-4">Driver Monitoring</h2>
            <div className="bg-black rounded-x1 h-40 dlex items-center justify-center mb-4">
                <p className="text-gray-500">Live Camera Feed</p>
            </div>
            <div className="space-y-2">
                <p>Driver Status: Alert</p>
                <p>Facial Tracking: Active</p>
                <p>Drowsiness Level: 12%</p>
                <p>DUI Risk Score: 18%</p>
                <p>Vehicle Speed: 50 MPH</p>
            </div>
        </div>
    );
}